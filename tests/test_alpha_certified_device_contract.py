from pathlib import Path


def test_certified_handoff_rechecks_device_identity_before_release_handoff():
    script = Path("scripts/run_alpha_certified_release_handoff.py").read_text(encoding="utf-8")

    validate_call = script.index("validate_certified_device(", script.index("def run_certified_handoff"))
    release_call = script.index("return run_release_handoff(", script.index("def run_certified_handoff"))

    assert validate_call < release_call
    assert "device preflight did not confirm ready" in script
    assert "certified device changed after execution readiness" in script
    assert "certified device identity changed after execution readiness" in script


def test_certified_handoff_requires_normalizes_and_forwards_selected_serial_to_guarded_release():
    script = Path("scripts/run_alpha_certified_release_handoff.py").read_text(encoding="utf-8")
    handoff = script[script.index("def run_certified_handoff"):script.index("def main")]
    cli = script[script.index("def main"):]

    assert 'parser.add_argument("--serial", required=True)' in cli
    assert "serial = _normalize(serial)" in handoff
    assert "exact device serial is required" in handoff
    assert '"--serial",\n        serial,' in handoff
    assert "return run_release_handoff(" in handoff
    release_call = handoff[handoff.index("return run_release_handoff("):]
    assert "serial=serial," in release_call


def test_certified_handoff_uses_privacy_safe_identity_key_for_exact_device_preflight():
    script = Path("scripts/run_alpha_certified_release_handoff.py").read_text(encoding="utf-8")
    handoff = script[script.index("def run_certified_handoff"):script.index("def main")]
    cli = script[script.index("def main"):]

    assert 'parser.add_argument("--device-identity-key", required=True)' in cli
    assert 'parser.add_argument("--expected-device-identity", required=True)' in cli
    assert "device_identity_key = _normalize(device_identity_key)" in handoff
    assert "expected_device_identity = _normalize(expected_device_identity)" in handoff
    assert "privacy-safe device identity inputs are required" in handoff
    assert '"--identity-key",\n        device_identity_key,' in handoff
    assert handoff.index('"--identity-key"') < handoff.index('"--serial"')
    assert "device_identity=expected_device_identity," in handoff
