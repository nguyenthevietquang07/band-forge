"""FastAPI application for BandForge's initial structured-source workflow."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, Header, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from bandforge_api.repository import create_session_factory
from bandforge_api.services import SourceWorkflowService, WorkflowError

Bar = Annotated[str, Field(min_length=1, max_length=64)]
IdempotencyKey = Annotated[
    str | None, Header(alias="Idempotency-Key", min_length=8, max_length=200)
]


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-Id", f"req_{uuid4().hex}")
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class CreateSongRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=300)]
    artist: Annotated[str | None, Field(max_length=300)] = None
    metadata_provider_id: str | None = Field(default=None, alias="metadataProviderId")


class CreateSourceRevisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rights_attested: Annotated[bool, Field(alias="rightsAttested")]
    key: Annotated[str, Field(pattern=r"^[A-G]_(MAJOR|MINOR)$")]
    bars: Annotated[list[Bar], Field(min_length=1, max_length=256)]


class StructuredSourceContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: Annotated[str, Field(pattern=r"^[A-G]_(MAJOR|MINOR)$")]
    bars: Annotated[list[Bar], Field(min_length=1, max_length=256)]


class CreateSourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: Literal["STRUCTURED"] = Field(alias="sourceType")
    rights_attested: Literal[True] = Field(alias="rightsAttested")
    content: StructuredSourceContent


class ApproveSourceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rights_attested: bool = Field(alias="rightsAttested")


class CreateArrangementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_revision_id: str = Field(alias="sourceRevisionId")
    title: Annotated[str, Field(min_length=1, max_length=300)]


class CreateCandidateProjectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: Annotated[int, Field(ge=0)] = 0
    tempo_bpm: Annotated[int, Field(alias="tempoBpm", ge=40, le=240)] = 104


class PlaybackPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: Annotated[int, Field(ge=0)] = 0
    tempo_bpm: Annotated[int, Field(alias="tempoBpm", ge=40, le=220)] = 104
    muted_track_ids: list[str] = Field(default_factory=list, alias="mutedTrackIds")
    solo_track_ids: list[str] = Field(default_factory=list, alias="soloTrackIds")
    loop_start_measure_id: str | None = Field(default=None, alias="loopStartMeasureId")
    loop_end_measure_id: str | None = Field(default=None, alias="loopEndMeasureId")
    metronome: bool = False
    count_in_bars: Annotated[int, Field(alias="countInBars", ge=0, le=4)] = 0
    tempo_override_bpm: Annotated[
        int | None, Field(alias="tempoOverrideBpm", ge=40, le=220)
    ] = None


def _error_response(
    request: Request, status_code: int, code: str, message: str, details: object = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "requestId": getattr(request.state, "request_id", None),
            }
        },
    )


def create_app(database_url: str = "sqlite:///bandforge-dev.sqlite3") -> FastAPI:
    app = FastAPI(title="BandForge API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8012", "http://localhost:8012"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )
    app.add_middleware(RequestIdMiddleware)
    service = SourceWorkflowService(create_session_factory(database_url))

    @app.exception_handler(WorkflowError)
    async def workflow_error_handler(request: Request, error: WorkflowError) -> JSONResponse:
        return _error_response(request, error.status_code, error.code, str(error))

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request, 422, "INVALID_REQUEST", "Request validation failed.", error.errors()
        )

    @app.get("/health")
    def health(request: Request) -> dict[str, str]:
        return {"status": "ok", "requestId": request.state.request_id}

    @app.post("/v1/songs", status_code=status.HTTP_201_CREATED)
    def create_song(
        payload: CreateSongRequest,
        idempotency_key: IdempotencyKey = None,
    ) -> dict[str, object]:
        if idempotency_key is None:
            return service.create_song(payload.title, payload.artist, payload.metadata_provider_id)
        return service.create_song_idempotent(
            payload.title, idempotency_key, payload.artist, payload.metadata_provider_id
        )

    @app.post("/v1/songs/{song_id}/source-revisions", status_code=status.HTTP_201_CREATED)
    def create_source_revision(
        song_id: str, payload: CreateSourceRevisionRequest
    ) -> dict[str, object]:
        return service.create_source_revision(
            song_id, payload.rights_attested, payload.key, payload.bars
        )

    @app.post("/v1/songs/{song_id}/sources", status_code=status.HTTP_201_CREATED)
    def create_source(
        song_id: str,
        payload: CreateSourceRequest,
        idempotency_key: IdempotencyKey = None,
    ) -> dict[str, object]:
        return service.create_source_revision(
            song_id,
            payload.rights_attested,
            payload.content.key,
            payload.content.bars,
            idempotency_key,
        )

    @app.get("/v1/songs/{song_id}/sources")
    def list_sources(song_id: str) -> dict[str, object]:
        return {"data": service.list_source_revisions(song_id), "nextPageToken": None}

    @app.post("/v1/source-revisions/{source_revision_id}/approve")
    def approve_source_revision(source_revision_id: str) -> dict[str, object]:
        return service.approve_source_revision(source_revision_id)

    @app.post("/v1/source-revisions/{source_revision_id}/approval")
    def approve_source(
        source_revision_id: str,
        payload: ApproveSourceRequest,
        idempotency_key: IdempotencyKey = None,
    ) -> dict[str, object]:
        return service.approve_source_revision(
            source_revision_id, payload.rights_attested, idempotency_key
        )

    @app.get("/v1/source-revisions/{source_revision_id}")
    def get_source(source_revision_id: str) -> dict[str, object]:
        return service.get_source_revision(source_revision_id)

    @app.get(
        "/v1/source-revisions/{source_revision_id}/chart-export",
        response_class=HTMLResponse,
    )
    def export_chart(source_revision_id: str) -> HTMLResponse:
        return HTMLResponse(service.render_chart_export(source_revision_id))

    @app.post("/v1/source-revisions/{source_revision_id}/arrangement-seeds", status_code=201)
    def create_arrangement_seed(source_revision_id: str) -> dict[str, object]:
        return service.create_arrangement_seed(source_revision_id)

    @app.post("/v1/arrangement-versions/{version_id}/candidates")
    def create_candidate_projection(
        version_id: str, payload: CreateCandidateProjectionRequest
    ) -> dict[str, object]:
        return service.create_candidate_projection(version_id, payload.seed, payload.tempo_bpm)

    @app.post("/v1/arrangement-versions/{version_id}/playback-plan")
    def create_playback_plan(
        version_id: str, payload: PlaybackPlanRequest
    ) -> dict[str, object]:
        return service.create_playback_plan(
            version_id,
            seed=payload.seed,
            tempo_bpm=payload.tempo_bpm,
            muted_track_ids=payload.muted_track_ids,
            solo_track_ids=payload.solo_track_ids,
            loop_start_measure_id=payload.loop_start_measure_id,
            loop_end_measure_id=payload.loop_end_measure_id,
            metronome=payload.metronome,
            count_in_bars=payload.count_in_bars,
            tempo_override_bpm=payload.tempo_override_bpm,
        )

    @app.post("/v1/songs/{song_id}/arrangements", status_code=status.HTTP_201_CREATED)
    def create_arrangement(
        song_id: str,
        payload: CreateArrangementRequest,
        idempotency_key: IdempotencyKey = None,
    ) -> dict[str, object]:
        return service.create_arrangement(
            song_id, payload.source_revision_id, payload.title, idempotency_key
        )

    return app


app = create_app()
