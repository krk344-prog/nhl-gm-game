"""Clean-room competitive research agent for the NHL GM simulation.

Five specialist subagents evaluate observable mechanics from hockey management
simulations, public repositories, and hockey-operations research. A synthesis
agent merges the evidence into an original, ranked implementation backlog.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


class CleanRoomViolation(ValueError):
    pass


class CleanRoomPolicy:
    """Prevent proprietary-code extraction and classify code reuse eligibility."""

    BLOCKED = (
        "decompile",
        "extract proprietary code",
        "copy proprietary source",
        "rip assets",
        "bypass drm",
    )
    PERMISSIVE = {
        "0BSD", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
        "CC0-1.0", "ISC", "MIT", "Unlicense",
    }

    @classmethod
    def validate_request(cls, request: str) -> None:
        normalized = " ".join(request.lower().split())
        for phrase in cls.BLOCKED:
            if phrase in normalized:
                raise CleanRoomViolation(f"Clean-room policy blocks requests to {phrase}.")

    @classmethod
    def disposition(cls, access: str, license_id: str | None) -> str:
        if access == "proprietary":
            return "original_clean_room_only"
        if access != "open_source" or not license_id:
            return "reference_only"
        if license_id in cls.PERMISSIVE:
            return "reuse_candidate_with_attribution"
        return "legal_review_required"


@dataclass(frozen=True)
class Evidence:
    agent: str
    source_id: str
    source: str
    url: str
    game: str
    feature_id: str
    feature: str
    category: str
    observation: str
    original_design: str
    dependencies: tuple[str, ...]
    scores: tuple[int, int, int, int, int]
    access: str = "proprietary"
    license_id: str | None = None

    @property
    def disposition(self) -> str:
        return CleanRoomPolicy.disposition(self.access, self.license_id)


@dataclass(frozen=True)
class SubAgentResult:
    name: str
    mission: str
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class Proposal:
    rank: int
    feature_id: str
    feature: str
    category: str
    score: int
    phase: str
    references: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    original_design: str
    dependencies: tuple[str, ...]
    implementation_mode: str


MISSIONS = {
    "hlm26": "HLM 26 career, scouting, development, CBA, staffing, and trade systems",
    "ea_nhl": "EA NHL Franchise presentation, ownership, delegation, and player identity",
    "deep_sims": "FHM/EHM draft, tactics, multi-league depth, and explainable AI",
    "open_source": "Public hockey-simulation repositories and license eligibility",
    "real_world": "Training-grade hockey operations, analytics, and validation",
}


EVIDENCE = (
    Evidence("hlm26", "hlm26-career", "HLM 26 official features", "https://hockeylegacymanager.com/hlm26/", "HLM 26", "career", "Executive career and reputation", "career", "Trades, signings, and results shape GM reputation and career mobility.", "Persist ownership trust, agent/player relations, transaction fairness, media credibility, employment history, and firing/hiring logic.", ("multi-season saves", "owner objectives"), (5, 5, 4, 5, 5)),
    Evidence("hlm26", "hlm26-training", "HLM training documentation", "https://hockeylegacymanager.com/features/trainings/", "HLM 26", "development", "Individual development plans", "player development", "Training capacity, focus, age, potential, coaching, usage, injury, production, and league level affect growth.", "Calculate monthly attribute changes from age curves, hidden potential, usage quality, competition, health, confidence, coach fit, and selected focus; archive recommendations and outcomes.", ("staff", "usage tracking", "injuries", "minor leagues"), (5, 5, 3, 5, 5)),
    Evidence("hlm26", "hlm26-scouting", "HLM scouting documentation", "https://hockeylegacymanager.com/features/scouting/", "HLM 26", "scouting", "Scouting intelligence and uncertainty", "scouting", "Regional knowledge, workload, assignments, budget, and progressive information unlocks make information scarce.", "Store team-specific knowledge profiles with confidence ranges, stale reports, scout bias, consensus estimates, travel time, assignment capacity, and calibration history.", ("hidden ratings", "staff", "budget", "prospects"), (5, 5, 3, 5, 5)),
    Evidence("hlm26", "hlm26-contracts", "HLM contract documentation", "https://hockeylegacymanager.com/features/contracts/", "HLM 26", "cba", "NHL contract rights and clauses", "contracts/CBA", "Contract limits, UFA/RFA rights, qualifying offers, entry-level deals, movement clauses, waivers, and retained salary constrain decisions.", "Build a dated rights ledger and rule service for reserve lists, contract slots, ELC slides, waivers, arbitration, qualifying offers, offer sheets, clauses, buyouts, and retention.", ("calendar", "contract ledger", "waivers"), (5, 5, 3, 5, 5)),
    Evidence("hlm26", "hlm26-trades", "HLM trade documentation", "https://hockeylegacymanager.com/features/trades/", "HLM 26", "trades", "Negotiated trade market", "transactions", "Multi-asset trades, picks, retained salary, cap checks, and smarter counterparties deepen negotiation.", "Support multi-asset proposals, conditions, protection, retention slots, counteroffers, rival needs, deadline leverage, movement-clause approval, and atomic compliance checks.", ("picks", "contracts", "AI plans", "relationships"), (5, 5, 3, 5, 5)),
    Evidence("hlm26", "hlm26-staff", "HLM coaching documentation", "https://hockeylegacymanager.com/features/coaching-staff/", "HLM 26", "staff", "Hockey operations staff market", "staff", "Coaches have category grades, styles, role fit, competitive-window fit, and development.", "Model contracts, specialties, relationships, workload, growth, philosophy fit, budgets, interviews, and authority for AGM, cap, scouting, development, analytics, medical, and coaching roles.", ("staff entities", "budget", "delegation"), (5, 5, 3, 5, 5)),
    Evidence("ea_nhl", "ea-franchise", "EA NHL Franchise mode", "https://www.ea.com/games/nhl/nhl-26", "EA NHL Franchise", "ownership", "Owner goals, budget, and job security", "ownership", "Owner expectations and budget allocation add pressure beyond standings.", "Generate weighted annual mandates, budget envelopes, patience, intervention thresholds, board reviews, and explainable trust changes tied to both process and results.", ("finances", "career", "fan model"), (5, 5, 3, 4, 5)),
    Evidence("ea_nhl", "ea-franchise", "EA NHL Franchise mode", "https://www.ea.com/games/nhl/nhl-26", "EA NHL Franchise", "delegation", "Assistant GM delegation controls", "workflow", "Users can delegate franchise domains to AI, keeping depth manageable.", "Add per-domain authority, approval thresholds, recommendation-only mode, staff competency effects, exception queues, and complete decision logs.", ("staff", "action center", "audit log"), (5, 5, 4, 4, 5)),
    Evidence("ea_nhl", "ea-iceq", "EA NHL 26 ICE-Q 2.0", "https://www.ea.com/games/nhl/nhl-26", "EA NHL 26", "identity", "Data-driven player identity", "simulation", "Tracking-informed physical tools and tendencies make players behave differently rather than merely display different overalls.", "Separate physical tools, tendencies, decision frequencies, role actions, and context splits; calibrate original simulation behavior against public hockey distributions.", ("event simulation", "attributes", "calibration"), (5, 5, 2, 5, 5)),
    Evidence("deep_sims", "fhm12", "Franchise Hockey Manager 12", "https://www.ootpdevelopments.com/franchise-hockey-manager-home/", "FHM 12", "draft", "Live draft war room", "draft", "A live draft with trade offers, news, changing availability, and time pressure turns selection into an operating event.", "Implement a pausable clock, live board, scout disagreement, contingency queue, calls, pick-value ranges, organizational need, and a decision audit trail.", ("draft classes", "scouting", "trades", "AI plans"), (5, 5, 3, 5, 5)),
    Evidence("deep_sims", "fhm12", "Franchise Hockey Manager 12", "https://www.ootpdevelopments.com/franchise-hockey-manager-home/", "FHM 12", "explainable_ai", "Explainable league AI", "artificial intelligence", "AI roster and transaction decisions are more credible when news explains their rationale.", "Require each AI move to retain objectives, candidate options, constraint checks, rejected alternatives, confidence, and a public explanation derived from a private organization plan.", ("AI plans", "transactions", "news"), (5, 5, 3, 5, 5)),
    Evidence("deep_sims", "ehm", "Eastside Hockey Manager", "https://store.steampowered.com/app/301120/Eastside_Hockey_Manager/", "EHM", "league_world", "Multi-league organization ecosystem", "league architecture", "Many leagues, affiliates, rights systems, international play, and persistent careers create a living hockey world.", "Create configurable rulebooks, affiliations, rights types, player movement agreements, international windows, and background-simulation fidelity tiers.", ("rule engine", "schedules", "rights", "world sim"), (5, 5, 2, 5, 5)),
    Evidence("deep_sims", "ehm", "Eastside Hockey Manager", "https://store.steampowered.com/app/301120/Eastside_Hockey_Manager/", "EHM", "tactics", "Tactical feedback and match analysis", "coaching", "Detailed tactics and match feedback connect management choices to outcomes.", "Record possession states, zone entries, shot quality, matchups, special teams, fatigue, and adjustments; explain postgame which choices likely moved the result.", ("event simulation", "lineups", "analytics"), (5, 5, 3, 5, 5)),
    Evidence("open_source", "hockey-gm-legacy", "Hockey GM Legacy repository", "https://github.com/noflow/Hockey-gm-Legacy", "Hockey GM Legacy", "command_center", "Action-first GM command center", "user experience", "A public project organizes the day around an office, action center, dossiers, reports, and decisions.", "Use only the high-level workflow idea and independently implement a mobile morning briefing with urgent decisions, evidence, and drill-down navigation.", ("action center", "notifications", "mobile navigation"), (4, 5, 4, 4, 5), "open_source", None),
    Evidence("open_source", "zengm", "ZenGM repository", "https://github.com/zengm-games/zengm", "ZenGM Hockey", "modding", "Rulebook and database modding", "platform", "A mature public simulation demonstrates the value of import/export and configurable leagues, but reuse requires a verified license.", "Create independent versioned JSON schemas, validators, migrations, scenario imports, and exports; keep external source reference-only until licensing is resolved.", ("schemas", "import/export", "rule engine"), (4, 5, 3, 5, 4), "open_source", None),
    Evidence("real_world", "scouting-roi", "NHL scouting ROI research", "https://arxiv.org/abs/1411.5754", "Hockey operations research", "scouting", "Scouting intelligence and uncertainty", "scouting", "Team scouting can improve draft rankings beyond public consensus, making information quality a measurable asset.", "Backtest scout calls against outcomes, track calibration by scout and attribute, value information gain, and let budget choices alter coverage and certainty.", ("historical outcomes", "analytics", "scouting"), (5, 5, 3, 5, 5), "public_research", None),
    Evidence("real_world", "player-value", "Context-aware player evaluation research", "https://arxiv.org/abs/1805.11088", "Hockey operations research", "identity", "Data-driven player identity", "simulation", "Context-aware event value distinguishes actions by game state and sequence, not box scores alone.", "Create interpretable expected-goal and possession-value features from simulated events and use them for role, contract, trade, and calibration analysis.", ("event simulation", "analytics", "calibration"), (5, 5, 2, 5, 5), "public_research", None),
    Evidence("real_world", "validation", "NHL public rules and data", "https://www.nhl.com/info/hockey-operations-guidelines", "Hockey operations research", "validation", "Simulation calibration and adversarial testing", "quality assurance", "A training-grade simulation needs statistical targets, CBA edge-case tests, and protection against dominant exploits.", "Run thousands of seeded seasons, compare distributions and correlations to public benchmarks, search for dominant strategies, stress legal boundaries, and enforce CI tolerances.", ("test harness", "benchmarks", "event simulation"), (5, 5, 4, 5, 5), "public_data", None),
    Evidence("real_world", "decision-audit", "Training simulation design", "https://www.nhl.com/info/hockey-operations-guidelines", "Front-office practice", "decision_audit", "Decision journals and after-action reviews", "training", "Training improves when assumptions, alternatives, approvals, dissent, risks, and outcomes are recorded.", "Capture optional decision memos and staff recommendations, score legal/financial process quality, and revisit major moves after 30 days, season end, and multiple years.", ("audit log", "executive reports", "action center"), (5, 4, 4, 5, 5), "public_practice", None),
)


class ResearchSubAgent:
    def __init__(self, name: str, mission: str):
        self.name = name
        self.mission = mission

    def run(self, evidence: Iterable[Evidence]) -> SubAgentResult:
        return SubAgentResult(self.name, self.mission, tuple(x for x in evidence if x.agent == self.name))


class CompetitiveResearchAgent:
    WEIGHTS = (0.30, 0.20, 0.20, 0.15, 0.15)

    def __init__(self) -> None:
        self.subagents = tuple(ResearchSubAgent(name, mission) for name, mission in MISSIONS.items())

    def run(self, request: str = "Research observable mechanics and write original specifications.") -> tuple[SubAgentResult, ...]:
        CleanRoomPolicy.validate_request(request)
        with ThreadPoolExecutor(max_workers=len(self.subagents)) as pool:
            return tuple(pool.map(lambda agent: agent.run(EVIDENCE), self.subagents))

    def synthesize(self, results: Iterable[SubAgentResult]) -> tuple[Proposal, ...]:
        return _rank(self, tuple(results))

    @staticmethod
    def _phase(score: int) -> str:
        return "foundation" if score >= 93 else "front-office depth" if score >= 88 else "immersion/scale"


def _rank(agent: CompetitiveResearchAgent, results: tuple[SubAgentResult, ...]) -> tuple[Proposal, ...]:
    grouped: dict[str, list[Evidence]] = {}
    for result in results:
        for item in result.evidence:
            grouped.setdefault(item.feature_id, []).append(item)
    proposals = []
    for items in grouped.values():
        first = items[0]
        averages = [sum(item.scores[i] for item in items) / len(items) for i in range(5)]
        score = min(100, round(sum(a * w for a, w in zip(averages, agent.WEIGHTS)) / 5 * 100 + min(5, 2 * (len({i.game for i in items}) - 1))))
        modes = {item.disposition for item in items}
        mode = "original_clean_room_implementation" if "original_clean_room_only" in modes else "licensed_reuse_candidate" if modes == {"reuse_candidate_with_attribution"} else "original_implementation_pending_legal_review" if "legal_review_required" in modes else "original_implementation_reference_only"
        proposals.append((score, first, items, mode))
    proposals.sort(key=lambda row: (-row[0], row[1].feature))
    return tuple(Proposal(rank, first.feature_id, first.feature, first.category, score, agent._phase(score), tuple(sorted({i.game for i in items})), tuple(sorted({i.source_id for i in items})), " | ".join(dict.fromkeys(i.original_design for i in items)), tuple(sorted({d for i in items for d in i.dependencies})), mode) for rank, (score, first, items, mode) in enumerate(proposals, 1))


def render_markdown(results: tuple[SubAgentResult, ...], proposals: tuple[Proposal, ...]) -> str:
    lines = ["# Competitive Research Agent Report", "", "## Governance", "", "- Proprietary games are behavioral references only; production code is original.", "- Public repositories remain reference-only until a compatible license is verified.", "- Any approved reuse must retain attribution and license notices.", "", "## Subagents", ""]
    lines += [f"- **{r.name}** — {r.mission} ({len(r.evidence)} findings)" for r in results]
    lines += ["", "## Ranked backlog", "", "| Rank | Feature | Score | Phase | References | Implementation |", "|---:|---|---:|---|---|---|"]
    for p in proposals:
        lines.append(f"| {p.rank} | {p.feature} | {p.score} | {p.phase} | {', '.join(p.references)} | {p.implementation_mode} |")
    lines += ["", "## Original implementation specifications", ""]
    for p in proposals:
        lines += [f"### {p.rank}. {p.feature}", "", p.original_design, "", f"**Dependencies:** {', '.join(p.dependencies) or 'None'}", "", f"**Evidence:** {', '.join(p.evidence_ids)}", ""]
    lines += ["## Code-source review", "", "| Source | License | Disposition |", "|---|---|---|"]
    seen = set()
    for r in results:
        for e in r.evidence:
            if e.source_id not in seen:
                seen.add(e.source_id)
                lines.append(f"| [{e.source}]({e.url}) | {e.license_id or 'not verified / not applicable'} | {e.disposition} |")
    return "\n".join(lines) + "\n"


def run_and_write(output: Path, backlog: Path, request: str) -> tuple[SubAgentResult, ...]:
    agent = CompetitiveResearchAgent()
    results = agent.run(request)
    proposals = agent.synthesize(results)
    output.parent.mkdir(parents=True, exist_ok=True)
    backlog.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(results, proposals), encoding="utf-8")
    backlog.write_text(json.dumps({"as_of": "2026-07-11", "subagents": [{"name": r.name, "mission": r.mission, "findings": len(r.evidence)} for r in results], "features": [asdict(p) for p in proposals]}, indent=2) + "\n", encoding="utf-8")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run competitive hockey-GM research subagents.")
    parser.add_argument("--output", type=Path, default=Path("docs/competitive_research_report.md"))
    parser.add_argument("--backlog", type=Path, default=Path("research/competitive_backlog.json"))
    parser.add_argument("--request", default="Research observable mechanics and write original specifications.")
    args = parser.parse_args()
    results = run_and_write(args.output, args.backlog, args.request)
    print(f"Ran {len(results)} subagents and wrote {args.output} and {args.backlog}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
