import json
from workflow_runtime.infrastructure.memory.context_extractor import ProjectContextExtractor
from workflow_runtime.infrastructure.memory.ai_synthesizer import AISynthesizer
from workflow_runtime.infrastructure.memory.markdown_writer import (
    generate_project_summary,
    write_architecture_domain_models,
    write_architecture_overview,
)


def test_context_extractor():
    extractor = ProjectContextExtractor(".")
    payload = extractor.get_full_context_payload()
    assert "project_id" in payload
    assert "manifests" in payload
    assert "readme_docs" in payload
    symbols = extractor.extract_code_symbols()
    assert isinstance(symbols, list)


def test_ai_synthesizer_prompt_builder():
    synthesizer = AISynthesizer(".")
    ctx = {"project_id": "test-app", "manifests": {}}
    prompt = synthesizer.build_synthesis_prompt(ctx)
    assert "Principal Software Architect" in prompt
    assert "business_purpose" in prompt


def test_markdown_with_ai_synth(tmp_path):
    info = {"project_name": "test-ai", "languages": ["Python"]}
    ai_synth = {
        "business_purpose": "An AI-powered high-throughput cognitive engine.",
        "architecture_style": "Clean Architecture with Event-Driven Sinks.",
        "system_context": "Clients publish events which are filtered and forwarded.",
        "core_subsystems": [{"name": "Engine", "path": "engine", "purpose": "Core processing loop"}],
        "data_flow_description": "Input stream -> Validation -> Ingestion -> Index.",
        "api_contracts_summary": "REST POST /ingest, GET /query",
        "invariants_and_rules": ["Zero mutation outside worker thread"],
        "known_pitfalls": ["Buffer overflow on unthrottled bursts"]
    }

    summary = generate_project_summary(info, ai_synth)
    assert "An AI-powered high-throughput cognitive engine." in summary
    assert "Clean Architecture with Event-Driven Sinks." in summary

    overview_file = tmp_path / "overview.md"
    write_architecture_overview(str(overview_file), info, ai_synth)
    assert overview_file.exists()
    content = overview_file.read_text(encoding="utf-8")
    assert "Clients publish events which are filtered and forwarded." in content

    models_file = tmp_path / "domain-models.md"
    write_architecture_domain_models(str(models_file), [{"name": "UserSession", "kind": "class", "file": "session.py"}])
    assert models_file.exists()
    assert "UserSession" in models_file.read_text(encoding="utf-8")
