"""SQLite development persistence for the source-to-arrangement workflow."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class SongRow(Base):
    __tablename__ = "songs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    artist: Mapped[str | None] = mapped_column(String(300), nullable=True)
    metadata_provider_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceRevisionRow(Base):
    __tablename__ = "source_revisions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    rights_attested: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    chart_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class ArrangementVersionRow(Base):
    __tablename__ = "arrangement_versions"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    source_revision_id: Mapped[str] = mapped_column(
        ForeignKey("source_revisions.id"), nullable=False
    )
    arrangement_id: Mapped[str | None] = mapped_column(
        ForeignKey("arrangements.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    document_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class ArrangementRow(Base):
    __tablename__ = "arrangements"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    song_id: Mapped[str] = mapped_column(ForeignKey("songs.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    current_draft_version_id: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)


class IdempotencyRow(Base):
    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)


_SQLITE_MIGRATION_COLUMNS = {
    "songs": {
        "artist": "VARCHAR(300)",
        "metadata_provider_id": "TEXT",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    },
    "source_revisions": {"created_at": "DATETIME"},
    "arrangements": {"title": "VARCHAR(300)", "created_at": "DATETIME"},
    "arrangement_versions": {
        "arrangement_id": "VARCHAR(80)",
        "status": "VARCHAR(32)",
        "content_hash": "VARCHAR(71)",
        "created_at": "DATETIME",
    },
}


def _migrate_sqlite_schema(engine) -> None:
    """Upgrade the small checked-in SQLite fixture without dropping data."""

    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, columns in _SQLITE_MIGRATION_COLUMNS.items():
            existing = {column["name"] for column in inspector.get_columns(table)}
            for column, sql_type in columns.items():
                if column not in existing:
                    connection.exec_driver_sql(
                        f'ALTER TABLE "{table}" ADD COLUMN "{column}" {sql_type}'
                    )

        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")
        for table in ("songs", "source_revisions", "arrangements", "arrangement_versions"):
            connection.execute(
                text(f'UPDATE "{table}" SET created_at = :now WHERE created_at IS NULL'),
                {"now": now},
            )
        connection.execute(
            text('UPDATE "songs" SET updated_at = :now WHERE updated_at IS NULL'),
            {"now": now},
        )
        connection.execute(
            text(
                'UPDATE "arrangements" SET title = '
                '(SELECT title FROM songs WHERE songs.id = arrangements.song_id) '
                'WHERE title IS NULL'
            )
        )
        connection.execute(
            text(
                'UPDATE "arrangement_versions" SET arrangement_id = '
                '(SELECT id FROM arrangements '
                'WHERE arrangements.current_draft_version_id = arrangement_versions.id) '
                'WHERE arrangement_id IS NULL'
            )
        )
        connection.execute(
            text('UPDATE "arrangement_versions" SET status = :status WHERE status IS NULL'),
            {"status": "DRAFT"},
        )

        legacy_versions = connection.execute(
            text(
                'SELECT id, arrangement_id, document_json FROM arrangement_versions '
                'WHERE arrangement_id IS NOT NULL'
            )
        ).mappings()
        for row in legacy_versions:
            try:
                document = json.loads(row["document_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(document, dict):
                continue
            document["arrangementId"] = row["arrangement_id"]
            document["versionId"] = row["id"]
            canonical_json = json.dumps(document, separators=(",", ":"), sort_keys=True)
            connection.execute(
                text(
                    'UPDATE "arrangement_versions" SET document_json = :document_json, '
                    'content_hash = :content_hash WHERE id = :id'
                ),
                {
                    "document_json": canonical_json,
                    "content_hash": f"sha256:{hashlib.sha256(canonical_json.encode()).hexdigest()}",
                    "id": row["id"],
                },
            )


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    _migrate_sqlite_schema(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
