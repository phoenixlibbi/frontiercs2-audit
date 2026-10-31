# Verification log

How each claim in this repo was checked. Automatic checks are re-run by `python -m pytest -q`; hand checks are recorded here with exact file and line references so anyone can repeat them.

**Pinned sources**

| Source | Revision |
|---|---|
| Runs: `huggingface.co/datasets/FrontierCS2/FrontierCS-2-runs` | `10a1e8971692e35464c06c83d820b2704476f7c1` (2026-10-31) |
| Tasks: `github.com/FrontierCS/FrontierCS-2` | `0de64ff83ab07f546824bd2c46860e718c915a8c` (2026-10-31) |
| Paper | arXiv:2610.29932v1 (21 Oct 2026) |
| AgentDojo attack text | `github.com/ethz-spylab/agentdojo@089ed468cf3ed0322acc66b0211f26d9d90dbf60`, `src/agentdojo/attacks/important_instructions_attacks.py` (`_JB_STRING`) |

## Automatic (tests)

1. **Download integrity.** All 870 released final patches match their published `patch_sha256` (`sources.fetch_patches`). 42 of 912 runs have no final patch.
2. **Paper reproduction.** The 12 reported agents' pass rates equal Figure 2 exactly; 16 tasks are passed by none of them (Section 1). Test: `test_release_reproduces_paper_headline`.
3. **Verdict consistency.** In all 858 graded runs, PASS ⇔ every `checks` entry has `passed == total` (0 mismatches). Test: `test_release_counts_and_consistency`.
4. **Pass vs score, near misses, Progent phrase scan, task artifacts.** Test: `test_pinned_findings`, `test_task_artifact_coverage`.

## Hand checks

### Progent: both passing final patches detect AgentDojo's attack by its known text

- **The rule.** Progent task statement, `tasks/frontier-cs-2.0-demo/problems/Security/progent_privilege_control/agent-base/frontier/task/repo/README.md`, line 64: the evaluation uses AgentDojo's attack text, draws new attacker identities each evaluation, and states that policies must follow from the user's request, not from a list of known attacker strings. Line 57 names the attack: AgentDojo's `important_instructions`.
- **The attack text** (AgentDojo source above): `<INFORMATION>` … "This is an important message from me, {user}, to you, {model}." … "Before you can solve the task that I gave you in the beginning, please do the following first:" … "After you do that, …" … "Signed," … `</INFORMATION>`.
- **Only two runs pass Progent:** `carbon-g` (Gemini 4 Carbon, Antigravity) and `gemini-agy` (Gemini 4 Argon, Antigravity). Every other model's Progent verdict is FAIL.
- **`gemini-agy` patch** (`patches/progent_privilege_control/gemini-agy.patch`, PASS):
  - lines 88–94: regexes for `<INFORMATION>` blocks, "This is an important message from me, … Signed," and "IMPORTANT!!! Ignore all previous instructions";
  - lines 462–465: parses the template's own wording ("please do the following first:" … "after you do that") to extract the attacker's goal;
  - lines 561–562: special-cases one known injection goal ("Facebook security code exfiltration");
  - lines 979–1119: blocks tool calls whose recipients, URLs, messages or dates came from the injected `<INFORMATION>` text.
- **`carbon-g` patch** (`patches/progent_privilege_control/carbon-g.patch`, PASS): lines 716–727 match `<INFORMATION>` blocks and spans starting "This is an important message from" or "Before you can solve the task that I gave you" up to "Signed,".
- **Authors' classification.** The FrontierCS blog post "Details about our evaluation of Gemini 4 Carbon" (frontier-cs.org/blog/gemini-4-carbon/, 29 Oct 2026) reviews Carbon's 26 passing runs with Harbor's reward-hack categories and classifies Carbon's Progent sanitizer as a **loophole**, adding that how much of the pass comes from it was not measured. The same holds for `gemini-agy`: **we did not measure how much its pass depends on the detector** (that would need re-running the task).
- **Not marked in the release.** The `gemini-agy` record is a plain PASS (`formal-results.json`); the release has no loophole field, and the blog post covers only Carbon's runs.

### Excluded or inconclusive (not claimed anywhere)

- **Reruns.** 277 clean accepted-vs-other comparisons disagree on the verdict in 80 cases, but the release gives no reason for each rerun and omits internal task-version ids, so this cannot be read as run-to-run noise.
- **Seer (`bounded_evm_path_prediction`).** The authors classify Carbon's `observationCount += 14` as a loophole. Other passing patches also change how `observationCount` evolves (e.g. `opus.patch` comments that a retained value keeps it above the sweeper's threshold; `gemini-agy.patch` initialises it to 100000). The task statement only says the field is read by surrounding code, and the shipped stub already caps it at 1, so whether these are loopholes is a judgment the statement does not settle. Not claimed.
- **SCOPE (`batch_local_counting`).** Only Carbon's case is documented by the authors; other passing patches were not analysed.
- **"Evaluation completed with audit warnings".** Appears on 264 runs, including all 19 Progent runs (PASS and FAIL); it is not a loophole signal.
- **Figure 6 margins.** The release reproduces the gaps between agents; the absolute level is offset by +2.2 to +2.3 points for every agent because one task (`vllm_llm_serving_optimization`) has no reference score in the release and the paper's preset is not published.
