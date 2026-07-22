import json
from copy import deepcopy
from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZIP_STORED, ZipFile

import pytest

from bandforge_domain.arrangements import build_arrangement_seed
from bandforge_domain.chart import StructuredChartInput, normalize_chart
from bandforge_domain.generator import ArrangementControls, generate_candidate
from bandforge_domain.packets import build_player_packet, validate_player_packet


def _candidate_document():
    chart = normalize_chart(
        StructuredChartInput(title="Packet Fixture", key="A_MINOR", bars=["Am", "F", "C", "G"])
    )
    source = build_arrangement_seed(
        chart,
        "src_rev_packet_001",
        "sha256:" + "b" * 64,
        datetime(2026, 7, 19, tzinfo=UTC),
        arrangement_id="arrangement_packet_001",
        version_id="version_packet_001",
    )
    result = generate_candidate(source, ArrangementControls(seed=23, tempo_bpm=108))
    assert result.accepted
    return result.document


def test_player_packet_is_deterministic_and_validates_hashes_and_traceability():
    candidate = _candidate_document()

    first = build_player_packet(candidate)
    second = build_player_packet(candidate)

    assert first.data == second.data
    assert first.manifest == second.manifest
    assert validate_player_packet(first.data, candidate) == {
        "fileNames": ["manifest.json", "score.musicxml"],
        "musicxmlBytes": first.manifest["files"]["score.musicxml"]["bytes"],
        "sourceRevisionIds": ["src_rev_packet_001"],
        "acceptedVersionId": candidate["versionId"],
        "rightsAttested": True,
    }
    assert first.manifest["files"]["score.musicxml"]["sha256"].startswith("sha256:")
    assert first.manifest["sourceRevisionIds"] == ["src_rev_packet_001"]
    assert first.manifest["acceptedVersionId"] == candidate["versionId"]
    assert first.manifest["lineage"] == candidate["extensions"]["bandforge.generation-lineage"]


def test_player_packet_rejects_bad_zip_names_hashes_and_xml():
    candidate = _candidate_document()
    packet = build_player_packet(candidate)

    with pytest.raises(ValueError, match="ZIP"):
        validate_player_packet(packet.data[:-10], candidate)

    tampered = bytearray(packet.data)
    marker = b"score.musicxml"
    offset = tampered.find(marker)
    assert offset >= 0
    tampered[offset] = ord("x")
    with pytest.raises(ValueError, match="hash|file|ZIP"):
        validate_player_packet(bytes(tampered), candidate)

    invalid = deepcopy(candidate)
    invalid["status"] = "DRAFT"
    with pytest.raises(ValueError, match="accepted"):
        build_player_packet(invalid)


def test_player_packet_rejects_non_object_manifest_json():
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        archive.writestr("manifest.json", b"[]")
        archive.writestr("score.musicxml", b"<score-partwise version='4.0'/>")

    with pytest.raises(ValueError, match="manifest"):
        validate_player_packet(output.getvalue())


def _rewrite_manifest(packet: bytes, transform) -> bytes:
    with ZipFile(BytesIO(packet), "r") as archive:
        musicxml = archive.read("score.musicxml")
        manifest = json.loads(archive.read("manifest.json"))
    transform(manifest)
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest).encode("utf-8"))
        archive.writestr("score.musicxml", musicxml)
    return output.getvalue()


def test_player_packet_rejects_missing_or_tampered_lineage():
    candidate = _candidate_document()
    packet = build_player_packet(candidate)

    tampered = _rewrite_manifest(
        packet.data,
        lambda manifest: manifest["lineage"].update({"seed": 999}),
    )
    with pytest.raises(ValueError, match="lineage"):
        validate_player_packet(tampered, candidate)

    missing = _rewrite_manifest(packet.data, lambda manifest: manifest.pop("lineage"))
    with pytest.raises(ValueError, match="lineage"):
        validate_player_packet(missing, candidate)


def test_player_packet_rejects_malformed_nested_manifest_without_candidate():
    candidate = _candidate_document()
    packet = build_player_packet(candidate)

    malformed = _rewrite_manifest(
        packet.data,
        lambda manifest: manifest.update({"files": []}),
    )

    with pytest.raises(ValueError, match="manifest"):
        validate_player_packet(malformed)


def test_player_packet_rejects_malformed_nested_file_object_without_candidate():
    candidate = _candidate_document()
    packet = build_player_packet(candidate)

    malformed = _rewrite_manifest(
        packet.data,
        lambda manifest: manifest["files"].update({"score.musicxml": []}),
    )

    with pytest.raises(ValueError, match="manifest"):
        validate_player_packet(malformed)


def test_player_packet_validates_required_manifest_without_candidate():
    candidate = _candidate_document()
    packet = build_player_packet(candidate)

    result = validate_player_packet(packet.data)

    assert result["sourceRevisionIds"] == ["src_rev_packet_001"]
    assert result["acceptedVersionId"] == candidate["versionId"]
