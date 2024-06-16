from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import openpyxl
import requests
from bs4 import BeautifulSoup
import os
import logging
import pprint
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS")}})

# logging.basicConfig(level=logging.DEBUG)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route("/crawl", methods=["POST"])
def crawl():
    data = request.get_json()

    # 여기에서 데이터를 처리합니다.
    # 예를 들어, 각 항목에 새로운 필드를 추가할 수 있습니다.
    results = []
    for item in data:
        keyword, blog_id = item
        position_list = check_blog_position(keyword, blog_id)
        for position, theme in position_list:
            results.append(
                {
                    "Keyword": keyword,
                    "Blog ID": blog_id,
                    "Position": position,
                    "Theme": theme,
                }
            )

    return jsonify(results)


def check_blog_position(keyword, blog_id):
    print("keyword : ", keyword)
    url = f"https://search.naver.com/search.naver?query={keyword}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    result = []

    sc_new_list = soup.find_all(class_=re.compile("sc_new sp_nreview"))

    for sc_new in sc_new_list:
        user_thumb_list = sc_new.find_all("a", {"class", "user_thumb"})
        print("blog count : ", len(user_thumb_list))
        for idx, tag in enumerate(user_thumb_list, start=1):
            href = tag.get("href", "")
            print("link : ", href)
            if blog_id in href:
                result.append((idx, keyword))

    sc_new_list = soup.find_all("div", {"class": "sc_new _slog_visible"})

    for sc_new in sc_new_list:
        theme = keyword
        headline = sc_new.find(class_=re.compile("fds-comps-header-headline"))

        if headline:
            theme = headline.get_text()
            print("theme : ", theme)

        thumb_anchor_list = sc_new.find_all(class_=re.compile("fds-thumb-anchor"))
        print("blog count : ", len(thumb_anchor_list))
        for idx, thumb_anchor in enumerate(thumb_anchor_list, start=1):
            href = thumb_anchor.get("href", "")
            print("link : ", href)
            if blog_id in href:
                result.append((idx, theme))

    return result


if __name__ == "__main__":
    if os.getenv("FLASK_ENV") == "development":
        app.run(
            debug=True, port=5000, host="127.0.0.1"
        )  # 외부에서 접속 가능하도록 설정
    else:
        app.run(debug=True)  # 외부에서 접속 가능하도록 설정
