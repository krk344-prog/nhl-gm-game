import json
import tempfile
import unittest
from pathlib import Path

from src.competitive_research_agent import (
    CleanRoomPolicy,
    CleanRoomViolation,
    CompetitiveResearchAgent,
    EVIDENCE,
    run_and_write,
)


class CompetitiveResearchAgentTests(unittest.TestCase):
    def test_five_subagents_and_ranked_backlog(self):
        agent = CompetitiveResearchAgent()
        results = agent.run()
        self.assertEqual(len(results), 5)
        self.assertEqual(sum(len(r.evidence) for r in results), len(EVIDENCE))
        proposals = agent.synthesize(results)
        self.assertGreaterEqual(len(proposals), 12)
        self.assertEqual([p.rank for p in proposals], list(range(1, len(proposals) + 1)))
        self.assertEqual(proposals, agent.synthesize(agent.run()))

    def test_policy_blocks_proprietary_extraction(self):
        with self.assertRaises(CleanRoomViolation):
            CleanRoomPolicy.validate_request(
                "Decompile the game and extract proprietary code"
            )

    def test_unlicensed_public_repositories_are_reference_only(self):
        public = {
            evidence.source_id: evidence.disposition
            for evidence in EVIDENCE
            if evidence.access == "open_source"
        }
        self.assertEqual(public["hockey-gm-legacy"], "reference_only")
        self.assertEqual(public["zengm"], "reference_only")

    def test_writes_report_and_json_backlog(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            backlog = Path(tmp) / "backlog.json"
            run_and_write(report, backlog, "Research observable mechanics")
            self.assertIn("Ranked backlog", report.read_text())
            payload = json.loads(backlog.read_text())
            self.assertEqual(len(payload["subagents"]), 5)
            self.assertEqual(payload["features"][0]["rank"], 1)


if __name__ == "__main__":
    unittest.main()
