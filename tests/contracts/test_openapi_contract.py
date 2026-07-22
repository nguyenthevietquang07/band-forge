from pathlib import Path

import yaml
from openapi_spec_validator import validate

OPENAPI_PATH = Path(__file__).resolve().parents[2] / "contracts" / "openapi.yaml"


def test_openapi_document_is_semantically_valid() -> None:
    validate(yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8")))


def test_public_structured_source_contract_has_content_schema() -> None:
    document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    schema = document["components"]["schemas"]["CreateSourceRequest"]

    assert "content" in schema["properties"]
    assert "STRUCTURED" in schema["properties"]["sourceType"]["enum"]


def test_openapi_documents_candidate_projection_route() -> None:
    document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    route = document["paths"]["/arrangement-versions/{versionId}/candidates"]["post"]
    assert route["operationId"] == "createArrangementVersionCandidate"
    assert route["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/CandidateProjection"
    )


def test_openapi_documents_canonical_playback_plan_route() -> None:
    document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    route = document["paths"]["/arrangement-versions/{versionId}/playback-plan"]["post"]
    assert route["operationId"] == "createArrangementVersionPlaybackPlan"
    assert route["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/PlaybackPlanProjection"
    )
    request_schema = document["components"]["schemas"]["PlaybackPlanRequest"]
    assert "tempoOverrideBpm" in request_schema["properties"]
    response_schema = document["components"]["schemas"]["PlaybackPlanProjection"]
    assert "lineage" in response_schema["required"]
    assert response_schema["properties"]["lineage"]["$ref"] == (
        "#/components/schemas/GenerationLineage"
    )
