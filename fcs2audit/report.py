"""Recompute every finding from the pinned release and write results/.

    python -m fcs2audit.report          # downloads once into data/, then writes results/
"""
from __future__ import annotations

import json
import sys

from . import analysis as A
from . import sources as S

FIG6 = {"opus": 9.4, "astra": 7.1, "sol": 5.7, "gemini": 2.1, "glm": 1.8, "wonder": 4.1,
        "ds": 0.5, "k3": -1.2, "glmf": -8.4, "muse": -3.3, "qwen": -6.4, "step": -10.6}


def build() -> dict:
    results = S.load_results()
    S.fetch_patches()
    paper = set(A.PAPER_AGENTS)
    return {
        "sources": {"hf_dataset": S.HF_DATASET, "hf_revision": S.HF_REVISION,
                    "github_repo": S.GH_REPO, "github_revision": S.GH_REVISION, "paper": S.PAPER},
        "counts": {"runs": len(results["runs"]), "models": len(results["models"]),
                   "tasks": len(results["tasks"]),
                   "patches": sum(1 for r in results["runs"] if r.get("patch_path"))},
        "reproduce": A.reproduce(results),
        "margin_offsets": A.margin_offsets(results, FIG6),
        "consistency": A.consistency(results),
        "pass_vs_score_paper12": A.pass_vs_score(results, paper),
        "pass_vs_score_all": A.pass_vs_score(results),
        "near_misses_paper12": A.near_misses(results, paper),
        "near_misses_all": A.near_misses(results),
        "progent_attack_text": A.progent_attack_text(results, S.patch_text),
        "reruns": A.reruns(results),
    }


def markdown(f: dict) -> str:
    rp, ps, nm = f["reproduce"], f["pass_vs_score_paper12"], f["near_misses_paper12"]
    mo, cs, pg, rr = f["margin_offsets"], f["consistency"], f["progent_attack_text"], f["reruns"]
    s = f["sources"]
    lines = [
        "# Findings (generated)", "",
        f"Computed by `python -m fcs2audit.report` from `{s['hf_dataset']}@{s['hf_revision'][:8]}` "
        f"and `{s['github_repo']}@{s['github_revision'][:8]}`. "
        f"{f['counts']['runs']} runs, {f['counts']['models']} models, {f['counts']['tasks']} tasks, "
        f"{f['counts']['patches']} final patches (each checked against its published sha256).", "",
        "## 1. The release reproduces the paper", "",
        "| Agent | Passes | Pass rate | Paper |", "|---|---|---|---|",
        *[f"| {m} | {a['passes']}/{a['runs']} | {a['pass_pct']}% | {a['paper_pct']}% |"
          for m, a in rp["agents"].items()],
        "", f"Tasks no reported agent passes: **{len(rp['never_passed'])}** (paper: 16). "
            f"All match: **{rp['all_match']}**.", "",
        f"Mean margins (Figure 6) differ from the release by a near-constant offset "
        f"({mo['offset_min']:+.2f} to {mo['offset_max']:+.2f}) for every agent, so the gaps between "
        f"agents reproduce; the absolute level depends on reference values not in the release "
        f"(no reference score recorded for: {', '.join(mo['tasks_without_reference'])}).", "",
        "## 2. Verdicts agree with the per-metric checks", "",
        f"In all {cs['graded_runs']} graded runs, PASS holds exactly when every hidden check is met "
        f"({len(cs['mismatches'])} mismatches).", "",
        "## 3. A higher score is not a pass (paper's 12 agents)", "",
        f"{ps['above_but_fail']} of the {ps['runs_above_reference']} runs whose final score is above "
        f"the reference's still FAIL. {len(ps['pass_at_or_below_reference'])} runs PASS with a score at "
        f"or below the reference: {', '.join(ps['pass_at_or_below_reference'])}.", "",
        "## 4. One check decides many failures (paper's 12 agents)", "",
        f"{nm['one_miss']} of {nm['graded_fails']} graded failures missed exactly one hidden "
        f"(metric, workload) check. Missed metrics: "
        + ", ".join(f"{k} {v}" for k, v in nm["missed_metric"].items()) + ".", "",
        "Sensitivity only (not a proposed rule): passes if one missed check were allowed.", "",
        "| Agent | Passes | + one-miss fails |", "|---|---|---|",
        *[f"| {m} | {a['passes']} | {a['passes'] + a['one_miss_fails']} |"
          for m, a in nm["per_agent"].items()],
        "", "## 5. Progent: both passing patches detect the attack by its known text", "",
        f"Task rule (Progent README): \"{pg['rule']}\"", "",
        f"Passing runs: {', '.join(pg['passing'])}. Passing patches matching 3+ AgentDojo "
        f"`important_instructions` phrases: {', '.join(pg['passing_with_markers'])}.", "",
        "| Model | Verdict | AgentDojo phrases in added lines |", "|---|---|---|",
        *[f"| {x['model']} | {x['verdict']} | "
          + (", ".join(f"{k} ({v})" for k, v in x["markers"].items()) or "none") + " |"
          for x in pg["runs"]],
        "", "A phrase mention alone is not proof of a detector; the two passing patches were read "
            "by hand (see docs/VERIFICATION.md).", "",
        "## 6. Reruns (not a finding)", "",
        f"`other_runs` holds {rr['other_runs']} non-accepted runs ({rr['graded_other_runs']} graded). "
        f"On {rr['clean_comparisons']} clean comparisons the verdict pairs (accepted/other) are "
        + ", ".join(f"{k} {v}" for k, v in rr["verdict_pairs"].items()) + ". " + rr["note"], "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    f = build()
    out = S.ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "findings.json").write_text(json.dumps(f, indent=1) + "\n")
    (out / "FINDINGS.md").write_text(markdown(f))
    print(f"wrote {out / 'findings.json'} and {out / 'FINDINGS.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
