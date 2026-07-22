from fastapi.testclient import TestClient

from bandforge_api.main import create_app


def test_candidate_projection_is_accepted_rights_attested_and_traceable(tmp_path) -> None:
    with TestClient(create_app(f"sqlite:///{tmp_path / 'candidate-projection.sqlite3'}")) as client:
        song = client.post("/v1/songs", json={"title": "Candidate Preview"}).json()
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
            json={"rightsAttested": True},
        )
        assert approved.status_code == 200
        seed = client.post(f"/v1/source-revisions/{source['id']}/arrangement-seeds").json()

        response = client.post(
            f"/v1/arrangement-versions/{seed['id']}/candidates",
            json={"seed": 7, "tempoBpm": 104},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["candidateId"] == payload["candidate"]["versionId"]
    assert payload["candidate"]["status"] == "ACCEPTED"
    assert payload["rightsAttested"] is True
    assert payload["lineage"]["inputRevisionSet"] == [source["id"]]
    assert payload["lineage"]["validatorVersion"]
    assert {
        "generated_drums",
        "generated_bass",
        "generated_guitar",
        "generated_keys",
    }.issubset({track["id"] for track in payload["candidate"]["tracks"]})


def test_candidate_projection_rejects_unapproved_source(tmp_path) -> None:
    with TestClient(create_app(f"sqlite:///{tmp_path / 'candidate-gate.sqlite3'}")) as client:
        song = client.post("/v1/songs", json={"title": "Candidate Gate"}).json()
        source = client.post(
            f"/v1/songs/{song['id']}/sources",
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
            },
        ).json()
        response = client.post(f"/v1/source-revisions/{source['id']}/arrangement-seeds")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SOURCE_NOT_READY"
