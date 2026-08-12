# AI-Wardrobe

An AI-powered wardrobe assistant: upload your clothes, get them auto-classified,
receive outfit suggestions, and preview them via virtual try-on.

## Repo layout

```
AI-Wardrobe/
├── backend/       FastAPI service — auth, wardrobe API, combination engine,
│                   classification, VTON integration (Ranveer)
├── frontend/       React (Vite) web app (teammate)
├── ml-colab/       Colab notebook(s) for self-hosted VTON showcase
├── docs/           Project plan, architecture notes, API contract
└── .gitignore
```

## Getting started

- Backend setup: see `backend/README.md`
- Frontend setup: see `frontend/README.md`
- Full roadmap: see `docs/PROJECT_PLAN.md`

## Contributing (just the two of us, but still)

We use a PR-based workflow — no direct pushes to `main`. Branch, commit,
push, open a PR, get a review, merge. See `docs/PROJECT_PLAN.md` Phase 0
for setup status.
