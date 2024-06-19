from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os
import logging
import re
from dotenv import load_dotenv

# Create the Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/crawl", methods=["POST"])
def crawl():
    data = request.get_json()
    keyword = data.get('keyword')
    blog_ids = data.get('blog_ids')
    results = []

    if keyword and blog_ids:
        # 네이버에 한 번만 요청
        position_list = check_blog_position(keyword, blog_ids)
        results.extend(position_list)

    return jsonify(results)

def check_blog_position(keyword, blog_ids):
    url = f"https://search.naver.com/search.naver?query={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.naver.com/",
    }
    response = requests.get(url, headers=headers)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return []
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    result = []

    sc_new_list = soup.find_all(class_=re.compile("sc_new sp_nreview"))

    for sc_new in sc_new_list:
        user_thumb_list = sc_new.find_all("a", {"class", "user_thumb"})
        for idx, tag in enumerate(user_thumb_list, start=1):
            href = tag.get("href", "")
            for blog_id in blog_ids:
                if blog_id in href:
                    result.append({
                        "Keyword": keyword,
                        "Blog ID": blog_id,
                        "Position": idx,
                        "Theme": keyword  # 또는 다른 테마가 있다면 적절히 변경
                    })

    sc_new_list = soup.find_all("div", {"class": "sc_new _slog_visible"})

    for sc_new in sc_new_list:
        theme = keyword
        headline = sc_new.find(class_=re.compile("fds-comps-header-headline"))

        if headline:
            theme = headline.get_text()

        thumb_anchor_list = sc_new.find_all(class_=re.compile("fds-thumb-anchor"))
        for idx, thumb_anchor in enumerate(thumb_anchor_list, start=1):
            href = thumb_anchor.get("href", "")
            for blog_id in blog_ids:
                if blog_id in href:
                    result.append({
                        "Keyword": keyword,
                        "Blog ID": blog_id,
                        "Position": idx,
                        "Theme": theme
                    })

    return result

if __name__ == "__main__":
    if os.getenv("FLASK_ENV") == "development":
        app.run(
            debug=True, port=5000, host="127.0.0.1"
        )
    else:
        app.run(debug=True)
