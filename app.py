from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/crawl", methods=["POST"])
def crawl():
    data = request.get_json()
    keyword = data.get('keyword')
    blog_ids = data.get('blog_ids')
    results = []

    if keyword and blog_ids:
        results = check_blog_position(keyword, blog_ids)

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

    # 케이스 1 확인 및 처리 (상위 노출 및 일반 검색 결과)
    case1_containers = soup.find_all("div", class_="spw_rerank type_head _rra_head")
    if case1_containers:
        result.extend(parse_case1(case1_containers, keyword, blog_ids))

    general_results_case1 = soup.find_all("div", class_="spw_rerank _rra_body")
    if general_results_case1:
        result.extend(parse_general_results(general_results_case1, keyword, blog_ids, "일반 검색 결과"))
    
    # 케이스 2 확인 및 처리
    case2_containers = soup.find_all("section", class_="sc_new sp_nreview _fe_view_root _prs_ugB_bsR")
    if case2_containers:
        result.extend(parse_case2(case2_containers, keyword, blog_ids))
    
    # 케이스 3 확인 및 처리
    case3_containers = soup.find_all("div", class_="sc_new _slog_visible")
    if case3_containers:
        result.extend(parse_case3(case3_containers, keyword, blog_ids))
    
    # 일반 검색 결과 확인 및 처리
    general_results = soup.find_all("section", class_="sc_new sp_ntotal _sp_ntotal _prs_web_gen _fe_root_web_gend")
    if general_results:
        result.extend(parse_general_results(general_results, keyword, blog_ids, "일반 검색 결과"))

    return result

def parse_case1(containers, keyword, blog_ids):
    result = []
    for container in containers:
        items = container.find_all("section", class_="sc_new sp_nreview _fe_view_root")
        result.extend(parse_items(items, keyword, blog_ids, "상위 노출"))
    return result

def parse_case2(containers, keyword, blog_ids):
    result = []
    for container in containers:
        items = container.find_all("li", class_="bx")
        filtered_items = [item for item in items if "bx" in item["class"] and len(item["class"]) == 1]
        result.extend(parse_items(filtered_items, keyword, blog_ids, "블로그 인기글"))
    return result

def parse_case3(containers, keyword, blog_ids):
    result = []
    for container in containers:
        theme = container.find("span", class_="fds-comps-header-headline").get_text(strip=True) if container.find("span", class_="fds-comps-header-headline") else keyword
        items = container.find_all("div", class_="fds-ugc-block-mod")
        result.extend(parse_items(items, keyword, blog_ids, theme))
    return result

def parse_general_results(containers, keyword, blog_ids, section):
    result = []
    for container in containers:
        items = container.find_all("li", class_="bx")
        filtered_items = [item for item in items if "bx" in item["class"] and len(item["class"]) == 1]
        result.extend(parse_items(filtered_items, keyword, blog_ids, section))
    return result

def parse_items(items, keyword, blog_ids, section):
    result = []
    for idx, item in enumerate(items, start=1):
        # 썸네일의 블로그 링크를 찾기
        thumbnail_tag = item.find("a", class_="user_thumb") or item.find("a", class_="thumb")
        href = thumbnail_tag["href"] if thumbnail_tag else ""
        
        # 제목 찾기
        title_tag = item.find("a", class_="title_link") or item.find("a", class_="link_tit")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        
        for blog_id in blog_ids:
            if blog_id in href:
                result.append({
                    "Keyword": keyword,
                    "Blog ID": blog_id,
                    "Section": section,
                    "Position": idx,
                    "Title": title
                })
    return result

if __name__ == "__main__":
    app.run(debug=True)
