# Ayaan's backend and local AI workspace

Owner: Ayaan.

Machine: Windows, RTX 4060, 32 GB DDR5 RAM. You choose the backend framework, local model approach, dependencies and GPU use.

## Environment setup

Install Git and a Python version compatible with the libraries you select. Clone the repo, open PowerShell in its root, then:

```powershell
git switch -c backend/initial-setup
py -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
```

Use `.\.venv\Scripts\python.exe` directly for commands, or activate with `.\.venv\Scripts\Activate.ps1` if your system permits it. Create your own requirements or project file after choosing the stack. Check your chosen ML library's official Windows/GPU instructions before installing GPU packages.

## Your starting steps

1. Read `docs/PROJECT_BRIEF.md`; agree on the first version with your teammate.
2. Pick weather and soil sources; record their coverage, units, licenses and limitations in `data/README.md`.
3. Decide which quantities the simulation calculates, which the AI predicts, and which data can actually validate those predictions.
4. Fill in `shared/API_PLAN.md` with your teammate before implementing endpoints.
5. Set up backend files and dependencies yourself in this folder.
6. Decide where local model weights, preprocessing settings and evaluation outputs live in `models/`.
7. Give your teammate your actual install/run commands and one labeled example response when available.

## Evaluation reminders for your design

Use earlier dates for training and later dates for testing. Compare forecasts with a simple persistence baseline and compare watering strategies under the same weather and assumptions. Distinguish measured predictive accuracy from simulated water savings. Record failures as well as improvements.

No framework, model, simulation implementation or dependencies have been added by this setup package.
