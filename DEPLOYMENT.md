# Deployment

The app is prepared for Streamlit Community Cloud and other Python hosts.

## Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create a Streamlit app with `app.py` as the entrypoint.
3. Keep Python 3.12 from `runtime.txt`.
4. Add `GEMINI_API_KEY` in the platform secret manager only when the optional LLM path is required.
5. Deploy and verify the Overview, Forecast Drivers, Policy Eval, and AI Agent tabs.

The app remains functional without an API key because the SCM Agent has a deterministic local fallback.

## Local production smoke test

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8501 --server.headless true
```

Open `http://localhost:8501`.

## Release checks

- Confirm all committed CSV files load.
- Confirm the data topology and both forecast-driver charts render.
- Confirm city and inventory-status filters update headline metrics.
- Confirm the Forecast Drivers detail selectors rerender without errors.
- Confirm the AI Agent returns a local answer without secrets.
- Confirm no `.env` or `.streamlit/secrets.toml` file is committed.
