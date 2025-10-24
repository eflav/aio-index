from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from aio_host import extract_text, summarize, upload_json, sanitize_filename, update_index
from datetime import datetime
import uvicorn
import os

# -------------------------------------------------------------------
# 🚀 Initialize FastAPI app with secure CORS (Framer + API domains)
# -------------------------------------------------------------------
app = FastAPI(title="AIO Flow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://numerical-psychology-661091.framer.app",  # Your Framer site
        "https://aioflow-api.onrender.com",               # Your API domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# 🏠 Root endpoint (for easy browser test)
# -------------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "✅ AIOFlow API is live. Use /analyze?url=https://example.com"}


# -------------------------------------------------------------------
# 🤖 Main AIO analysis endpoint (supports GET + POST)
# -------------------------------------------------------------------
@app.get("/analyze")
@app.post("/analyze")
async def analyze(request: Request, url: str = Query(None)):
    """
    Analyze a website — supports both GET (for browsers) and POST (for API calls)
    """

    # Handle POST body (JSON)
    if request.method == "POST":
        try:
            data = await request.json()
            url = url or data.get("url")
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    # Validate input
    if not url:
        return JSONResponse({"error": "Missing URL"}, status_code=400)

    try:
        # -------------------------------------------------------------------
        # 🧠 Normalize user input (add https:// if missing, strip trailing /)
        # -------------------------------------------------------------------
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url.lstrip("/")
        if url.endswith("/"):
            url = url[:-1]

        # -------------------------------------------------------------------
        # 🔍 Extract + Summarize Website
        # -------------------------------------------------------------------
        text = extract_text(url)
        summary = summarize(text, url)

        # -------------------------------------------------------------------
        # 💾 Upload JSON report to GitHub
        # -------------------------------------------------------------------
        payload = {
            "source": url,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "data": summary,
        }

        filename = sanitize_filename(url)
        upload_json(filename, payload)
        update_index(url, filename, summary.get("aio_score", 0))

        # -------------------------------------------------------------------
        # ✅ Return response to frontend
        # -------------------------------------------------------------------
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


# -------------------------------------------------------------------
# 🧩 Local entry point (used if running directly)
# -------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
