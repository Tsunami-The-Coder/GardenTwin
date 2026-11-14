# GardenTwin

**An AI-powered climate-resilient garden simulator**  
Veritas AI Hackathon · AI + Climate  
Pilot: tomatoes in Edison, New Jersey

GardenTwin will help home gardeners and community gardens compare how weather, soil and garden-management choices affect a growing season. See [the project brief](docs/PROJECT_BRIEF.md).

## Team

| Owner | Responsibility | Working area |
| --- | --- | --- |
| You | UI/UX, user flow, screen design and frontend presentation | `frontend/` |
| Ayaan | Backend, data, simulation and locally run AI model | `backend/`, `data/`, `models/` |
| Both | Agree on inputs/outputs, integrate, document results and prepare submission | `shared/`, `docs/` |

## Start here

1. Both clone this repository and confirm access.
2. You: follow [your UI/UX starting steps](frontend/README.md).
3. Ayaan: follow [backend setup steps](backend/README.md).
4. Together: fill in [the API planning template](shared/API_PLAN.md) before building against different assumptions.
5. Use [the shared checklist](docs/TEAM_CHECKLIST.md) to divide the remaining work.

This package contains setup documents and folder placeholders. Implementation, framework selection, dependency files and model choices belong to the team. There is no runnable application or trained model yet.

## Git workflow

```bash
git clone https://github.com/Tsunami-The-Coder/tbd.git
cd tbd
```

You create `ui-ux/initial-design`; Ayaan creates `backend/initial-setup` on his own clone:

```bash
git switch -c ui-ux/initial-design
# Work in your own folder, then stage specific files.
git add frontend
git commit -m "Add initial GardenTwin UI designs"
git push -u origin ui-ux/initial-design
```

Open a pull request into `main`. After merging, both run `git switch main` and `git pull --ff-only`. Discuss changes to `shared/` first. The repository owner needs to give Ayaan collaborator access if he does not already have it.

## Hackathon

[Official briefs and submission](https://highschoolhackathon.org/briefs) · [FAQ](https://highschoolhackathon.org/faq)

Deadline: **Sunday, November 15, 2026, 11:59 PM Eastern**. Aim to submit two hours early. Complete [the submission checklist](docs/SUBMISSION.md).
