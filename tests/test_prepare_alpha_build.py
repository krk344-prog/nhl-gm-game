from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "prepare_alpha_build", SCRIPTS / "prepare_alpha_build.py"
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


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


def test_explicit_endpoint_produces_exact_pr13_dispatch_command():
    payload = module.prepare_build_handoff(
        api_base_url="http://192.168.1.20:8000/api/v1",
        preflight=_passing_preflight,
    )

    assert payload["ready"] is True
    assert payload["endpoint_source"] == "explicit"
    assert payload["ref"] == "agent/alpha-rules-integration-v1"
    assert payload["workflow"] == "ci.yml"
    assert (ROOT / ".github" / "workflows" / payload["workflow"]).is_file()
    assert payload["dispatch_argv"][:4] == ["gh", "workflow", "run", "ci.yml"]
    assert payload["dispatch_argv"][-1] == (
        "api_base_url=http://192.168.1.20:8000/api/v1"
    )
    assert "--ref agent/alpha-rules-integration-v1" in payload["dispatch_command"]


def test_discovered_endpoint_is_selected_preflighted_and_locked():
    payload = module.prepare_build_handoff(
        addresses=["127.0.0.1", "192.168.1.30"],
        preflight=_passing_preflight,
    )

    assert payload["endpoint_source"] == "discovered"
    assert payload["api_base_url"] == "http://192.168.1.30:8000/api/v1"
    assert payload["dispatch_argv"][-1] == (
        "api_base_url=http://192.168.1.30:8000/api/v1"
    )


def test_failed_preflight_blocks_dispatch_output():
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
        raise AssertionError("failed preflight must block the dispatch handoff")
