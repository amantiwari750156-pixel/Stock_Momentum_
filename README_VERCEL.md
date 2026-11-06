# India Momentum Scanner — Vercel Edition (DEMA + Clean Chart)

The local Streamlit dashboard is `streamlit_app.py` so Vercel does not misidentify it as a serverless function. The FastAPI backend is `api/index.py` and exports `app`.

This package deploys the latest scanner logic as a static browser dashboard with a Python FastAPI serverless backend. It includes EMA 50/100/200, DEMA 50, DEMA-vs-EMA bullish crossover scans, price crosses above/below selected averages, and a clean chart that displays only user-selected moving-average overlays and signal markers.

## Deploy to Vercel
1. Extract this ZIP. Its contents (including `index.html`, `api/`, `scanner/`, `requirements.txt`, and `vercel.json`) must be at the root of the GitHub repository.
2. Push the files to GitHub.
3. In Vercel select **Add New → Project**, import that repository, leave Root Directory as `./`, and deploy.
4. No environment variables are needed for the initial deployment. Start with Nifty 50 and a batch size of 10–25 to test market-data access and function limits.

## Important
- Vercel serverless functions have execution and memory limits; full NSE scans may need multiple batches and may be interrupted by Yahoo Finance throttling.
- Yahoo Finance is unofficial and may be delayed or incomplete.
- Caches in `/tmp` are temporary. This edition retains scan results in the browser session, not as permanent database history.
- `localhost:8501` is your Mac's local Streamlit dashboard; it is not the Vercel website.

## Local API test
`pip install -r requirements.txt && uvicorn api.index:app --reload` then open `http://127.0.0.1:8000/docs`.
