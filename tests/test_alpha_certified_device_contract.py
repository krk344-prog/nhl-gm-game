from pathlib import Path


def test_certified_handoff_rechecks_device_identity_before_release_handoff():
    script = Path("scripts/run_alpha_certified_release_handoff.py").read_text(encoding="utf-8")

    validate_call = script.index("validate_certified_device(", script.index("def run_certified_handoff"))
    release_call = script.index("return run_release_handoff(", script.index("def run_certified_handoff"))

    assert validate_call < release_call
    assert "device preflight did not confirm ready" in script
    assert "certified device changed after execution readiness" in script
    assert "certified device identity changed after execution readiness" in script
