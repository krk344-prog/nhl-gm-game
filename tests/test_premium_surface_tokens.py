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
