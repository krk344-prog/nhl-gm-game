"""Research and curriculum agent for the NHL GM simulation.

The agent converts authoritative hockey-operations research into:
1. a front-office duty model,
2. scenario requirements,
3. feature-gap priorities, and
4. training-grade evaluation criteria.

It intentionally separates sourced rules from game-design assumptions so the
simulation can be audited as NHL rules and operating practices change.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
import json
from typing import Iterable


class EvidenceTier(str, Enum):
    PRIMARY = "primary"
    TEAM_SOURCE = "team_source"
    SECONDARY = "secondary"
    DESIGN_ASSUMPTION = "design_assumption"


class Cadence(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SEASONAL = "seasonal"
    EVENT_DRIVEN = "event_driven"
    MULTI_YEAR = "multi_year"


@dataclass(frozen=True)
class SourceRecord:
    title: str
    url: str
    tier: EvidenceTier
    effective_date: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class Duty:
    key: str
    owner_role: str
    description: str
    cadence: Cadence
    decisions: tuple[str, ...]
    dependencies: tuple[str, ...]
    consequences: tuple[str, ...]
    evidence: tuple[str, ...]
    training_objective: str


@dataclass(frozen=True)
class ScenarioRequirement:
    key: str
    title: str
    trigger: str
    available_information: tuple[str, ...]
    hidden_information: tuple[str, ...]
    required_actions: tuple[str, ...]
    scoring_dimensions: tuple[str, ...]
    downstream_effects: tuple[str, ...]


@dataclass
class ResearchSnapshot:
    version: str
    sources: list[SourceRecord] = field(default_factory=list)
    duties: list[Duty] = field(default_factory=list)
    scenarios: list[ScenarioRequirement] = field(default_factory=list)

    def validate(self) -> None:
        source_titles = {source.title for source in self.sources}
        duplicate_keys = _duplicates([duty.key for duty in self.duties])
        duplicate_keys |= _duplicates([scenario.key for scenario in self.scenarios])
        if duplicate_keys:
            raise ValueError(f"Duplicate keys: {sorted(duplicate_keys)}")

        for duty in self.duties:
            missing = set(duty.evidence) - source_titles
            if missing:
                raise ValueError(f"Duty {duty.key} references unknown sources: {missing}")

    def duty_matrix(self) -> list[dict[str, object]]:
        return [asdict(duty) for duty in self.duties]

    def training_backlog(self, implemented_capabilities: Iterable[str]) -> list[dict[str, object]]:
        implemented = set(implemented_capabilities)
        backlog: list[dict[str, object]] = []
        for duty in self.duties:
            missing = sorted(set(duty.dependencies) - implemented)
            if missing:
                backlog.append(
                    {
                        "duty": duty.key,
                        "owner_role": duty.owner_role,
                        "missing_capabilities": missing,
                        "training_objective": duty.training_objective,
                    }
                )
        return backlog

    def export(self, output_path: str | Path) -> None:
        self.validate()
        payload = {
            "version": self.version,
            "sources": [asdict(source) for source in self.sources],
            "duties": [asdict(duty) for duty in self.duties],
            "scenarios": [asdict(scenario) for scenario in self.scenarios],
        }
        Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def build_baseline_snapshot() -> ResearchSnapshot:
    """Return the first auditable front-office operating model."""
    sources = [
        SourceRecord(
            title="NHL-NHLPA Collective Bargaining Agreement",
            url="https://www.nhl.com/info/collective-bargaining-agreement",
            tier=EvidenceTier.PRIMARY,
            notes="Authoritative source for contracts, reserve lists, waivers, arbitration, cap accounting and player movement.",
        ),
        SourceRecord(
            title="NHL Central Registry and Hockey Operations rules",
            url="https://www.nhl.com/info/hockey-operations-guidelines",
            tier=EvidenceTier.PRIMARY,
            notes="Use for transaction deadlines, roster registration and league approvals when published.",
        ),
        SourceRecord(
            title="NHL club hockey-operations staff directories",
            url="https://www.nhl.com/info/teams",
            tier=EvidenceTier.TEAM_SOURCE,
            notes="Role taxonomy evidence across president, GM, assistant GM, scouting, development, analytics and cap staff.",
        ),
    ]

    duties = [
        Duty(
            key="organizational_strategy",
            owner_role="President of Hockey Operations / General Manager",
            description="Set the competitive window, roster identity, asset-allocation policy and ownership-facing plan.",
            cadence=Cadence.MULTI_YEAR,
            decisions=("contend, retool or rebuild", "budget allocation", "risk tolerance", "management staffing"),
            dependencies=("ownership_mandates", "multi_year_forecast", "asset_valuation", "job_security"),
            consequences=("organizational alignment", "future flexibility", "ownership confidence", "fan expectations"),
            evidence=("NHL club hockey-operations staff directories",),
            training_objective="Defend a coherent multi-year plan while balancing wins, prospect capital, cash and cap flexibility.",
        ),
        Duty(
            key="roster_and_cap_management",
            owner_role="General Manager / Assistant GM / Cap and Contracts Staff",
            description="Maintain a legal roster and optimize daily cap, reserve-list, waiver and contract status.",
            cadence=Cadence.DAILY,
            decisions=("recalls and assignments", "waivers", "IR or LTIR placement", "contract registration", "cap-space accrual"),
            dependencies=("daily_cap_ledger", "waiver_engine", "reserve_lists", "injury_designations", "central_registry_gate"),
            consequences=("transaction approval", "lost players", "cap penalties", "deadline buying power"),
            evidence=("NHL-NHLPA Collective Bargaining Agreement", "NHL Central Registry and Hockey Operations rules"),
            training_objective="Complete legal transactions under time pressure without creating hidden cap or roster violations.",
        ),
        Duty(
            key="player_acquisition",
            owner_role="General Manager / Pro Scouting / Analytics",
            description="Acquire NHL players through trades, waivers and free agency using integrated evaluation and negotiation.",
            cadence=Cadence.EVENT_DRIVEN,
            decisions=("target identification", "trade package", "retention", "conditions", "contract offer", "no-trade handling"),
            dependencies=("pro_scouting", "trade_market", "negotiation_ai", "contract_clauses", "medical_risk"),
            consequences=("roster quality", "draft capital", "cap efficiency", "league relationships"),
            evidence=("NHL-NHLPA Collective Bargaining Agreement", "NHL club hockey-operations staff directories"),
            training_objective="Synthesize scouting, analytics, medical, contract and market information into defensible acquisitions.",
        ),
        Duty(
            key="amateur_draft_pipeline",
            owner_role="General Manager / Director of Amateur Scouting",
            description="Manage draft philosophy, scouting coverage, interviews, rankings, pick trades and selection decisions.",
            cadence=Cadence.SEASONAL,
            decisions=("scouting assignments", "final list", "pick trade", "selection", "rights strategy"),
            dependencies=("draft_rules", "amateur_scouting", "combine_interviews", "prospect_uncertainty", "pick_valuation"),
            consequences=("prospect pool", "development load", "future surplus value", "scouting accountability"),
            evidence=("NHL-NHLPA Collective Bargaining Agreement", "NHL club hockey-operations staff directories"),
            training_objective="Run an evidence-based draft room where uncertainty, organizational need and long-term value remain distinct.",
        ),
        Duty(
            key="player_development",
            owner_role="Assistant GM / Director of Player Development / AHL Management",
            description="Coordinate development plans, affiliate assignments, coaching feedback and progression checkpoints.",
            cadence=Cadence.WEEKLY,
            decisions=("league assignment", "role and minutes", "development intervention", "recall readiness"),
            dependencies=("ahl_affiliate", "development_plans", "coach_feedback", "progression_model"),
            consequences=("prospect outcomes", "depth readiness", "organizational trust", "asset value"),
            evidence=("NHL club hockey-operations staff directories",),
            training_objective="Make development decisions that optimize long-term outcomes rather than short-term ratings gains.",
        ),
        Duty(
            key="coaching_and_performance_management",
            owner_role="General Manager / Head Coach / Performance Staff",
            description="Hire and evaluate coaches, align systems with roster construction and resolve performance breakdowns.",
            cadence=Cadence.WEEKLY,
            decisions=("coach hiring", "system alignment", "staff changes", "player-coach conflict", "performance intervention"),
            dependencies=("coaching_market", "system_fit", "locker_room", "performance_diagnostics"),
            consequences=("team results", "player morale", "development", "management credibility"),
            evidence=("NHL club hockey-operations staff directories",),
            training_objective="Diagnose whether poor results originate in talent, tactics, deployment, health or leadership before acting.",
        ),
        Duty(
            key="stakeholder_and_crisis_management",
            owner_role="President / General Manager / Communications / Ownership",
            description="Manage ownership, media, agents, players and internal executives during sensitive decisions and crises.",
            cadence=Cadence.EVENT_DRIVEN,
            decisions=("message strategy", "discipline", "confidentiality", "escalation", "ownership recommendation"),
            dependencies=("media_system", "agent_relationships", "ownership_mandates", "morale", "ethics_and_compliance"),
            consequences=("trust", "reputation", "job security", "negotiating leverage", "locker-room stability"),
            evidence=("NHL club hockey-operations staff directories",),
            training_objective="Communicate accurate, controlled and ethical decisions while preserving organizational leverage.",
        ),
    ]

    scenarios = [
        ScenarioRequirement(
            key="deadline_trade_room",
            title="Trade Deadline War Room",
            trigger="Six hours remain before the deadline; the club is in a playoff position with limited accrued cap room.",
            available_information=("pro scouting reports", "analytics model", "cap ledger", "medical summary", "asking prices"),
            hidden_information=("rival fallback offers", "ownership patience", "player injury recurrence risk"),
            required_actions=("set target hierarchy", "authorize walk-away prices", "validate cap and roster", "submit transaction", "brief stakeholders"),
            scoring_dimensions=("competitive value", "cap legality", "asset discipline", "process quality", "communication"),
            downstream_effects=("playoff odds", "future draft capital", "GM relationships", "ownership confidence"),
        ),
        ScenarioRequirement(
            key="waiver_injury_crisis",
            title="Injury and Waiver Compliance Crisis",
            trigger="A player is injured before a back-to-back while the roster and cap are both constrained.",
            available_information=("medical estimate", "waiver eligibility", "AHL roster", "daily cap position"),
            hidden_information=("recovery setback", "waiver claim probability"),
            required_actions=("choose designation", "select recall", "evaluate waiver exposure", "register legal roster"),
            scoring_dimensions=("legality", "risk management", "competitive readiness", "future flexibility"),
            downstream_effects=("player availability", "waiver loss", "cap accrual", "team performance"),
        ),
        ScenarioRequirement(
            key="draft_table_conflict",
            title="Draft Table Decision Conflict",
            trigger="Scouting and analytics disagree on two prospects while another club offers a trade-down package.",
            available_information=("scout grades", "model projections", "interviews", "medical flags", "trade offer"),
            hidden_information=("other teams' lists", "true development curve"),
            required_actions=("surface assumptions", "price uncertainty", "make selection or trade", "document rationale"),
            scoring_dimensions=("decision quality", "uncertainty handling", "organizational alignment", "asset value"),
            downstream_effects=("prospect pipeline", "staff confidence", "future roster construction"),
        ),
    ]

    return ResearchSnapshot(version="0.1.0", sources=sources, duties=duties, scenarios=scenarios)


if __name__ == "__main__":
    snapshot = build_baseline_snapshot()
    snapshot.export("front_office_research_snapshot.json")
    print(f"Exported {len(snapshot.duties)} duties and {len(snapshot.scenarios)} scenarios.")
