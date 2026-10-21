# How to Run the Backend Scripts

All commands are run **from the repository root**.

## One-time setup
```bash
pip install -r backend/requirements.txt
```
Use Python 3.11 or newer.

## 1. Week 1 scripts (the team's `data/customers.csv`)
```bash
python backend/causal_dag.py       # causal graph, identified estimand, naive vs adjusted effect
python backend/baseline_model.py   # predictive baseline model
```
`causal_dag.py` saves a DAG picture only if Graphviz is installed, and otherwise just prints a note.

## 2. Create the richer dataset
```bash
python backend/generate_causal_data.py
```
Writes `data/customers_causal.csv` (5,000 customers, a $0/$10/$20 discount level, and the true effects for validation). It does **not** overwrite the team's `customers.csv`.

## 3. Week 2 scripts (need `data/customers_causal.csv`)
| Command | What it does | Time |
|---|---|---|
| `python backend/casual_model.py` | Double ML (ours and EconML) vs a predictive baseline | about 30 s |
| `python backend/propensity.py` | Propensity matching, balance table, two figures in `backend/figures/` | about 1 min |
| `python backend/refutation.py` | DoWhy and Double ML refutation tests | about 40 s |
| `python backend/export_sample_json.py` | Writes `docs/sample_ite.json` and `docs/sample_uplift_curve.json` for the frontend | about 30 s |

## 4. Week 3 script
```bash
python backend/optimizer.py --export
```
Allocates a $5,000 budget (change it with `--budget`) and writes `docs/sample_optimize.json`. Add `--point-estimate` to optimise point estimates instead of the cautious lower bound.

## Where things are
| Folder | Contents |
|---|---|
| `backend/` | Scripts, `requirements.txt`, figures |
| `data/` | `customers.csv` (team data), `customers_causal.csv` (generated) |
| `docs/` | Reports, notes, sample JSON, API contract |

## Troubleshooting
- **`FileNotFoundError: data/customers_causal.csv`:** run step 2 first.
- **Import errors:** run `pip install -r backend/requirements.txt` again.
- **Run commands from the repo root.** The scripts find the data folder relative to their own location, but the paths above assume the root.
- **Results differ slightly between machines:** that is normal, because library versions differ. The seeds are fixed, so repeated runs on one machine match exactly.
