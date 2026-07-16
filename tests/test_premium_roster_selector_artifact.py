from pathlib import Path
import xml.etree.ElementTree as ET


def test_premium_roster_selector_is_accessible_and_reviewable() -> None:
    artifact = Path("docs/ui/new-game-roster-pack-premium-v2.svg")
    assert artifact.exists()

    source = artifact.read_text(encoding="utf-8")
    root = ET.fromstring(source)

    assert root.attrib["role"] == "img"
    assert root.attrib["aria-labelledby"] == "title desc"
    assert root.attrib["viewBox"] == "0 0 1440 900"

    # Preserve Kyle's approved visual foundation and verify the premium-depth primitives.
    assert 'fill="#000000"' in source
    assert 'id="ambient"' in source
    assert 'id="shadow"' in source
    assert 'id="card"' in source

    # Verify franchise identity, disclosure, and a realistic non-ideal state are visible in the preview.
    for required_label in (
        "Buffalo Harbor Northstars",
        "Rochester Forge",
        "Real identity",
        "Generated ratings",
        "Unknown contracts",
        "NEEDS REVIEW",
        "Selection blocked",
        "UI Review Pending",
    ):
        assert required_label in source
