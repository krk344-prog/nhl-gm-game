import json
from pathlib import Path


def test_premium_surface_tokens_are_accessible_and_bounded() -> None:
    tokens_path = Path("docs/ui/premium-surface-tokens-v1.json")
    tokens = json.loads(tokens_path.read_text(encoding="utf-8"))

    assert tokens["status"] == "UI Review Pending"
    assert tokens["foundation"]["canvas"] == "#000000"
    assert tokens["accessibility"]["minimum_touch_target_px"] >= 44
    assert tokens["accessibility"]["minimum_body_text_px"] >= 14
    assert tokens["accessibility"]["status_requires_text_or_icon"] is True
    assert tokens["accessibility"]["logo_fallback_initials"] is True
    assert tokens["density"]["card_primary_action_limit"] == 1
    assert tokens["density"]["visible_consequence_limit"] <= 3
    assert tokens["density"]["details_pattern_desktop"] == "drawer"
    assert tokens["density"]["details_pattern_mobile"] == "bottom-sheet"


def test_premium_interaction_tokens_prevent_motion_and_state_regressions() -> None:
    tokens_path = Path("docs/ui/premium-surface-tokens-v1.json")
    tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    interaction = tokens["interaction"]

    assert 100 <= interaction["transition_min_ms"] <= interaction["transition_max_ms"] <= 200
    assert interaction["hover_layout_shift_allowed"] is False
    assert interaction["reduced_motion_removes_nonessential_animation"] is True
    assert interaction["blocked_state_requires_reason"] is True
    assert interaction["selected_state_requires_persistent_indicator"] is True


def test_premium_atmosphere_is_restrained_and_purposeful() -> None:
    tokens_path = Path("docs/ui/premium-surface-tokens-v1.json")
    tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    atmosphere = tokens["atmosphere"]

    assert atmosphere["ambient_gradient_allowed"] is True
    assert 0 < atmosphere["ambient_gradient_max_opacity"] <= 0.20
    assert 0 <= atmosphere["texture_max_opacity"] <= 0.05
    assert atmosphere["glow_regions_max"] <= 2
    assert atmosphere["glow_must_anchor_identity_or_action"] is True
    assert atmosphere["decorative_motion_allowed"] is False
    assert tokens["franchise_accent"]["maximum_visible_surface_ratio"] <= 0.15
