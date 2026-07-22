from fastapi.testclient import TestClient

from bandforge_api.main import create_app


def test_chart_export_requires_approval_and_preserves_source_provenance(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'chart-export.sqlite3'}"
    with TestClient(create_app(database_url)) as client:
        song = client.post(
            "/v1/songs",
            json={"title": "Original Chart"},
            headers={"Idempotency-Key": "chart-song-001"},
        ).json()
        source = client.post(
            f"/v1/songs/{song['id']}/sources",
            json={
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
            },
            headers={"Idempotency-Key": "chart-source-001"},
        ).json()

        draft_export = client.get(f"/v1/source-revisions/{source['id']}/chart-export")
        assert draft_export.status_code == 409
        assert draft_export.json()["error"]["code"] == "SOURCE_NOT_READY"

        approved = client.post(
            f"/v1/source-revisions/{source['id']}/approval",
            json={"rightsAttested": True},
            headers={"Idempotency-Key": "chart-approval-001"},
        ).json()
        export = client.get(f"/v1/source-revisions/{approved['id']}/chart-export")

    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/html")
    assert "Original Chart" in export.text
    assert "A minor" in export.text
    assert "Am" in export.text and "G" in export.text
    assert approved["id"] in export.text
    assert approved["contentHash"] in export.text
    assert "ticksPerQuarter" in export.text
