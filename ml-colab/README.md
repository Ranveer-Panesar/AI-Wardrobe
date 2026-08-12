# ml-colab — Self-hosted VTON showcase

This folder holds the Colab notebook(s) used for the self-hosted virtual
try-on showcase (Phase 6 of the project plan).

- `vton_server.ipynb` (to be added) — loads CatVTON/IDM-VTON, wraps it in a
  small FastAPI app, exposes it via `pyngrok` so the main backend can call it
  over HTTP.

**Why this lives in its own folder instead of inside `backend/`:** it runs
on Google's GPU, not your local machine, and it's edited/run directly in the
Colab UI rather than through your normal local dev loop. Keeping it separate
avoids confusion about where code actually executes.

The backend talks to whatever's running here through the `RenderProvider`
abstraction (see `backend/app` — added in Phase 6) via the ngrok URL set in
`COLAB_RENDER_URL` in `.env`.
