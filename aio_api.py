from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from aio_host import extract_text, summarize, upload_json, sanitize_filename, update_index
from datetime import datetime
import uvicorn
import json
import os

app = FastAPI(title="AIO Flow API")


@app.get("/")
def home():
    return {"message": "✅ AIOFlow API is live. Use /analyze?url=https://example.com"}


@app.get("/analyze")
@app.post("/analyze")
async def analyze(request: Request, url: str = Query(None)):
    """
    Analyze a website — supports both GET (for browsers) and POST (for API calls)
    """

    # If POST, read JSON body
    if request.method == "POST":
        try:
            data = await request.json()
            url = url or data.get("url")
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    # Validate URL
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

        return JSONResponse(
            {
                "status": "ok",
                "url": url,
                "aio_score": summary.get("aio_score", 0),
                "summary": summary.get("summary", ""),
            },
            status_code=200,
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
