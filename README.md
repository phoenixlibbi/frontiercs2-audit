# fcs2audit

Model-free checks on the released runs of **FrontierCS 2** ([paper](https://arxiv.org/abs/2610.29932), [tasks](https://github.com/FrontierCS/FrontierCS-2), [runs](https://huggingface.co/datasets/FrontierCS2/FrontierCS-2-runs)).

No model or task is run. Every number is computed from the authors' own release, pinned to exact revisions in [`fcs2audit/sources.py`](fcs2audit/sources.py), and every downloaded patch is checked against its published sha256.

```bash
python -m pytest -q              # unit tests + pinned-release tests (downloads ~26 MB once)
python -m fcs2audit.report       # writes results/findings.json and results/FINDINGS.md
```

Current results: [`results/FINDINGS.md`](results/FINDINGS.md).

*Work in progress: the write-up and the task-building guide are being added.*

## License

Code: MIT. The FrontierCS 2 runs, patches and task files are © their authors under CC BY 4.0; this repo downloads them and does not redistribute them.
