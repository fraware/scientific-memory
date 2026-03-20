"""Pipeline orchestrator delegates to publish without changing artifacts unnecessarily."""

from pathlib import Path

from sm_pipeline.models.stage_contracts import PipelineStage
from sm_pipeline.pipeline_orchestrator import run_pipeline_for_paper


def test_run_pipeline_publication_only_langmuir() -> None:
    repo = Path(__file__).resolve().parents[2]
    report = run_pipeline_for_paper(
        repo,
        "langmuir_1918_adsorption",
        stages=[PipelineStage.publication],
    )
    assert len(report.outcomes) == 1
    assert report.outcomes[0].stage == PipelineStage.publication
    assert report.outcomes[0].severity.value == "ok"
