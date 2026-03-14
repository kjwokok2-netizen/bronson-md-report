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
    exit()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 데이터 수집 (네이버 & 유튜브)
def get_naver_search(keyword, target="shop"):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id: return ""
    encText = urllib.parse.quote(keyword)
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

# 3. 데이터 취합
def collect_data():
    target_keywords = [
        "아웃스탠딩", "에스피오나지", "프리즘웍스", "브론슨 의류", 
        "리얼맥코이", "버즈릭슨", "더블알엘 RRL", "웨어하우스 복각", "오어슬로우", "오디너리핏츠",
        "남자 아메카지 코디", "밀리터리 복각"
    ]
    all_info = []
    for kw in target_keywords:
        all_info.append(f"### [SOURCE: {kw}] ###")
        all_info.append(get_naver_search(kw, "shop"))
        all_info.append(get_naver_search(kw, "cafearticle"))
        all_info.append(get_youtube_data(kw))
        all_info.append("\n")
    return "\n".join(all_info)

# 4. 리포트 생성 (가독성 높은 HTML 구조화 요청)
def generate_report(data):
    today = datetime.now()
    w_start = (today - timedelta(days=7)).strftime('%m/%d')
    w_end = today.strftime('%m/%d')
    m_name = today.strftime('%m')
    
    prompt = f"""
    당신은 브론슨(Bronson)의 수석 MD입니다. 제공된 데이터를 바탕으로 실무용 전략 리포트를 작성하세요.

    [작성 규칙]
    1. 가독성을 위해 각 분석 포인트는 <div class="card"> 섹션으로 구분하세요.
    2. 핵심 키워드나 결론은 <span class="badge"> 태그를 활용해 강조하세요.
    3. 주간 분석(Weekly)과 월간 분석(Monthly)을 명확히 분리하세요.
    4. 발신/수신/스르비 언급은 절대 금지합니다.
    5. 오직 아래 {w_start}~{w_end} 기간에 수집된 데이터로만 작성하세요.

    [데이터 소스]
    {data}
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 5. 디자인 최적화 HTML
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bronson Intelligence Report</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            :root {{ --primary: #c0392b; --dark: #2d3436; --bg: #f5f6fa; --card-bg: #ffffff; }}
            body {{ font-family: 'Pretendard', sans-serif; background-color: var(--bg); color: var(--dark); margin: 0; display: flex; }}
            
            /* Sidebar Navigation */
            nav {{ width: 240px; background: var(--dark); height: 100vh; position: fixed; color: white; padding: 40px 20px; box-sizing: border-box; }}
            nav h2 {{ font-size: 1.2em; margin-bottom: 30px; letter-spacing: 1px; color: var(--primary); }}
            nav ul {{ list-style: none; padding: 0; }}
            nav li {{ margin-bottom: 15px; font-size: 0.95em; opacity: 0.7; cursor: pointer; transition: 0.3s; }}
            nav li:hover {{ opacity: 1; color: var(--primary); }}

            /* Main Content */
            main {{ flex: 1; margin-left: 240px; padding: 60px 80px; }}
            header {{ margin-bottom: 60px; }}
            header h1 {{ font-size: 2.8em; margin: 0; letter-spacing: -1.5px; line-height: 1.1; }}
            .date-badge {{ display: inline-block; background: var(--primary); color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.85em; margin-top: 15px; font-weight: 600; }}

            /* Card Style */
            .card {{ background: var(--card-bg); border-radius: 12px; padding: 35px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border: 1px solid #edf2f7; }}
            .card h2 {{ font-size: 1.6em; margin-top: 0; color: #1a1a1a; border-bottom: 2px solid #f1f2f6; padding-bottom: 15px; }}
            .card h3 {{ color: var(--primary); font-size: 1.2em; margin-top: 25px; }}
            
            /* Text Style */
            p, li {{ line-height: 1.8; font-size: 1.05em; color: #4a5568; }}
            .badge {{ background: #fff5f5; color: var(--primary); padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.9em; margin-right: 5px; border: 1px solid #ffdada; }}
            
            /* Action Box */
            .action-box {{ background: #1a1a1a; color: #fff; padding: 30px; border-radius: 12px; margin-top: 50px; }}
            .action-box h3 {{ color: var(--primary); margin-top: 0; }}

            @media (max-width: 1024px) {{
                nav {{ display: none; }}
                main {{ margin-left: 0; padding: 40px 20px; }}
            }}
        </style>
    </head>
    <body>
        <nav>
            <h2>BRONSON<br>LAB</h2>
            <ul>
                <li>• Weekly Hot-Issue</li>
                <li>• Brand Benchmarking</li>
                <li>• Monthly Outlook</li>
                <li>• Action Plan</li>
            </ul>
        </nav>
        <main>
            <header>
                <h1>Weekly Strategic Intelligence</h1>
                <div class="date-badge">Report Issued: {now}</div>
            </header>
            <section class="content">
                {content}
            </section>
            <div class="action-box">
                <h3>※ MD's Action Summary</h3>
                <p>본 리포트는 인공지능이 최근 7일간의 온라인 VOC와 트렌드 데이터를 교차 분석한 결과입니다. 브론슨 기획 회의 시 의사결정 보조 자료로 활용하십시오.</p>
            </div>
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
