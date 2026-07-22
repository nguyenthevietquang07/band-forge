from fastapi.testclient import TestClient

from bandforge_api.main import create_app


def test_local_static_editor_origin_can_call_api():
    with TestClient(create_app("sqlite:///:memory:")) as client:
        response = client.options(
            "/v1/songs",
            headers={
                "Origin": "http://127.0.0.1:8012",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,idempotency-key",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8012"
    assert "Idempotency-Key" in response.headers["access-control-allow-headers"]
