# NHL Front-Office Training Simulation Blueprint

## Product Goal

Build a realistic management simulation that trains the user to operate an NHL hockey-operations department, not merely assemble a high-rated roster. The user should be evaluated on process, legal compliance, judgment under uncertainty, communication, organizational alignment and long-term consequences.

## What the Game Must Simulate

### 1. The General Manager as an Executive

The GM is accountable for a multi-year competitive plan, ownership expectations, hockey-operations staffing, roster construction, contracts, cap flexibility, draft capital and organizational reputation. Every major decision should require a written or selected rationale and should alter future information, relationships and job security.

### 2. A Real Front Office, Not a Single Omniscient Player

Information should arrive through staff roles with different expertise, bias, confidence and incentives:

- President of Hockey Operations
- General Manager
- Assistant General Manager
- Director of Hockey Administration / Cap and Contracts
- Director of Pro Scouting
- Director of Amateur Scouting
- Director of Player Development
- Analytics and Strategy staff
- AHL general manager and coaches
- Medical and performance staff
- Legal, communications and ownership stakeholders

The user receives recommendations but remains responsible for resolving conflicts and authorizing decisions.

### 3. Auditable Rules and Evidence

Every CBA or league-rule mechanic must store:

- source title and URL
- effective date or season
- rule version
- game implementation note
- automated test reference

Rules must never be embedded only as unexplained constants. The 186-day and salary-cap assumptions currently in the prototype should become season configuration, because league calendars, caps and labor rules change.

## Core Operating Cadence

### Daily

- Review roster legality, cap position and transaction status.
- Process injuries, recalls, assignments and waivers.
- Review scouting and player-development updates.
- Respond to trade calls, agent messages and league notices.
- Approve lineup-impacting actions with coaching staff.

### Weekly

- Conduct a hockey-operations meeting.
- Review performance versus underlying metrics.
- Update organizational depth chart and player plans.
- Reassess standings, playoff odds and competitive posture.
- Brief ownership on material deviations and risks.

### Seasonal Milestones

- Training camp and final roster decisions
- Opening-day cap submission
- Contract-extension windows
- Trade deadline preparation and execution
- Exit interviews and staff evaluations
- Draft lottery, combine, interviews and draft table
- Qualifying offers, arbitration and buyout windows
- Free agency and contract registration
- Development camp and affiliate planning

## Required Decision Model

Every consequential scenario should contain:

1. **Trigger** — why the issue exists now.
2. **Deadline** — when a decision must be registered.
3. **Information packet** — reports available to the GM.
4. **Uncertainty** — information that is incomplete, biased or hidden.
5. **Options** — legal and illegal alternatives.
6. **Consultation** — staff members who may be asked for advice.
7. **Authorization** — ownership, league or player approval when required.
8. **Execution** — transaction or organizational action.
9. **Communication** — internal, player, agent, media and ownership messaging.
10. **Consequences** — immediate, seasonal and multi-year effects.
11. **After-action review** — evaluation of process separately from outcome.

## Training Scoring

A move that works statistically can still be a poor management decision. Score the user across six dimensions:

- **Compliance:** Was the action legal and correctly registered?
- **Decision process:** Were relevant sources and staff consulted?
- **Asset management:** Was the price consistent with alternatives and the competitive window?
- **Risk management:** Were medical, contract, development and downside risks understood?
- **Leadership:** Were conflicts and stakeholder expectations managed effectively?
- **Outcome quality:** Did the decision improve the organization over the relevant horizon?

Random outcomes must not erase process quality. A sound decision with an unlucky result should be graded differently from an undisciplined gamble that happens to succeed.

## Agent Architecture

`src/front_office_research_agent.py` provides the first schema for:

- source records and evidence tiers
- front-office duties
- operating cadence
- required capabilities
- training objectives
- scenario requirements
- feature-gap reports

The next iteration should add adapters that periodically review authoritative sources and produce a human-reviewed rules-change proposal. No sourced rule should automatically alter live game logic without review and regression tests.

## Recommended Engineering Sequence

### Phase A — Rules Registry and Organization Model

1. Convert cap ceiling, season length and roster rules into versioned season configuration.
2. Add front-office roles, staff attributes, reporting lines and permissions.
3. Add a rules registry with source provenance.
4. Add transaction submission and Central Registry validation states.

### Phase B — Daily Office Workflow

1. Create an inbox and deadline queue.
2. Add staff reports with confidence and bias.
3. Add meeting and consultation actions.
4. Add decision memoranda and after-action scoring.

### Phase C — Transaction Realism

1. Complete waivers, reserve lists, recalls and assignments.
2. Add contract clauses, retention, conditions and draft-pick encumbrances.
3. Add agent negotiation and player-interest logic.
4. Add medical review and ownership authorization gates.

### Phase D — Full Annual Hockey-Operations Cycle

1. Training camp and opening roster.
2. In-season management and deadline room.
3. Exit interviews and organizational review.
4. Draft, rights management, arbitration, buyouts and free agency.
5. Development camp, AHL planning and next-season budgeting.

### Phase E — Training Validation

1. Build expert-authored benchmark scenarios.
2. Compare user actions with defensible decision ranges, not one predetermined answer.
3. Add explainable scoring and debrief reports.
4. Test scenarios with hockey operations, cap, scouting and sports-management practitioners.

## Initial Acceptance Criteria

The game reaches its first training-grade milestone when a user can complete one full league year and must:

- submit a legal opening roster;
- manage injuries, waivers, recalls and daily cap;
- run weekly front-office meetings;
- make and document trade decisions;
- manage the deadline under a clock;
- conduct staff and player exit reviews;
- run a draft room;
- complete qualifying offers and free agency;
- receive a process-based executive evaluation and retain or lose the GM job.

## Important Limitation

This project can train structured hockey-operations judgment, rule application and decision discipline. It should not claim to confer official NHL certification or reproduce confidential team methods. Public rules and public role evidence should remain clearly separated from game-design assumptions.