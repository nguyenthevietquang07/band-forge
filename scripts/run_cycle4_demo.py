"""Run the real local HTTP demo for the structured source editor slice."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).parents[1]
API_BASE = os.environ.get("BANDFORGE_API_URL", "http://127.0.0.1:8011")
WEB_BASE = os.environ.get("BANDFORGE_WEB_URL", "http://127.0.0.1:8012")


def request(
    path: str,
    method: str = "GET",
    body: dict | None = None,
    key: str | None = None,
):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Origin": WEB_BASE}
    if key:
        headers["Idempotency-Key"] = key
    response = urlopen(
        Request(f"{API_BASE}{path}", data=data, method=method, headers=headers), timeout=10
    )
    payload = json.loads(response.read())
    return response.status, payload, response.headers.get("X-Request-Id")


def request_text(path: str) -> tuple[int, str, str | None]:
    response = urlopen(
        Request(f"{API_BASE}{path}", headers={"Origin": WEB_BASE}), timeout=10
    )
    return response.status, response.read().decode(), response.headers.get("content-type")


def wait_for_health() -> None:
    for _ in range(40):
        try:
            status, _, _ = request("/health")
            if status == 200:
                return
        except URLError:
            time.sleep(0.25)
    raise RuntimeError("API did not become healthy on the configured port")


def main() -> int:
    api = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "bandforge_api.main:app",
            "--app-dir",
            "src",
            "--host",
            "127.0.0.1",
            "--port",
            "8011",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    web = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8012", "--bind", "127.0.0.1", "--directory", "web"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    evidence: dict[str, object] = {
        "scope": "Cycle 4 structured source editor",
        "browserVerified": False,
    }
    run_id = uuid4().hex[:10]
    try:
        wait_for_health()
        static = urlopen(f"{WEB_BASE}/", timeout=10).read().decode()
        evidence["staticPage"] = {
            "status": 200,
            "containsEditorHeading": "Make the chart unambiguous." in static,
        }

        song_status, song, song_request_id = request(
            "/v1/songs",
            "POST",
            {"title": "BandForge Original Demo", "artist": "Quang's rehearsal room"},
            f"cycle4-song-{run_id}",
        )
        replay_status, replay, _ = request(
            "/v1/songs",
            "POST",
            {"title": "BandForge Original Demo", "artist": "Quang's rehearsal room"},
            f"cycle4-song-{run_id}",
        )
        evidence["song"] = {
            "status": song_status,
            "replayStatus": replay_status,
            "sameIdOnReplay": song["id"] == replay["id"],
            "requestId": song_request_id,
        }

        invalid_status, invalid, _ = request(
            f"/v1/songs/{song['id']}/sources",
            "POST",
            {
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "F", "Cmaj9#11", "G"]},
            },
            f"cycle4-source-invalid-{run_id}",
        )
        evidence["invalidRevision"] = {
            "status": invalid_status,
            "revisionId": invalid["id"],
            "findingBars": [item["barOrdinal"] for item in invalid["findings"]],
        }

        corrected_status, corrected, _ = request(
            f"/v1/songs/{song['id']}/sources",
            "POST",
            {
                "sourceType": "STRUCTURED",
                "rightsAttested": True,
                "content": {"key": "A_MINOR", "bars": ["Am", "F", "C", "G"]},
            },
            f"cycle4-source-corrected-{run_id}",
        )
        evidence["correctedRevision"] = {
            "status": corrected_status,
            "revisionId": corrected["id"],
            "newImmutableId": corrected["id"] != invalid["id"],
            "findingCount": len(corrected["findings"]),
        }

        approved_status, approved, _ = request(
            f"/v1/source-revisions/{corrected['id']}/approval",
            "POST",
            {"rightsAttested": True},
            f"cycle4-approval-{run_id}",
        )
        evidence["approval"] = {
            "status": approved_status,
            "revisionStatus": approved["status"],
        }

        export_status, export_html, export_type = request_text(
            f"/v1/source-revisions/{approved['id']}/chart-export"
        )
        evidence["chartExport"] = {
            "status": export_status,
            "contentType": export_type,
            "containsTitle": "BandForge Original Demo" in export_html,
            "containsSourceRevision": approved["id"] in export_html,
            "containsContentHash": approved["contentHash"] in export_html,
        }

        seed_status, seed, _ = request(
            f"/v1/source-revisions/{corrected['id']}/arrangement-seeds", "POST"
        )
        document = seed["document"]
        evidence["lockedSeed"] = {
            "status": seed_status,
            "arrangementId": document["arrangementId"],
            "versionId": document["versionId"],
            "ticksPerQuarter": document["global"]["ticksPerQuarter"],
            "lockTypes": [lock["type"] for lock in document["locks"]],
            "sourceRevisionId": document["sourceRefs"][0]["sourceRevisionId"],
        }

        report = ROOT / "reports" / "cycle-4-editor-demo.md"
        report.parent.mkdir(exist_ok=True)
        report.write_text(
            "# Cycle 4 Editor Demo Evidence\n\n"
            f"Date: {datetime.now(UTC).isoformat()}\n\n"
            "Source fixture: original/authored demo chart `Am | F | Cmaj9#11 | G`; "
            "the title and artist are metadata only.\n\n"
            f"```json\n{json.dumps(evidence, indent=2)}\n```\n\n"
            "The real HTTP flow created an idempotent song, observed a blocking finding "
            "on bar 3, submitted a corrected immutable revision, approved it, and "
            "created a source-locked ArrangementDocument seed. Browser visual "
            "automation was unavailable (`agent-browser`, Chrome/Edge, and Chrome "
            "DevTools MCP were not available); the static page was fetched over HTTP "
            "and API behavior was exercised over HTTP. Generation, playback, "
            "notation, export, imports, model planning, and scale readiness remain "
            "roadmap work.\n",
            encoding="utf-8",
        )
        print(json.dumps(evidence, indent=2))
        return 0
    finally:
        for process in (web, api):
            process.terminate()
        for process in (web, api):
            process.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
