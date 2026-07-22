import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from sqlalchemy import func, select

from bandforge_api.main import create_app
from bandforge_api.repository import ArrangementVersionRow, SongRow, create_session_factory

OPENAPI_PATH = Path(__file__).resolve().parents[2] / "contracts" / "openapi.yaml"


def _response_validator(path: str, method: str, status_code: int) -> Draft202012Validator:
    import yaml

    document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    responses = document["paths"][path][method]["responses"]
    response = responses.get(str(status_code)) or responses["default"]
    response = _resolve_references(response, document)
    schema = response["content"]["application/json"]["schema"]
    return Draft202012Validator(_resolve_references(schema, document))


def _resolve_references(value: object, document: dict[str, object]) -> object:
    if isinstance(value, dict):
        if set(value) == {"$ref"}:
            target: object = document
            for part in value["$ref"].removeprefix("#/").split("/"):
                target = target[part]
            return _resolve_references(target, document)
        return {key: _resolve_references(item, document) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_references(item, document) for item in value]
    return value


def _assert_matches_contract(path: str, method: str, response) -> None:
    validator = _response_validator(path, method, response.status_code)
    assert not list(validator.iter_errors(response.json()))


def test_public_source_routes_create_an_arrangement(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-contract.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        source = client.post(
            f"/v1/songs/{song['id']}/sources",
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
            },
        ).json()
        approval = client.post(
            f"/v1/source-revisions/{source['id']}/approval",
            json={"rightsAttested": True},
        )
        response = client.post(
            f"/v1/songs/{song['id']}/arrangements",
            json={"sourceRevisionId": source["id"], "title": "Late Set"},
        )

    assert approval.status_code == 200
    assert response.status_code == 201
    assert response.json()["songId"] == song["id"]
    assert response.json()["currentDraftVersionId"]


def test_song_metadata_fields_round_trip_through_the_public_contract(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-song-metadata.sqlite3'}"
    payload = {
        "title": "Late Set",
        "artist": "The Side Stage",
        "metadataProviderId": "musicbrainz-recording-123",
    }
    with TestClient(create_app(database_url)) as client:
        response = client.post("/v1/songs", json=payload)

    assert response.status_code == 201
    assert response.json()["artist"] == payload["artist"]
    assert response.json()["metadataProviderId"] == payload["metadataProviderId"]
    _assert_matches_contract("/songs", "post", response)

    with create_session_factory(database_url)() as session:
        song = session.get(SongRow, response.json()["id"])

    assert song is not None
    assert song.artist == payload["artist"]
    assert song.metadata_provider_id == payload["metadataProviderId"]


@pytest.mark.parametrize(
    "changed_field, changed_value",
    [("artist", "Another Artist"), ("metadataProviderId", "recording-456")],
)
def test_song_metadata_fields_are_included_in_idempotency_fingerprints(
    tmp_path, changed_field: str, changed_value: str
) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-song-metadata-idempotency.sqlite3'}"
    payload = {
        "title": "Late Set",
        "artist": "The Side Stage",
        "metadataProviderId": "musicbrainz-recording-123",
    }
    changed_payload = {**payload, changed_field: changed_value}
    headers = {"Idempotency-Key": "song-metadata-create-001"}
    with TestClient(create_app(database_url)) as client:
        first = client.post("/v1/songs", headers=headers, json=payload)
        conflict = client.post("/v1/songs", headers=headers, json=changed_payload)

    assert first.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_executable_public_responses_conform_to_openapi_schemas(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-response-contract.sqlite3'}"
    headers = {"Idempotency-Key": "song-create-001"}
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", headers=headers, json={"title": "Late Set"})
        source = client.post(
            f"/v1/songs/{song.json()['id']}/sources",
            headers={"Idempotency-Key": "source-create-001"},
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
            },
        )
        approval = client.post(
            f"/v1/source-revisions/{source.json()['id']}/approval",
            headers={"Idempotency-Key": "source-approval-001"},
            json={"rightsAttested": True},
        )
        arrangement = client.post(
            f"/v1/songs/{song.json()['id']}/arrangements",
            headers={"Idempotency-Key": "arrangement-create-001"},
            json={"sourceRevisionId": source.json()["id"], "title": "Late Set"},
        )
        error = client.post(
            f"/v1/songs/{song.json()['id']}/sources",
            json={"sourceType": "STRUCTURED", "rightsAttested": False, "content": {}},
        )

    _assert_matches_contract("/songs", "post", song)
    _assert_matches_contract("/songs/{songId}/sources", "post", source)
    _assert_matches_contract("/source-revisions/{sourceRevisionId}/approval", "post", approval)
    _assert_matches_contract("/songs/{songId}/arrangements", "post", arrangement)
    _assert_matches_contract("/songs/{songId}/sources", "post", error)


@pytest.mark.parametrize("bar", ["", "x" * 65])
def test_public_structured_source_rejects_bars_outside_contract_bounds(tmp_path, bar: str) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-source-bar-bounds.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        response = client.post(
            f"/v1/songs/{song['id']}/sources",
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": [bar]},
            },
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert response.json()["error"]["message"] == "Request validation failed."
    assert response.json()["error"]["requestId"]
    _assert_matches_contract("/songs/{songId}/sources", "post", response)


def test_source_list_rehydrates_structured_editor_state(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-source-list.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        created = client.post(
            f"/v1/songs/{song['id']}/sources",
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "Cmaj9#11"]},
            },
        ).json()
        response = client.get(f"/v1/songs/{song['id']}/sources")
        read = client.get(f"/v1/source-revisions/{created['id']}")

    assert response.status_code == 200
    assert response.json()["data"] == [created]
    assert response.json()["data"][0]["content"] == {
        "key": "A_MINOR",
        "bars": ["Am", "Cmaj9#11"],
    }
    assert response.json()["data"][0]["findings"][0]["barOrdinal"] == 2
    _assert_matches_contract("/songs/{songId}/sources", "get", response)
    assert read.status_code == 200
    assert read.json() == created
    _assert_matches_contract("/source-revisions/{sourceRevisionId}", "get", read)


def test_arrangement_creation_persists_matching_document_ids_atomically(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-arrangement-identity.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        source = client.post(
            f"/v1/songs/{song['id']}/sources",
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
            },
        ).json()
        client.post(
            f"/v1/source-revisions/{source['id']}/approval", json={"rightsAttested": True}
        )
        response = client.post(
            f"/v1/songs/{song['id']}/arrangements",
            json={"sourceRevisionId": source["id"], "title": "Late Set"},
        )

    with create_session_factory(database_url)() as session:
        version = session.get(ArrangementVersionRow, response.json()["currentDraftVersionId"])

    assert response.status_code == 201
    assert version is not None
    document = json.loads(version.document_json)
    assert document["arrangementId"] == response.json()["id"]
    assert document["versionId"] == version.id


def test_source_song_mismatch_rolls_back_without_orphan_version(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-arrangement-rollback.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        first_song = client.post("/v1/songs", json={"title": "First Set"}).json()
        second_song = client.post("/v1/songs", json={"title": "Second Set"}).json()
        source = client.post(
            f"/v1/songs/{first_song['id']}/sources",
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am"]},
            },
        ).json()
        client.post(
            f"/v1/source-revisions/{source['id']}/approval", json={"rightsAttested": True}
        )
        response = client.post(
            f"/v1/songs/{second_song['id']}/arrangements",
            json={"sourceRevisionId": source["id"], "title": "Second Set"},
        )

    with create_session_factory(database_url)() as session:
        version_count = session.scalar(select(func.count()).select_from(ArrangementVersionRow))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SOURCE_SONG_MISMATCH"
    assert version_count == 0
