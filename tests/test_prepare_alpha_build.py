from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("prepare_alpha_build", SCRIPTS / "prepare_alpha_build.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

build_spec = importlib.util.spec_from_file_location("build_alpha_apk_local", SCRIPTS / "build_alpha_apk_local.py")
assert build_spec and build_spec.loader
builder = importlib.util.module_from_spec(build_spec)
build_spec.loader.exec_module(builder)


def _passing_preflight(api_base_url, *, season_id, timeout, allow_loopback):
    assert timeout == 5.0
    assert allow_loopback is False
    return module.PreflightResult(
        api_base_url=api_base_url.rstrip("/"),
        health_status="ok",
        api_version="alpha",
        season_id=season_id,
        regular_season_games=84,
        ready=True,
    )


def test_explicit_endpoint_produces_exact_pr13_local_build_command():
    payload = module.prepare_build_handoff(
        api_base_url="http://192.168.1.20:8000/api/v1",
        preflight=_passing_preflight,
    )
    assert payload["ready"] is True
    assert payload["endpoint_source"] == "explicit"
    assert payload["ref"] == "agent/alpha-rules-integration-v1"
    assert payload["build_script"] == "scripts/build_alpha_apk_local.py"
    assert (ROOT / payload["build_script"]).is_file()
    assert payload["build_argv"][-3:] == [
        "--api-base-url",
        "http://192.168.1.20:8000/api/v1",
        "--execute",
    ]
    assert "gh workflow run" not in payload["build_command"]


def test_discovered_endpoint_is_selected_preflighted_and_locked():
    payload = module.prepare_build_handoff(
        addresses=["127.0.0.1", "192.168.1.30"],
        preflight=_passing_preflight,
    )
    assert payload["endpoint_source"] == "discovered"
    assert payload["api_base_url"] == "http://192.168.1.30:8000/api/v1"
    assert payload["build_argv"][-2] == "http://192.168.1.30:8000/api/v1"


def test_failed_preflight_blocks_build_output():
    def failed_preflight(*args, **kwargs):
        raise RuntimeError("backend unavailable")
    try:
        module.prepare_build_handoff(
            api_base_url="http://192.168.1.20:8000/api/v1",
            preflight=failed_preflight,
        )
    except RuntimeError as exc:
        assert str(exc) == "backend unavailable"
    else:
        raise AssertionError("failed preflight must block the build handoff")


def test_local_builder_rejects_loopback_and_wrong_routes():
    for endpoint in (
        "http://127.0.0.1:8000/api/v1",
        "http://192.168.1.20:8000/api/v2",
        "http://192.168.1.20:8000/api/v1?debug=1",
    ):
        try:
            builder.validate_api_base_url(endpoint)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe endpoint accepted: {endpoint}")


def test_local_builder_plan_contains_export_prebuild_and_apk_steps():
    plan = builder.command_plan("http://192.168.1.20:8000/api/v1")
    flattened = [item for command in plan for item in command]
    assert plan[0] == ["npm", "ci"]
    assert "export" in flattened
    assert "prebuild" in flattened
    assert "assembleDebug" in flattened
