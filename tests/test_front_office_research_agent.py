from src.front_office_research_agent import build_baseline_snapshot


def test_baseline_snapshot_is_valid():
    snapshot = build_baseline_snapshot()
    snapshot.validate()
    assert len(snapshot.duties) >= 7
    assert len(snapshot.scenarios) >= 3


def test_backlog_identifies_missing_training_capabilities():
    snapshot = build_baseline_snapshot()
    backlog = snapshot.training_backlog({"daily_cap_ledger", "asset_valuation"})
    assert backlog
    roster_gap = next(item for item in backlog if item["duty"] == "roster_and_cap_management")
    assert "waiver_engine" in roster_gap["missing_capabilities"]
    assert "central_registry_gate" in roster_gap["missing_capabilities"]


def test_all_duties_have_training_objectives_and_evidence():
    snapshot = build_baseline_snapshot()
    for duty in snapshot.duties:
        assert duty.training_objective
        assert duty.evidence
