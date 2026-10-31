# How a FrontierCS 2 task is built and checked

A practitioner's reading of the released tasks. Every step cites where it comes from: the paper (arXiv:2610.29932v1), the task repo at `FrontierCS/FrontierCS-2@0de64ff8`, or the FrontierCS blog. Paths below are under `tasks/frontier-cs-2.0-demo/problems/`. Counts over all 48 tasks are computed by `fcs2audit/tasks.py`.

## The idea in one line

Take a published paper's own code, delete the paper's contribution, and ask an agent to write it back so it **beats the authors' code** on every metric and every hidden workload (paper, Sections 1 and 3).

## 1. Pin the source

Record the exact upstream commit and license, and hash every file of the task.

- `Theory/binary_fuse_filter/README.md`: source pin `FastFilter/xor_singleheader@3e10fb18…`, Apache-2.0.
- `upstream.lock.json` (a hash of every file in the task) exists in **48 of 48** tasks; images are pinned by digest (repo `README.md`).

## 2. Delete the contribution, and only the contribution

Remove the code that implements the paper's idea; leave everything it depends on, and keep the deleted functions declared and called (paper, Section 3).

## 3. Keep the deleted code as the private reference

The deleted code becomes `judge/reference.patch`, held by the judge and never copied into the agent's image (paper, Section 3; `binary_fuse_filter/README.md`). Present in **45 of 48** tasks (the rest use a reference program or, for Structured LWE, published instances).

## 4. Fix the patch surface

Say exactly what the agent may edit.

- `binary_fuse_filter/judge/config.yaml`: `allow_paths: [include/]`, at most 32 changed files, at most 524,288 patch bytes.
- `Database/bounded_evm_path_prediction` (Seer) statement: exactly one changed file, a five-package import allowlist, and no OS, network, `unsafe`, or judge/environment inspection.
- A separate patch-surface checker (`judge/submission_patch.py`) exists in **40 of 48** tasks.

## 5. Write the pass rule as a contract (the "beat spec")

`judge/beat_spec.json` exists in **48 of 48** tasks. For each metric it states the better direction, the exact rule, the tolerance, the code that measures it, and what it means. Binary Fuse Filter, for example, requires strictly fewer resident bytes and faster build and lookup than the reference on every workload.

## 6. Prove the rule can be passed

Binary Fuse Filter's own README records that an earlier rule was **impossible to pass**: at 16-bit fingerprints, its accuracy requirement plus strictly fewer bytes was below the information-theoretic minimum on at least 24 of the 144 final workloads. It was replaced (revision r8) by a certified non-inferiority rule for the two accuracy metrics.

## 7. Pre-register tolerances for noisy metrics

For noisy accuracy metrics, Binary Fuse Filter sets per-workload anchors from reference-only measurements (5 rounds, 900 constructions; `judge/statistical_calibration.json`). Its beat spec says the anchors were fixed before any solver result and never tuned to submissions.

## 8. Run the reference against itself

Binary Fuse Filter's runtime receipt (`judge/reference/runtime-qualification.json`) runs the reference as if it were a candidate. Against itself it "wins" build time on 56 of 144 final workloads, lookup time on 70, resident bytes on 0 (exact ties), and passes both accuracy guards on all 144. The receipt's verdict: a valid reference, with a strict FAIL on the paired performance ties, as expected for a comparison against itself. The point: equal code cannot pass a strict-improvement rule, so a pass needs a real margin.

## 9. Check that measurement is repeatable

The Seer statement reports that repeated fixed replays of an unchanged implementation gave identical parsed scores, so no run-to-run score noise was measured on that task.

## 10. Hold out what is graded

- Seer: development scores blocks 14,650,001–14,650,200; the final check also grades two held-out 200-block epochs.
- Progent: about 40% of each suite's user tasks are held out, and each evaluation draws new attacker identities.
- Paper, Section 3: held-out instances are different seeds, queries or input graphs.

## 11. Seal the judge

The agent's sandbox reaches no network except a driver; the judge keeps the evaluator, the held-out suite and the reference; each submission returns only a development score and per-metric pass counts (paper, Section 4, Figure 4). On GPU tasks, baseline and patch are measured serially on the same GPU class (blog, "Roadmap to FrontierCS 2").

## 12. Qualify the real runtime, and fail closed

Binary Fuse Filter's production evaluation refuses to run until the reference has been re-measured inside the exact immutable production image (`binary_fuse_filter/README.md`; receipt status `QUALIFIED_EXACT_RUNTIME`). Such receipts exist in 3 tasks.

## 13. Close loopholes in writing, then review passing runs

- Progent's statement: policies must follow from the user's request, not from a list of known attacker strings.
- After evaluation, the authors reviewed the final patch and trace of all 26 passing Gemini 4 Carbon runs with Harbor's reward-hack categories (tampering, cheating, loopholes) and found 3 loopholes (blog, "Details about our evaluation of Gemini 4 Carbon").

## What the released runs show

See [`results/FINDINGS.md`](../results/FINDINGS.md) (generated) and [`VERIFICATION.md`](VERIFICATION.md). In short:

- The release reproduces the paper's pass rates and its 16 never-passed tasks exactly.
- 242 of the 379 runs that out-score the reference still fail (paper's 12 agents).
- 57 of 401 graded failures missed exactly one hidden metric-workload check.
- Only two runs pass Progent, and both final patches detect AgentDojo's attack by its known text, which step 13's rule excludes. The authors flagged one (Carbon); the other (Gemini 4 Argon in Antigravity) is a plain PASS in the release.
