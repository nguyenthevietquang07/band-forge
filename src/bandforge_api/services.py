"""Transactional use cases for the constrained structured-source workflow."""

from __future__ import annotations

import hashlib
import html
import json
from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from bandforge_api.repository import (
    ArrangementRow,
    ArrangementVersionRow,
    IdempotencyRow,
    SongRow,
    SourceRevisionRow,
)
from bandforge_domain.arrangements import SourceNotReadyError, build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate
from bandforge_domain.playback import PlaybackControls, build_playback_plan


class WorkflowError(ValueError):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class SourceWorkflowService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_song(
        self, title: str, artist: str | None = None, metadata_provider_id: str | None = None
    ) -> dict[str, object]:
        now = datetime.now(UTC)
        song = SongRow(
            id=f"song_{uuid4().hex}",
            title=title,
            artist=artist,
            metadata_provider_id=metadata_provider_id,
            created_at=now,
            updated_at=now,
        )
        with self._session_factory.begin() as session:
            session.add(song)
        return self._song_response(song)

    def create_song_idempotent(
        self,
        title: str,
        idempotency_key: str,
        artist: str | None = None,
        metadata_provider_id: str | None = None,
    ) -> dict[str, object]:
        fingerprint = self._fingerprint(
            "POST",
            "/v1/songs",
            {
                "title": title,
                "artist": artist,
                "metadataProviderId": metadata_provider_id,
            },
        )
        with self._session_factory.begin() as session:
            replay = self._replay_or_reject(session, idempotency_key, fingerprint)
            if replay is not None:
                return replay
            now = datetime.now(UTC)
            song = SongRow(
                id=f"song_{uuid4().hex}",
                title=title,
                artist=artist,
                metadata_provider_id=metadata_provider_id,
                created_at=now,
                updated_at=now,
            )
            response = self._song_response(song)
            session.add(song)
            self._store_idempotent_response(session, idempotency_key, fingerprint, response)
        return response

    def create_source_revision(
        self,
        song_id: str,
        rights_attested: bool,
        key: str,
        bars: list[str],
        idempotency_key: str | None = None,
    ) -> dict[str, object]:
        with self._session_factory.begin() as session:
            payload = {
                "sourceType": "STRUCTURED",
                "rightsAttested": rights_attested,
                "content": {"key": key, "bars": bars},
            }
            fingerprint = self._fingerprint("POST", f"/v1/songs/{song_id}/sources", payload)
            if idempotency_key is not None:
                replay = self._replay_or_reject(session, idempotency_key, fingerprint)
                if replay is not None:
                    return replay
            if not rights_attested:
                raise WorkflowError(
                    "RIGHTS_ATTESTATION_REQUIRED", "Rights attestation is required.", 422
                )
            song = session.get(SongRow, song_id)
            if song is None:
                raise WorkflowError("SONG_NOT_FOUND", "Song was not found.", 404)
            chart = normalize_chart(StructuredChartInput(title=song.title, key=key, bars=bars))
            source_payload = {"title": song.title, "key": key, "bars": bars}
            revision = SourceRevisionRow(
                id=f"src_rev_{uuid4().hex}",
                song_id=song_id,
                content_hash=self._content_hash(source_payload),
                rights_attested=True,
                status="DRAFT",
                chart_json=json.dumps(source_payload, separators=(",", ":"), sort_keys=True),
                created_at=datetime.now(UTC),
            )
            session.add(revision)
            response = self._revision_response(revision, chart.findings)
            if idempotency_key is not None:
                self._store_idempotent_response(session, idempotency_key, fingerprint, response)
        return response

    def approve_source_revision(
        self,
        source_revision_id: str,
        rights_attested: bool = True,
        idempotency_key: str | None = None,
    ) -> dict[str, object]:
        with self._session_factory.begin() as session:
            fingerprint = self._fingerprint(
                "POST",
                f"/v1/source-revisions/{source_revision_id}/approval",
                {"rightsAttested": rights_attested},
            )
            if idempotency_key is not None:
                replay = self._replay_or_reject(session, idempotency_key, fingerprint)
                if replay is not None:
                    return replay
            if not rights_attested:
                raise WorkflowError(
                    "RIGHTS_ATTESTATION_REQUIRED", "Rights attestation is required.", 422
                )
            revision = self._require_revision(session, source_revision_id)
            payload = json.loads(revision.chart_json)
            chart = normalize_chart(StructuredChartInput(**payload))
            if chart.findings:
                raise WorkflowError(
                    "SOURCE_NOT_READY", "Resolve every source finding before approval.", 409
                )
            revision.status = "APPROVED"
            response = self._revision_response(revision, [])
            if idempotency_key is not None:
                self._store_idempotent_response(session, idempotency_key, fingerprint, response)
        return response

    def create_arrangement_seed(self, source_revision_id: str) -> dict[str, object]:
        with self._session_factory.begin() as session:
            revision = self._require_revision(session, source_revision_id)
            payload = json.loads(revision.chart_json)
            _, version, document = self._create_arrangement_and_version(
                session, revision, payload["title"]
            )
        return {"id": version.id, "document": document}

    def create_candidate_projection(
        self, version_id: str, seed: int, tempo_bpm: int
    ) -> dict[str, object]:
        """Return an accepted, non-persisted candidate projection for local preview."""
        return self._candidate_projection(version_id, seed, tempo_bpm)

    def create_playback_plan(
        self,
        version_id: str,
        *,
        seed: int,
        tempo_bpm: int,
        muted_track_ids: list[str],
        solo_track_ids: list[str],
        loop_start_measure_id: str | None,
        loop_end_measure_id: str | None,
        metronome: bool,
        count_in_bars: int,
        tempo_override_bpm: int | None,
    ) -> dict[str, object]:
        projection = self._candidate_projection(version_id, seed, tempo_bpm)
        try:
            controls = PlaybackControls(
                muted_track_ids=tuple(muted_track_ids),
                solo_track_ids=tuple(solo_track_ids),
                loop_start_measure_id=loop_start_measure_id,
                loop_end_measure_id=loop_end_measure_id,
                metronome=metronome,
                count_in_bars=count_in_bars,
                tempo_override_bpm=tempo_override_bpm,
            )
            plan = build_playback_plan(projection["candidate"], controls)
        except ValueError as error:
            raise WorkflowError("INVALID_PLAYBACK_CONTROLS", str(error), 422) from error
        return {
            "candidateVersionId": plan.candidate_version_id,
            "accepted": projection["accepted"],
            "rightsAttested": projection["rightsAttested"],
            "lineage": dict(plan.lineage),
            "tempoBpm": plan.tempo_bpm,
            "activeTrackIds": list(plan.active_track_ids),
            "loopStartTick": plan.loop_start_tick,
            "loopEndTick": plan.loop_end_tick,
            "metronome": plan.metronome,
            "countInBars": plan.count_in_bars,
            "events": [
                {
                    "trackId": event.track_id,
                    "eventId": event.event_id,
                    "kind": event.kind,
                    "startTick": event.start_tick,
                    "durationTicks": event.duration_ticks,
                    "pitches": list(event.pitches),
                    "velocity": event.velocity,
                }
                for event in plan.events
            ],
        }

    def _candidate_projection(
        self, version_id: str, seed: int, tempo_bpm: int
    ) -> dict[str, object]:
        with self._session_factory() as session:
            version = session.get(ArrangementVersionRow, version_id)
            if version is None:
                raise WorkflowError(
                    "ARRANGEMENT_VERSION_NOT_FOUND", "Arrangement version was not found.", 404
                )
            revision = self._require_revision(session, version.source_revision_id)
            if revision.status != "APPROVED" or not revision.rights_attested:
                raise WorkflowError(
                    "SOURCE_NOT_READY",
                    "Approve and rights-attest the source before generating a candidate.",
                    409,
                )
            source = json.loads(version.document_json)
            result = generate_candidate(
                source, ArrangementControls(seed=seed, tempo_bpm=tempo_bpm)
            )
            if not result.accepted:
                raise WorkflowError(
                    "CANDIDATE_NOT_ACCEPTED", "Hard validation rejected the candidate.", 409
                )
            candidate = deepcopy(result.document)
            candidate["status"] = "ACCEPTED"
            lineage = {
                "seed": result.lineage.seed,
                "engineVersion": result.lineage.engine_version,
                "stylePackVersion": result.lineage.style_pack_version,
                "validatorVersion": result.lineage.validator_version,
                "inputRevisionSet": list(result.lineage.input_revision_set),
                "provenance": result.lineage.provenance,
            }
            return {
                "candidateId": candidate["versionId"],
                "accepted": True,
                "rightsAttested": all(
                    ref.get("rightsAttested") is True for ref in candidate["sourceRefs"]
                ),
                "lineage": lineage,
                "validatorVersion": result.lineage.validator_version,
                "candidate": candidate,
            }

    def create_arrangement(
        self,
        song_id: str,
        source_revision_id: str,
        title: str,
        idempotency_key: str | None = None,
    ) -> dict[str, object]:
        with self._session_factory.begin() as session:
            payload = {"sourceRevisionId": source_revision_id, "title": title}
            fingerprint = self._fingerprint("POST", f"/v1/songs/{song_id}/arrangements", payload)
            if idempotency_key is not None:
                replay = self._replay_or_reject(session, idempotency_key, fingerprint)
                if replay is not None:
                    return replay
            revision = self._require_revision(session, source_revision_id)
            if revision.song_id != song_id:
                raise WorkflowError(
                    "SOURCE_SONG_MISMATCH", "Source revision belongs to another song.", 409
                )
            arrangement, _, _ = self._create_arrangement_and_version(session, revision, title)
            response = self._arrangement_response(arrangement)
            if idempotency_key is not None:
                self._store_idempotent_response(session, idempotency_key, fingerprint, response)
        return response

    def _create_arrangement_and_version(
        self, session: Session, revision: SourceRevisionRow, title: str
    ) -> tuple[ArrangementRow, ArrangementVersionRow, dict[str, object]]:
        if revision.status != "APPROVED":
            raise WorkflowError("SOURCE_NOT_READY", "Approve the harmonic source first.", 409)
        chart = normalize_chart(StructuredChartInput(**json.loads(revision.chart_json)))
        arrangement_id = f"arrangement_{uuid4().hex}"
        version_id = f"arr_version_{uuid4().hex}"
        now = datetime.now(UTC)
        try:
            document = build_arrangement_seed(
                chart,
                revision.id,
                revision.content_hash,
                now,
                arrangement_id=arrangement_id,
                version_id=version_id,
            )
        except SourceNotReadyError as error:
            raise WorkflowError("SOURCE_NOT_READY", str(error), 409) from error
        arrangement = ArrangementRow(
            id=arrangement_id,
            song_id=revision.song_id,
            title=title,
            current_draft_version_id=version_id,
            created_at=now,
        )
        version = ArrangementVersionRow(
            id=version_id,
            source_revision_id=revision.id,
            arrangement_id=arrangement_id,
            status="DRAFT",
            content_hash=self._content_hash(document),
            document_json=json.dumps(document, separators=(",", ":"), sort_keys=True),
            created_at=now,
        )
        session.add(arrangement)
        session.add(version)
        return arrangement, version, document

    def list_source_revisions(self, song_id: str) -> list[dict[str, object]]:
        with self._session_factory() as session:
            if session.get(SongRow, song_id) is None:
                raise WorkflowError("SONG_NOT_FOUND", "Song was not found.", 404)
            revisions = session.scalars(
                select(SourceRevisionRow)
                .where(SourceRevisionRow.song_id == song_id)
                .order_by(SourceRevisionRow.created_at, SourceRevisionRow.id)
            ).all()
            return [self._revision_from_row(revision) for revision in revisions]

    def get_source_revision(self, source_revision_id: str) -> dict[str, object]:
        with self._session_factory() as session:
            return self._revision_from_row(self._require_revision(session, source_revision_id))

    def render_chart_export(self, source_revision_id: str) -> str:
        with self._session_factory() as session:
            revision = self._require_revision(session, source_revision_id)
            if revision.status != "APPROVED":
                raise WorkflowError(
                    "SOURCE_NOT_READY", "Approve the source before exporting a chart.", 409
                )
            payload = json.loads(revision.chart_json)
            chart = normalize_chart(StructuredChartInput(**payload))
            if chart.findings:
                raise WorkflowError("SOURCE_NOT_READY", "Resolve every source finding first.", 409)
            key = payload["key"]
            display_key = f"{key[0]}{key[1:].lower().replace('_', ' ')}"
            bars = "".join(
                f'<article class="bar"><span>Bar {ordinal}</span>'
                f"<strong>{html.escape(chord)}</strong></article>"
                for ordinal, chord in enumerate(payload["bars"], start=1)
            )
            return (
                '<!doctype html><html lang="en"><head><meta charset="utf-8">'
                f"<title>{html.escape(payload['title'])} · BandForge chart</title>"
                '<style>body{font:16px system-ui;max-width:900px;margin:40px auto;color:#172220}'
                'header{border-bottom:2px solid #172220;margin-bottom:24px}.grid{display:grid;'
                'grid-template-columns:repeat(4,1fr);gap:12px}.bar{border:1px solid #9aa8a5;'
                'border-radius:8px;padding:18px}.bar span{display:block;color:#61716d;'
                'font-size:12px}.bar strong{font-size:24px}.provenance{margin-top:32px;'
                'font:12px ui-monospace,monospace;white-space:pre-wrap}</style></head><body>'
                f"<header><h1>{html.escape(payload['title'])}</h1>"
                f"<p>{html.escape(display_key)} · 4/4 · 960 ticks / quarter</p></header>"
                f'<main class="grid">{bars}</main>'
                f'<section class="provenance"><strong>Source provenance</strong>\n'
                f"sourceRevisionId: {html.escape(revision.id)}\n"
                f"contentHash: {html.escape(revision.content_hash)}\n"
                f"rightsAttested: {str(revision.rights_attested).lower()}\n"
                "ticksPerQuarter: 960</section></body></html>"
            )

    @staticmethod
    def _content_hash(payload: dict[str, object]) -> str:
        canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return f"sha256:{hashlib.sha256(canonical).hexdigest()}"

    @staticmethod
    def _fingerprint(method: str, path: str, payload: dict[str, object]) -> str:
        canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(f"{method}\n{path}\n{canonical}".encode()).hexdigest()

    @staticmethod
    def _require_revision(session: Session, source_revision_id: str) -> SourceRevisionRow:
        revision = session.get(SourceRevisionRow, source_revision_id)
        if revision is None:
            raise WorkflowError("SOURCE_REVISION_NOT_FOUND", "Source revision was not found.", 404)
        return revision

    @staticmethod
    def _timestamp(value: object) -> str:
        if not isinstance(value, datetime):
            raise TypeError("persisted timestamps must be datetime values")
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @classmethod
    def _song_response(cls, song: SongRow) -> dict[str, object]:
        return {
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "metadataProviderId": song.metadata_provider_id,
            "createdAt": cls._timestamp(song.created_at),
            "updatedAt": cls._timestamp(song.updated_at),
        }

    @classmethod
    def _arrangement_response(cls, arrangement: ArrangementRow) -> dict[str, object]:
        return {
            "id": arrangement.id,
            "songId": arrangement.song_id,
            "title": arrangement.title,
            "currentDraftVersionId": arrangement.current_draft_version_id,
            "acceptedVersionId": None,
            "createdAt": cls._timestamp(arrangement.created_at),
        }

    def _replay_or_reject(
        self, session: Session, idempotency_key: str, fingerprint: str
    ) -> dict[str, object] | None:
        existing = session.get(IdempotencyRow, idempotency_key)
        if existing is None:
            return None
        if existing.request_fingerprint != fingerprint:
            raise WorkflowError(
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency-Key was previously used with a different request.",
                409,
            )
        return json.loads(existing.response_json)

    @staticmethod
    def _store_idempotent_response(
        session: Session, idempotency_key: str, fingerprint: str, response: dict[str, object]
    ) -> None:
        session.add(
            IdempotencyRow(
                key=idempotency_key,
                request_fingerprint=fingerprint,
                response_json=json.dumps(response, separators=(",", ":"), sort_keys=True),
            )
        )

    @staticmethod
    def _revision_response(
        revision: SourceRevisionRow, findings: list[object]
    ) -> dict[str, object]:
        payload = json.loads(revision.chart_json)
        return {
            "id": revision.id,
            "songId": revision.song_id,
            "sourceType": "STRUCTURED",
            "contentHash": revision.content_hash,
            "rightsAttested": revision.rights_attested,
            "status": revision.status,
            "content": {"key": payload["key"], "bars": payload["bars"]},
            "findings": [
                {
                    "code": finding.code,
                    "message": finding.message,
                    "barOrdinal": finding.bar_ordinal,
                }
                for finding in findings
            ],
            "createdAt": SourceWorkflowService._timestamp(revision.created_at),
        }

    @classmethod
    def _revision_from_row(cls, revision: SourceRevisionRow) -> dict[str, object]:
        payload = json.loads(revision.chart_json)
        chart = normalize_chart(StructuredChartInput(**payload))
        return cls._revision_response(revision, chart.findings)
