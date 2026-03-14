import os
import requests
import urllib.request
import urllib.parse
import json
import re
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime, timedelta

# 1. Gemini API 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") 
if not GEMINI_KEY:
    print("에러: API 키 미설정")
    exit()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 데이터 수집 모듈 (네이버 수집량 증대: 15개)
def get_naver_search(keyword, target="shop"):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id: return ""
    encText = urllib.parse.quote(keyword)
    # 데이터 밀도를 높이기 위해 display를 15로 상향
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=15"
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    try:
        response = urllib.request.urlopen(request_obj)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            clean = lambda x: x.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&#39;', "'")
            return "\n".join([f"- {clean(i['title'])}: {clean(i.get('description', ''))[:80]}" for i in data['items']])
    except: return ""
    return ""

def get_youtube_data(keyword):
    encoded_query = urllib.parse.quote(keyword)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"\}', response.text)
        return " / ".join([t for t in titles if len(t) > 5][:5])
    except: return ""

# 3. 데이터 취합 (브론슨 타겟 브랜드 및 키워드)
def collect_data():
    target_keywords = [
        "아웃스탠딩", "에스피오나지", "프리즘웍스", "브론슨 의류", 
        "리얼맥코이", "버즈릭슨", "더블알엘 RRL", "웨어하우스 복각", "오어슬로우", "오디너리핏츠",
        "남자 아메카지 코디", "밀리터리 복각 자켓"
    ]
    all_info = []
    for kw in target_keywords:
        all_info.append(f"### [SOURCE: {kw}] ###")
        all_info.append(get_naver_search(kw, "shop"))
        all_info.append(get_naver_search(kw, "cafearticle"))
        all_info.append(get_youtube_data(kw))
        all_info.append("\n")
    return "\n".join(all_info)

# 4. 이원화 리포트 생성 (주간/월간 분리 프롬프트)
def generate_report(data):
    today = datetime.now()
    # 주간 범위 (직전 7일)
    w_start = (today - timedelta(days=7)).strftime('%Y/%m/%d')
    w_end = today.strftime('%Y/%m/%d')
    # 월간 범위 (이번 달 1일 ~ 현재)
    m_start = today.replace(day=1).strftime('%Y/%m/%d')
    m_end = today.strftime('%Y/%m/%d')
    
    prompt = f"""
    당신은 브론슨(Bronson)의 수석 MD입니다. 제공된 데이터만을 근거로 리포트를 작성하세요.
    내용은 크게 '주간 분석'과 '월간 전략' 두 섹션으로 명확히 구분되어야 합니다.

    [기간 정보]
    - 주간 분석 범위: {w_start} ~ {w_end} (최근 7일)
    - 월간 분석 범위: {m_start} ~ {m_end} (이번 달 전체)

    [수집 데이터]
    {data}

    [작성 가이드라인]
    1. SECTION 1: WEEKLY HOT-ISSUE ({w_start} ~ {w_end})
       - 최근 7일간 커뮤니티(고아캐드, 브랜디드)와 유튜브에서 가장 뜨거웠던 아이템과 브랜드를 분석하세요.
       - 소비자들의 즉각적인 반응과 결핍 요소를 도출하세요.

    2. SECTION 2: MONTHLY STRATEGY OUTLOOK ({m_start} ~ {m_end})
       - 이번 달 전체 데이터를 관통하는 핵심 실루엣과 소재의 흐름을 정리하세요.
       - 브론슨이 이번 달 남은 기간 동안 집중해야 할 '핵심 타겟 상품군'을 제안하세요.

    [주의 사항]
    - 발신/수신, 영문 헤더 등 불필요한 수식어는 일절 제거하세요.
    - 오디너리핏츠는 반드시 일본 브랜드 섹션에 포함하세요.
    - 데이터가 없는 부분은 억지로 지어내지 말고 '정보 없음'으로 처리하세요.
    - 전문적인 비즈니스 문체로 HTML 형식을 사용하여 작성하세요.
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 5. 디자인 UI (주간/월간 가독성 강화)
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Bronson MD Intelligence</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            body {{ font-family: 'Pretendard', sans-serif; background-color: #f4f4f4; color: #222; margin: 0; padding: 40px 20px; }}
            .container {{ max-width: 900px; margin: auto; background: #fff; padding: 60px; border-radius: 2px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); }}
            header {{ border-bottom: 5px solid #1a1a1a; padding-bottom: 20px; margin-bottom: 50px; }}
            header h1 {{ font-size: 2.4em; margin: 0; letter-spacing: -1.5px; color: #1a1a1a; }}
            .date {{ font-weight: 700; color: #999; margin-top: 10px; }}
            .content h2 {{ font-size: 1.6em; color: #c0392b; margin-top: 50px; border-left: 5px solid #c0392b; padding-left: 15px; }}
            .content p, .content li {{ line-height: 1.9; font-size: 1.1em; color: #444; }}
            .monthly-section {{ background: #fdfdfd; border: 1px solid #eee; padding: 30px; margin-top: 50px; border-radius: 8px; }}
            hr {{ border: 0; border-top: 1px solid #eee; margin: 50px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Bronson Strategic Report</h1>
                <div class="date">Issue Date: {now}</div>
            </header>
            <div class="content">
                {content}
            </div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    raw_info = collect_data()
    with open("raw_data_log.txt", "w", encoding="utf-8") as f:
        f.write(raw_info)
    report_text = generate_report(raw_info)
    save_to_html(report_text)
