# Competitive Research Agent

Run five bounded subagents to compare hockey-management simulations and turn observable strengths into an original implementation backlog:

```bash
python -m src.competitive_research_agent
```

Outputs:

- `docs/competitive_research_report.md` — human-readable comparison and specifications.
- `research/competitive_backlog.json` — ranked machine-readable features for future engineering agents.

Subagents cover HLM 26, EA NHL Franchise, deeper PC simulations (FHM/EHM), open-source license review, and real-world hockey-operations research. The synthesis score weights realism, player value, feasibility, differentiation, and training value.

## Clean-room policy

Proprietary games are behavioral references only. The agent does not decompile executables, extract assets, or copy proprietary code. Public repositories are reference-only until an explicit compatible license is verified; approved reuse must preserve attribution and license notices.

Run validation with:

```bash
python -m unittest tests.test_competitive_research_agent -v
```
