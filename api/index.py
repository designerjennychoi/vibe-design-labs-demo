import sys
import os

# 프로젝트 루트를 path에 추가
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests as http_requests
import anthropic

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# templates, static 경로를 루트 기준으로 명시
app = Flask(
    __name__,
    template_folder=os.path.join(root, "templates"),
    static_folder=os.path.join(root, "static"),
)


def fetch_news(keyword: str, page_size: int = 5) -> list[dict]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": keyword,
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "language": "ko",
    }
    headers = {"X-Api-Key": NEWSAPI_KEY}
    try:
        response = http_requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data.get("status") != "ok":
            params.pop("language")
            response = http_requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
        articles = data.get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", ""),
                "publishedAt": a.get("publishedAt", "")[:10] if a.get("publishedAt") else "",
            }
            for a in articles
            if a.get("title") and a.get("title") != "[Removed]"
        ]
    except Exception:
        return []


def summarize_with_claude(keyword: str, articles: list[dict]) -> str:
    if not articles:
        return "관련 뉴스를 찾을 수 없습니다."
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    articles_text = "\n".join(
        [f"- 제목: {a['title']}\n  내용: {a['description'] or '(내용 없음)'}" for a in articles]
    )
    prompt = f"""다음은 '{keyword}'에 관한 최신 뉴스 기사들입니다:

{articles_text}

위 기사들을 바탕으로 '{keyword}' 관련 최신 동향을 한국어로 2~3문장으로 간결하게 요약해 주세요.
핵심 내용만 담아 독자가 빠르게 파악할 수 있도록 작성해 주세요."""
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/editorial-demo")
def editorial_demo():
    return render_template("editorial_demo.html")


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    keywords = [k.strip() for k in data.get("keywords", []) if k.strip()]
    if not keywords:
        return jsonify({"error": "키워드를 입력해 주세요."}), 400
    if not NEWSAPI_KEY:
        return jsonify({"error": "NEWSAPI_KEY가 설정되지 않았습니다."}), 500
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY가 설정되지 않았습니다."}), 500
    results = []
    for keyword in keywords:
        articles = fetch_news(keyword)
        summary = summarize_with_claude(keyword, articles)
        results.append({"keyword": keyword, "summary": summary, "articles": articles})
    return jsonify({"results": results})


# Vercel 핸들러
handler = app
