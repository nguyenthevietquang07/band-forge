import pytest
from fastapi.testclient import TestClient

from bandforge_api.main import create_app
from bandforge_api.repository import create_session_factory
from bandforge_api.services import SourceWorkflowService, WorkflowError


@pytest.mark.parametrize("idempotency_key", ["short-7", "x" * 201])
def test_public_idempotent_routes_reject_keys_outside_contract_bounds(
    tmp_path, idempotency_key: str
) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-idempotency-key-bounds.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        source = client.post(
            f"/v1/songs/{song['id']}/sources",
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am"]},
            },
        ).json()
        routes = [
            ("/v1/songs", {"title": "New Set"}),
            (
                f"/v1/songs/{song['id']}/sources",
                {
                    "sourceType": "STRUCTURED",
                    "rightsAttested": True,
                    "content": {"key": "A_MINOR", "bars": ["Am"]},
                },
            ),
            (
                f"/v1/source-revisions/{source['id']}/approval",
                {"rightsAttested": True},
            ),
            (
                f"/v1/songs/{song['id']}/arrangements",
                {"sourceRevisionId": source["id"], "title": "Late Set"},
            ),
        ]

        responses = [
            client.post(route, headers={"Idempotency-Key": idempotency_key}, json=payload)
            for route, payload in routes
        ]

    for response in responses:
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_REQUEST"
        assert response.json()["error"]["message"] == "Request validation failed."
        assert response.json()["error"]["requestId"]


def test_same_idempotency_key_replays_original_song(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-idempotency.sqlite3'}"
    headers = {"Idempotency-Key": "song-create-001"}
    with TestClient(create_app(database_url)) as client:
        first = client.post("/v1/songs", headers=headers, json={"title": "Late Set"})
        second = client.post("/v1/songs", headers=headers, json={"title": "Late Set"})

    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()


def test_reused_idempotency_key_with_different_song_is_rejected(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-idempotency-conflict.sqlite3'}"
    headers = {"Idempotency-Key": "song-create-001"}
    with TestClient(create_app(database_url)) as client:
        client.post("/v1/songs", headers=headers, json={"title": "Late Set"})
        response = client.post("/v1/songs", headers=headers, json={"title": "Other Set"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_same_idempotency_key_replays_original_source_revision(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-source-idempotency.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        headers = {"Idempotency-Key": "source-create-001"}
        payload = {
            "sourceType": "STRUCTURED",
            "rightsAttested": True,
            "content": {"key": "A_MINOR", "bars": ["Am", "F"]},
        }
        first = client.post(f"/v1/songs/{song['id']}/sources", headers=headers, json=payload)
        second = client.post(f"/v1/songs/{song['id']}/sources", headers=headers, json=payload)

    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()


def test_source_idempotency_key_conflict_is_rejected(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-source-idempotency-conflict.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        headers = {"Idempotency-Key": "source-create-001"}
        first_payload = {
            "sourceType": "STRUCTURED",
            "rightsAttested": True,
            "content": {"key": "A_MINOR", "bars": ["Am", "F"]},
        }
        second_payload = {
            **first_payload,
            "content": {"key": "A_MINOR", "bars": ["Am", "C"]},
        }
        client.post(f"/v1/songs/{song['id']}/sources", headers=headers, json=first_payload)
        response = client.post(
            f"/v1/songs/{song['id']}/sources", headers=headers, json=second_payload
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_same_idempotency_key_replays_source_approval_and_arrangement(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-idempotency-workflow.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        source = client.post(
            f"/v1/songs/{song['id']}/sources",
            headers={"Idempotency-Key": "source-create-001"},
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
            },
        )
        source_replay = client.post(
            f"/v1/songs/{song['id']}/sources",
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
        approval_replay = client.post(
            f"/v1/source-revisions/{source.json()['id']}/approval",
            headers={"Idempotency-Key": "source-approval-001"},
            json={"rightsAttested": True},
        )
        arrangement = client.post(
            f"/v1/songs/{song['id']}/arrangements",
            headers={"Idempotency-Key": "arrangement-create-001"},
            json={"sourceRevisionId": source.json()["id"], "title": "Late Set"},
        )
        arrangement_replay = client.post(
            f"/v1/songs/{song['id']}/arrangements",
            headers={"Idempotency-Key": "arrangement-create-001"},
            json={"sourceRevisionId": source.json()["id"], "title": "Late Set"},
        )

    assert source.status_code == source_replay.status_code == 201
    assert source.json() == source_replay.json()
    assert approval.status_code == approval_replay.status_code == 200
    assert approval.json() == approval_replay.json()
    assert arrangement.status_code == arrangement_replay.status_code == 201
    assert arrangement.json() == arrangement_replay.json()


def test_reused_approval_idempotency_key_with_different_body_is_rejected(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-approval-idempotency-conflict.sqlite3'}"
    headers = {"Idempotency-Key": "source-approval-001"}
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
        approved = client.post(
            f"/v1/source-revisions/{source['id']}/approval",
            headers=headers,
            json={"rightsAttested": True},
        )
        conflict = client.post(
            f"/v1/source-revisions/{source['id']}/approval",
            headers=headers,
            json={"rightsAttested": False},
        )

    assert approved.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert conflict.json()["error"]["requestId"]


def test_reused_idempotency_key_with_different_source_request_is_rejected(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-source-idempotency-conflict.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post("/v1/songs", json={"title": "Late Set"}).json()
        headers = {"Idempotency-Key": "source-create-001"}
        client.post(
            f"/v1/songs/{song['id']}/sources",
            headers=headers,
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am"]},
            },
        )
        response = client.post(
            f"/v1/songs/{song['id']}/sources",
            headers=headers,
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["F"]},
            },
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"


def test_service_rejects_changed_source_body_before_rights_validation(tmp_path) -> None:
    database_url = f"sqlite:///{tmp_path / 'bandforge-source-rights-idempotency-conflict.sqlite3'}"
    session_factory = create_session_factory(database_url)
    service = SourceWorkflowService(session_factory)
    song = service.create_song("Late Set")
    service.create_source_revision(song["id"], True, "A_MINOR", ["Am"], "source-create-001")

    try:
        service.create_source_revision(song["id"], False, "A_MINOR", ["Am"], "source-create-001")
    except WorkflowError as error:
        assert error.code == "IDEMPOTENCY_KEY_REUSED"
        assert error.status_code == 409
    else:
        raise AssertionError("changed source body must reject reused idempotency key")
