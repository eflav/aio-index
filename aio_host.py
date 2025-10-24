import os
import json
import base64
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from openai import OpenAI

# === ENVIRONMENT VARIABLES ===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME, OPENAI_API_KEY]):
    raise SystemExit("Please ensure GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME, and OPENAI_API_KEY are set.")

# === SETUP ===
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
client = OpenAI(api_key=OPENAI_API_KEY)

# === CORE FUNCTIONS ===

def extract_text(url: str) -> str:
    """Fetch website and extract readable text."""
    print("🕷️  Fetching website...")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for s in soup(["script", "style", "noscript"]):
        s.extract()
    text = " ".join(soup.stripped_strings)
    return text[:8000]


def summarize(text: str, url: str) -> dict:
    """Use OpenAI GPT-4 to generate structured AIO summary."""
    print("🤖  Summarizing with GPT-4...")
    prompt = f"""
    You are an AI Optimization assistant. Analyze the following webpage content
    and output a compact JSON object with these fields:

    {{
      "summary": "...",
      "brand": "...",
      "services": ["..."],
      "location": "...",
      "topics": ["..."],
      "aio_score": integer 0-100 estimating AI readability and clarity
    }}

    Page URL: {url}
    Content:
    {text[:7000]}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("⚠️  JSON parse error:", e)
        return {"summary": text[:120] + "...", "brand": "", "services": [], "location": "", "topics": [], "aio_score": 0}


def get_existing_sha(path: str):
    """Check if file already exists on GitHub (for updating)."""
    r = requests.get(f"{API_BASE}/{path}", headers=HEADERS)
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def upload_json(path: str, data: dict):
    """Upload or update JSON file to GitHub repo under /data/ folder."""
    # Ensure path includes data/ prefix
    if not path.startswith("data/"):
        path = f"data/{path}"

    content = json.dumps(data, indent=2)
    b64 = base64.b64encode(content.encode()).decode()
    existing_sha = get_existing_sha(path)
    payload = {
        "message": f"Update {path}" if existing_sha else f"Add {path}",
        "content": b64,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    r = requests.put(f"{API_BASE}/{path}", headers=HEADERS, json=payload)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub upload failed: {r.status_code} - {r.text}")
    print(f"✅ Uploaded {path} successfully.")


def sanitize_filename(url: str) -> str:
    url = url.replace("https://", "").replace("http://", "")
    for ch in ["/", "?", "&", "=", "#"]:
        url = url.replace(ch, "_")
    return url.strip("_") + ".json"


def update_index(source_url, filename, aio_score):
    """Add or update a record in index.json."""
    print("📇  Updating index.json...")
    index_path = "index.json"
    entry = {
        "source": source_url,
        "json": f"data/{filename}",  # reference new data folder
        "aio_score": aio_score,
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }

    # Try to read existing index.json
    existing_index = []
    r = requests.get(f"{API_BASE}/{index_path}", headers=HEADERS)
    if r.status_code == 200:
        try:
            content = base64.b64decode(r.json()["content"]).decode()
            existing_index = json.loads(content)
        except Exception as e:
            print("⚠️  Could not read existing index.json:", e)

    # Replace or add entry
    existing_index = [i for i in existing_index if i["source"] != source_url]
    existing_index.append(entry)

    # Upload updated index
    upload_json(index_path, existing_index)
    print("✅  index.json updated.")


def main():
    url = input("Paste a website URL: ").strip()
    text = extract_text(url)
    summary = summarize(text, url)

    # Save and upload JSON summary
    payload = {
        "source": url,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "data": summary,
    }

    filename = sanitize_filename(url)
    print("⬆️  Uploading JSON to GitHub (data folder)...")
    upload_json(filename, payload)

    # Update index.json
    update_index(url, filename, summary.get("aio_score", 0))

    public_url = f"https://{GITHUB_USERNAME}.github.io/{GITHUB_REPO.split('/')[-1]}/data/{filename}"
    index_url = f"https://{GITHUB_USERNAME}.github.io/{GITHUB_REPO.split('/')[-1]}/index.json"
    print(f"\n✅ Hosted JSON:\n{public_url}")
    print(f"📇 Live Index:\n{index_url}")


if __name__ == "__main__":
    main()
