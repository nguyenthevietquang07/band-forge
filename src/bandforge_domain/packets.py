"""Deterministic dependency-free ZIP player packets."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from bandforge_domain.notation import (
    export_candidate_musicxml,
    validate_generation_lineage,
    validate_musicxml,
)


@dataclass(frozen=True)
class PlayerPacketArtifact:
    data: bytes
    manifest: dict[str, Any]


def build_player_packet(candidate: Mapping[str, Any]) -> PlayerPacketArtifact:
    """Build a deterministic ZIP containing score.musicxml and manifest.json."""
    notation = export_candidate_musicxml(candidate)
    xml_hash = "sha256:" + hashlib.sha256(notation.data).hexdigest()
    manifest = {
        "artifactType": "BAND_FORGE_PLAYER_PACKET",
        "formatVersion": "1.0",
        "files": {
            "score.musicxml": {
                "bytes": len(notation.data),
                "sha256": xml_hash,
            }
        },
        "sourceRevisionIds": notation.manifest["sourceRevisionIds"],
        "acceptedVersionId": notation.manifest["acceptedVersionId"],
        "rightsAttested": notation.manifest["rightsAttested"],
        "lineage": notation.manifest["lineage"],
    }
    manifest_data = _json_bytes(manifest)
    packet = _zip_bytes({"manifest.json": manifest_data, "score.musicxml": notation.data})
    return PlayerPacketArtifact(data=packet, manifest=manifest)


def validate_player_packet(
    data: bytes, candidate: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Validate packet names, manifest hashes, XML structure, and traceability."""
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            names = archive.namelist()
            if len(names) != 2 or len(set(names)) != 2 or set(names) != {
                "manifest.json",
                "score.musicxml",
            }:
                raise ValueError("ZIP packet contains unexpected file names")
            manifest_data = archive.read("manifest.json")
            musicxml_data = archive.read("score.musicxml")
    except (zipfile.BadZipFile, KeyError, OSError) as error:
        raise ValueError(f"ZIP packet is malformed: {error}") from error
    try:
        manifest = json.loads(manifest_data)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"ZIP manifest is malformed JSON: {error}") from error
    if not isinstance(manifest, dict):
        raise ValueError("ZIP manifest must be a JSON object")
    _require_manifest_shape(manifest)
    score_file = manifest["files"]["score.musicxml"]
    expected_hash = score_file["sha256"]
    actual_hash = "sha256:" + hashlib.sha256(musicxml_data).hexdigest()
    if expected_hash != actual_hash:
        raise ValueError("ZIP manifest MusicXML hash does not match content")
    if score_file["bytes"] != len(musicxml_data):
        raise ValueError("ZIP manifest MusicXML byte count does not match content")
    validate_musicxml(musicxml_data, candidate)
    if candidate is not None:
        expected_source_ids = [ref["sourceRevisionId"] for ref in candidate["sourceRefs"]]
        if manifest["sourceRevisionIds"] != expected_source_ids:
            raise ValueError("ZIP manifest source revision traceability does not match candidate")
        if manifest["acceptedVersionId"] != candidate["versionId"]:
            raise ValueError("ZIP manifest accepted version traceability does not match candidate")
        if manifest["rightsAttested"] is not True:
            raise ValueError("ZIP manifest must preserve rights attestation")
        candidate_lineage = candidate.get("extensions", {}).get(
            "bandforge.generation-lineage"
        )
        try:
            candidate_lineage = validate_generation_lineage(candidate_lineage)
        except ValueError as error:
            raise ValueError(f"ZIP candidate lineage is invalid: {error}") from error
        if manifest["lineage"] != candidate_lineage:
            raise ValueError("ZIP manifest lineage does not match candidate")
    return {
        "fileNames": sorted(names),
        "musicxmlBytes": len(musicxml_data),
        "sourceRevisionIds": manifest["sourceRevisionIds"],
        "acceptedVersionId": manifest["acceptedVersionId"],
        "rightsAttested": manifest["rightsAttested"],
    }


def _require_manifest_shape(manifest: Mapping[str, Any]) -> None:
    if manifest.get("artifactType") != "BAND_FORGE_PLAYER_PACKET":
        raise ValueError("ZIP manifest artifactType is invalid")
    if manifest.get("formatVersion") != "1.0":
        raise ValueError("ZIP manifest formatVersion is invalid")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != {"score.musicxml"}:
        raise ValueError("ZIP manifest files must contain score.musicxml")
    score_file = files["score.musicxml"]
    if not isinstance(score_file, dict):
        raise ValueError("ZIP manifest score.musicxml must be an object")
    byte_count = score_file.get("bytes")
    if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 1:
        raise ValueError("ZIP manifest score.musicxml bytes is invalid")
    content_hash = score_file.get("sha256")
    if (
        not isinstance(content_hash, str)
        or len(content_hash) != 71
        or not content_hash.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in content_hash[7:])
    ):
        raise ValueError("ZIP manifest score.musicxml sha256 is invalid")
    source_revision_ids = manifest.get("sourceRevisionIds")
    if not isinstance(source_revision_ids, list) or not source_revision_ids:
        raise ValueError("ZIP manifest sourceRevisionIds is invalid")
    if not all(isinstance(value, str) and bool(value) for value in source_revision_ids):
        raise ValueError("ZIP manifest sourceRevisionIds is invalid")
    accepted_version_id = manifest.get("acceptedVersionId")
    if not isinstance(accepted_version_id, str) or not accepted_version_id:
        raise ValueError("ZIP manifest acceptedVersionId is invalid")
    if manifest.get("rightsAttested") is not True:
        raise ValueError("ZIP manifest rightsAttested must be true")
    try:
        validate_generation_lineage(manifest.get("lineage"))
    except ValueError as error:
        raise ValueError(f"ZIP manifest lineage is invalid: {error}") from error


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _zip_bytes(files: Mapping[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 0
            info.external_attr = 0
            archive.writestr(info, files[name])
    return output.getvalue()
