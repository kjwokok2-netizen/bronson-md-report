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
if not GEMINI_KEY: exit()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 데이터 수집 (수집량 극대화)
def get_naver_search(keyword, target="shop"):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id: return ""
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=20" # 데이터 확보량 최대치
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    try:
        response = urllib.request.urlopen(request_obj)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            clean = lambda x: x.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&#39;', "'")
            return "\n".join([f"- {clean(i['title'])}: {clean(i.get('description', ''))[:100]}" for i in data['items']])
    except: return ""
    return ""

def get_youtube_data(keyword):
    encoded_query = urllib.parse.quote(keyword)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"\}', response.text)
        return " / ".join(list(set([t for t in titles if len(t) > 5]))[:7])
    except: return ""

# 3. 데이터 취합 (주완 MD 지정 모든 키워드 포함)
def collect_data():
    target_keywords = [
        "아웃스탠딩", "에스피오나지", "프리즘웍스", "브론슨 의류", 
        "리얼맥코이", "버즈릭슨", "더블알엘 RRL", "웨어하우스 복각", "오어슬로우", "오디너리핏츠",
        "남자 아메카지 코디", "밀리터리 복각", "워크웨어 팬츠", "고아캐드", "브랜디드"
    ]
    all_info = []
    for kw in target_keywords:
        all_info.append(f"### [KEYWORD DATA: {kw}] ###")
        all_info.append(get_naver_search(kw, "shop"))
        all_info.append(get_naver_search(kw, "cafearticle"))
        all_info.append(get_youtube_data(kw))
        all_info.append("\n")
    return "\n".join(all_info)

# 4. 리포트 생성 (브랜드 누락 금지 프롬프트)
def generate_report(data):
    today = datetime.now()
    w_range = f"{(today - timedelta(days=7)).strftime('%m/%d')} ~ {today.strftime('%m/%d')}"
    
    prompt = f"""
    당신은 브론슨(Bronson)의 수석 MD입니다. 제공된 데이터를 기반으로 리포트를 작성하되, 아래 지시를 어길 시 큰 손실이 발생합니다.

    [절대 규칙]
    1. 데이터에 포함된 '모든 브랜드'의 분석 내용을 누락 없이 포함하세요. (아웃스탠딩, 에스피오나지, 프리즘웍스, 브론슨, 맥코이, 버즈릭슨, RRL, 웨어하우스, 오어슬로우, 오디너리핏츠)
    2. '오디너리핏츠'는 반드시 일본 브랜드 섹션에 넣으세요.
    3. 주간(최근 7일) 핵심 이슈와 이번 달 전체 전략 섹션을 명확히 구분하세요.
    4. 스르비 언급, 발신/수신 등 모든 불필요한 수식어는 제거하세요.
    5. 가독성을 위해 카드형 레이아웃(<div class="card">)과 강조 배지(<span class="badge">)를 적극 사용하세요.

    [원본 데이터]
    {data}
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 5. 디자인 UI (사이드바 및 고밀도 카드 적용)
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bronson Intelligence Center</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            :root {{ --primary: #c0392b; --dark: #1a1a1a; --bg: #f2f2f2; }}
            body {{ font-family: 'Pretendard', sans-serif; background: var(--bg); color: #333; margin: 0; display: flex; }}
            nav {{ width: 260px; background: var(--dark); height: 100vh; position: fixed; padding: 40px 20px; color: #fff; }}
            nav h2 {{ color: var(--primary); font-size: 1.1em; letter-spacing: 2px; }}
            main {{ flex: 1; margin-left: 260px; padding: 50px 80px; }}
            header {{ border-bottom: 4px solid var(--dark); padding-bottom: 20px; margin-bottom: 50px; }}
            .card {{ background: #fff; border-radius: 8px; padding: 40px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #ddd; }}
            .card h2 {{ font-size: 1.7em; margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 15px; color: var(--dark); }}
            .badge {{ background: #fff0f0; color: var(--primary); padding: 3px 10px; border-radius: 4px; font-weight: 700; font-size: 0.85em; border: 1px solid #ffcccc; }}
            p, li {{ line-height: 1.9; font-size: 1.1em; }}
            .youtube-item {{ color: #7f8c8d; font-size: 0.9em; font-style: italic; }}
        </style>
    </head>
    <body>
        <nav>
            <h2>BRONSON<br>INTELLIGENCE</h2>
            <p style="font-size: 0.8em; opacity: 0.5;">Weekly & Monthly Data Analysis</p>
        </nav>
        <main>
            <header>
                <h1 style="margin:0; font-size: 2.5em; letter-spacing: -2px;">STRATEGIC MD REPORT</h1>
                <div style="margin-top:10px; font-weight:700; color:#888;">UPDATE: {now}</div>
            </header>
            {content}
        </main>
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
