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

# 2. 데이터 수집 모듈 (네이버 API & 유튜브)
def get_naver_search(keyword, target="cafearticle"):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id: return ""
    encText = urllib.parse.quote(keyword)
    # 데이터 밀도를 위해 수집량 유지 (20개)
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=20"
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    try:
        response = urllib.request.urlopen(request_obj)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            clean = lambda x: x.replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            return "\n".join([f"[{target}] {clean(i['title'])}: {clean(i.get('description', ''))[:100]}" for i in data['items']])
    except: return ""
    return ""

# 3. 데이터 취합 (브론슨을 포함한 전체 시장 쿼리)
def collect_data():
    # 브론슨을 포함하여 검색하되, 리포트 분석의 대조군으로 활용함
    queries = [
        "남자 아메카지 코디", "밀리터리 복각 자켓", "워크웨어 팬츠", 
        "아웃스탠딩", "에스피오나지", "프리즘웍스", "브론슨 의류", 
        "리얼맥코이", "버즈릭슨", "더블알엘 RRL", "웨어하우스 복각", 
        "오어슬로우", "오디너리핏츠", "엔지니어드가먼츠", "고아캐드", "브랜디드"
    ]
    raw_data = []
    for q in queries:
        raw_data.append(get_naver_search(q, "cafearticle"))
        raw_data.append(get_naver_search(q, "blog"))
    return "\n".join(raw_data)

# 4. 리포트 생성 (외부 시장 통찰 중심)
def generate_report(data):
    today = datetime.now()
    w_range = f"{(today - timedelta(days=7)).strftime('%m/%d')} ~ {today.strftime('%m/%d')}"
    
    prompt = f"""
    당신은 브랜드 '브론슨(Bronson)'의 수석 전략 MD입니다. 
    수집된 전체 시장 데이터를 분석하여 실무용 리포트를 작성하세요.

    [핵심 지침]
    1. 데이터 분석 범위: 브론슨을 포함한 모든 수집 데이터를 활용하되, 리포트 결과에서 '브론슨 자사 제품 모니터링' 섹션은 제외할 것.
    2. 분석의 목적: 외부 경쟁사 동향과 커뮤니티(고아캐드, 브랜디드 등)의 실시간 여론을 분석하여 브론슨이 취해야 할 '전략적 우위'를 도출하는 것임.
    3. 주간/월간 통합: 최근 7일간의 폭발적인 이슈 키워드와 이번 달 전체를 관통하는 흐름을 구분하여 작성할 것.
    4. 문체: 전문 비즈니스 개조식(~함, ~임)을 사용하고, '습니다'체는 배제할 것.
    5. 오디너리핏츠는 일본 브랜드로 분류할 것.

    [수집 데이터]
    {data}
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 5. 세련된 실무 대시보드 UI
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Bronson Market Intelligence Dashboard</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            :root {{ --primary: #c0392b; --dark: #121212; --bg: #f5f6fa; }}
            body {{ font-family: 'Pretendard', sans-serif; background: var(--bg); color: #333; margin: 0; padding: 0; }}
            .wrapper {{ max-width: 1200px; margin: 40px auto; padding: 0 20px; }}
            .header {{ background: var(--dark); color: #fff; padding: 40px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: flex-end; }}
            .header h1 {{ margin: 0; font-size: 2.2em; letter-spacing: -1.5px; }}
            .header .info {{ text-align: right; opacity: 0.7; font-weight: 600; }}
            .main-report {{ background: #fff; padding: 60px; border-radius: 0 0 8px 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}
            .content h2 {{ font-size: 1.7em; color: var(--primary); margin-top: 50px; border-bottom: 2px solid #f1f2f6; padding-bottom: 15px; }}
            .content p, .content li {{ line-height: 1.9; font-size: 1.1em; color: #444; }}
            .strategy-highlight {{ background: #fff5f5; border-left: 5px solid var(--primary); padding: 30px; margin-top: 40px; border-radius: 4px; }}
            .strategy-highlight h3 {{ margin-top: 0; color: var(--primary); }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="header">
                <h1>MARKET INTELLIGENCE</h1>
                <div class="info">UPDATE: {now}<br>FOR BRONSON STRATEGY TEAM</div>
            </div>
            <main class="main-report">
                <div class="content">
                    {content}
                </div>
            </main>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    raw_info = collect_data()
    report_text = generate_report(raw_info)
    save_to_html(report_text)
