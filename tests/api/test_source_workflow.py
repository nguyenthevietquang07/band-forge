import json

from fastapi.testclient import TestClient

from bandforge_api.main import create_app
from bandforge_api.repository import ArrangementRow, ArrangementVersionRow, create_session_factory


def _client(tmp_path) -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'bandforge-test.sqlite3'}"
    return TestClient(create_app(database_url))


def test_approved_chart_creates_schema_valid_arrangement_seed(tmp_path) -> None:
    with _client(tmp_path) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        revision = client.post(
            f"/v1/songs/{song['id']}/source-revisions",
            json={"rightsAttested": True, "key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
        ).json()

        assert client.post(f"/v1/source-revisions/{revision['id']}/approve").status_code == 200
        response = client.post(f"/v1/source-revisions/{revision['id']}/arrangement-seeds")

    assert response.status_code == 201
    assert response.json()["document"]["sourceRefs"][0]["sourceRevisionId"] == revision["id"]
    assert response.json()["document"]["harmony"][0]["displaySymbol"] == "Am"


def test_legacy_seed_persists_arrangement_and_matching_document_ids(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-legacy-seed-identity.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        revision = client.post(
            f"/v1/songs/{song['id']}/source-revisions",
            json={"rightsAttested": True, "key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
        ).json()
        client.post(f"/v1/source-revisions/{revision['id']}/approve")
        response = client.post(f"/v1/source-revisions/{revision['id']}/arrangement-seeds")

    assert response.status_code == 201
    with create_session_factory(database_url)() as session:
        version = session.get(ArrangementVersionRow, response.json()["id"])
        assert version is not None
        document = json.loads(version.document_json)
        arrangement = session.get(ArrangementRow, document["arrangementId"])

    assert arrangement is not None
    assert version.arrangement_id == arrangement.id == document["arrangementId"]
    assert version.id == document["versionId"]
    assert arrangement.current_draft_version_id == version.id


def test_unresolved_chord_cannot_be_approved(tmp_path) -> None:
    with _client(tmp_path) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        revision = client.post(
            f"/v1/songs/{song['id']}/source-revisions",
            json={"rightsAttested": True, "key": "A_MINOR", "bars": ["Cmaj9#11"]},
        ).json()
        response = client.post(f"/v1/source-revisions/{revision['id']}/approve")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SOURCE_NOT_READY"


def test_source_without_rights_attestation_is_rejected(tmp_path) -> None:
    with _client(tmp_path) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        response = client.post(
            f"/v1/songs/{song['id']}/source-revisions",
            json={"rightsAttested": False, "key": "A_MINOR", "bars": ["Am"]},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "RIGHTS_ATTESTATION_REQUIRED"


def test_health_returns_request_id(tmp_path) -> None:
    with _client(tmp_path) as client:
        response = client.get("/health", headers={"X-Request-Id": "req_test_001"})

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "req_test_001"
    assert response.json()["status"] == "ok"


def test_playback_plan_endpoint_returns_canonical_domain_projection(tmp_path) -> None:
    with _client(tmp_path) as client:
        song = client.post("/v1/songs", json={"title": "Playback API"}).json()
        revision = client.post(
            f"/v1/songs/{song['id']}/source-revisions",
            json={"rightsAttested": True, "key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
        ).json()
        client.post(f"/v1/source-revisions/{revision['id']}/approve")
        seed = client.post(f"/v1/source-revisions/{revision['id']}/arrangement-seeds").json()
        candidate = client.post(
            f"/v1/arrangement-versions/{seed['id']}/candidates",
            json={"seed": 0, "tempoBpm": 104},
        ).json()

        response = client.post(
            f"/v1/arrangement-versions/{seed['id']}/playback-plan",
            json={
                "seed": 0,
                "tempoBpm": 104,
                "mutedTrackIds": ["generated_bass"],
                "soloTrackIds": ["generated_bass", "generated_guitar"],
                "loopStartMeasureId": "measure_002",
                "loopEndMeasureId": "measure_003",
                "metronome": True,
                "countInBars": 1,
                "tempoOverrideBpm": 116,
            },
        )

    assert response.status_code == 200
    plan = response.json()
    assert plan["candidateVersionId"] == candidate["candidateId"]
    assert plan["lineage"] == candidate["lineage"]
    assert plan["accepted"] is True
    assert plan["rightsAttested"] is True
    assert plan["tempoBpm"] == 116
    assert plan["activeTrackIds"] == ["generated_guitar"]
    assert plan["loopStartTick"] == 3840
    assert plan["loopEndTick"] == 11520
    assert plan["countInBars"] == 1
    assert plan["metronome"] is True
    assert plan["events"]
    assert {
        "trackId",
        "eventId",
        "kind",
        "startTick",
        "durationTicks",
        "pitches",
        "velocity",
    } <= plan["events"][0].keys()

    too_fast = client.post(
        f"/v1/arrangement-versions/{seed['id']}/playback-plan",
        json={"seed": 0, "tempoBpm": 240},
    )
    assert too_fast.status_code == 422
