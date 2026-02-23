import sys
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

from flask import Flask, render_template, request, jsonify
import requests as req
import anthropic

NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

app = Flask(
    __name__,
    template_folder=os.path.join(root, "templates"),
    static_folder=os.path.join(root, "static"),
)


def fetch_news(keyword, page_size=5):
    url = "https://newsapi.org/v2/everything"
    params = {"q": keyword, "sortBy": "publishedAt", "pageSize": page_size, "language": "ko"}
    headers = {"X-Api-Key": NEWSAPI_KEY}
    try:
        r = req.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        if data.get("status") != "ok":
            params.pop("language")
            r = req.get(url, params=params, headers=headers, timeout=10)
            data = r.json()
        return [
            {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", ""),
                "publishedAt": a.get("publishedAt", "")[:10] if a.get("publishedAt") else "",
            }
            for a in data.get("articles", [])
            if a.get("title") and a.get("title") != "[Removed]"
        ]
    except Exception:
        return []


def summarize_with_claude(keyword, articles):
    if not articles:
        return "관련 뉴스를 찾을 수 없습니다."
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    articles_text = "\n".join(
        [f"- 제목: {a['title']}\n  내용: {a['description'] or '(내용 없음)'}" for a in articles]
    )
    prompt = f"""다음은 '{keyword}'에 관한 최신 뉴스 기사들입니다:\n\n{articles_text}\n\n위 기사들을 바탕으로 '{keyword}' 관련 최신 동향을 한국어로 2~3문장으로 간결하게 요약해 주세요."""
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


handler = app
