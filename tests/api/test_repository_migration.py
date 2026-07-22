from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from bandforge_api.repository import ArrangementVersionRow, SongRow, create_session_factory


def test_checked_in_legacy_sqlite_fixture_is_upgraded_without_replacing_rows(tmp_path):
    source = Path(__file__).parents[2] / "bandforge-dev.sqlite3"
    database = tmp_path / "legacy-copy.sqlite3"
    shutil.copy2(source, database)

    session_factory = create_session_factory(f"sqlite:///{database}")

    with session_factory() as session:
        song = session.get(SongRow, "song_4020461c773d48a4be438bdefaed6d27")
        version = session.get(
            ArrangementVersionRow,
            "arr_version_c6b2cd4faa124b75b607332140b89a13",
        )

    assert song is not None
    assert song.title == "BandForge Cycle 2 Original"
    assert song.artist is None
    assert song.created_at is not None
    assert version is not None
    assert version.arrangement_id == "arrangement_edff83eb6ad4416895b12081f321c048"
    assert '"arrangementId":"arrangement_edff83eb6ad4416895b12081f321c048"' in (
        version.document_json.replace(" ", "")
    )
    assert '"versionId":"arr_version_c6b2cd4faa124b75b607332140b89a13"' in (
        version.document_json.replace(" ", "")
    )

    with sqlite3.connect(database) as connection:
        tables = {
            row[0]: {column[1] for column in connection.execute(f"PRAGMA table_info({row[0]})")}
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert {"artist", "metadata_provider_id", "created_at", "updated_at"} <= tables["songs"]
    assert {"arrangement_id", "status", "content_hash", "created_at"} <= tables[
        "arrangement_versions"
    ]

    second_factory = create_session_factory(f"sqlite:///{database}")
    with second_factory() as session:
        second_version = session.get(
            ArrangementVersionRow,
            "arr_version_c6b2cd4faa124b75b607332140b89a13",
        )
    assert second_version is not None
    assert second_version.content_hash.startswith("sha256:")
