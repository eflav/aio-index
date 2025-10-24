from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from aio_host import extract_text, summarize, upload_json, sanitize_filename, update_index
from datetime import datetime
import uvicorn
import json
import os

app = FastAPI(title="AIO Flow API")

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        return JSONResponse({"error": "Missing URL"}, status_code=400)

    try:
        # Fetch and summarize the site
        text = extract_text(url)
        summary = summarize(text, url)

        # Upload JSON to GitHub
        payload = {
            "source": url,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "data": summary,
        }
        filename = sanitize_filename(url)
        upload_json(filename, payload)
        update_index(url, filename, summary.get("aio_score", 0))

        return {
            "status": "ok",
            "url": url,
            "aio_score": summary.get("aio_score", 0),
            "summary": summary.get("summary", ""),
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
