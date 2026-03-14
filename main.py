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

# 2. 유튜브 검색 결과 수집
def get_youtube_data(keyword):
    encoded_query = urllib.parse.quote(keyword)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"\}', response.text)
        results = [t for t in titles if len(t) > 5][:5]
        return f"[YouTube '{keyword}' 동향]: " + " / ".join(results)
    except: return ""

# 3. 네이버 통합 검색 (쇼핑, 블로그, 카페글)
def get_naver_search(keyword, target="shop"):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id: return ""
    
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=10"
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

# 4. 데이터 취합 (브론슨 집중 타겟팅)
def collect_data():
    target_keywords = [
        "아웃스탠딩", "에스피오나지", "프리즘웍스", "브론슨 의류", 
        "리얼맥코이", "버즈릭슨", "더블알엘 RRL", "웨어하우스 복각", "오어슬로우", "오디너리핏츠",
        "남자 아메카지 코디", "밀리터리 복각 자켓", "워크웨어 브랜드 추천"
    ]
    all_info = []
    for kw in target_keywords:
        all_info.append(f"### [SOURCE: {kw}] ###")
        all_info.append(get_naver_search(kw, "shop"))
        all_info.append(get_naver_search(kw, "cafearticle"))
        all_info.append(get_youtube_data(kw))
        all_info.append("\n")
    return "\n".join(all_info)

# 5. 브론슨 전용 전략 보고서 생성 (프롬프트에서 스르비 삭제)
def generate_report(data):
    today = datetime.now()
    date_context = f"{(today - timedelta(days=7)).strftime('%Y/%m/%d')} - {today.strftime('%Y/%m/%d')}"
    
    prompt = f"""
    당신은 15년 차 시니어 패션 MD이자 '브론슨(Bronson)'의 수석 브랜드 매니저입니다.
    다음 수집된 데이터를 바탕으로 브론슨 기획팀이 즉시 활용할 수 있는 전문 전략 리포트를 작성하세요.

    [주의 사항]
    - 반드시 '브론슨(Bronson)' 브랜드와 아메카지/밀리터리/워크웨어 시장에만 집중하세요.
    - '스르비'나 기타 여성복 관련 내용은 일절 언급하지 마세요.
    - 오디너리핏츠는 반드시 일본 브랜드 섹션으로 분류하세요.

    [보고서 필수 구조]
    1. MARKET OVERVIEW: 현재 아메카지 씬의 핵심 트렌드 정의.
    2. COMPETITOR ANALYSIS: 아웃스탠딩, 에스피오나지, 프리즘웍스의 주력 상품 및 소비자 반응.
    3. HERITAGE REFERENCE: RRL, 리얼맥코이 등 하이엔드 브랜드에서 포착된 디테일 인사이트.
    4. BRONSON'S NEXT STEP: 주완 MD가 이번 주에 실행해야 할 기획 및 마케팅 전략 3가지.

    매우 격식 있고 전문적인 비즈니스 문체를 사용하며, HTML 형식을 갖추어 작성하세요.
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 6. 브론슨 단독 브랜드 디자인 적용
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Bronson Strategic Intelligence Report</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            body {{ font-family: 'Pretendard', sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 40px 20px; }}
            .paper {{ max-width: 1000px; margin: auto; background: #ffffff; color: #222; padding: 60px; border-radius: 2px; box-shadow: 0 40px 80px rgba(0,0,0,0.5); }}
            .top-header {{ display: flex; justify-content: space-between; border-bottom: 4px solid #1a1a1a; padding-bottom: 10px; margin-bottom: 50px; }}
            .top-header .brand {{ font-size: 1.1em; font-weight: 900; letter-spacing: 3px; text-transform: uppercase; color: #1a1a1a; }}
            h1 {{ font-size: 3.2em; line-height: 1.1; margin: 30px 0; letter-spacing: -2.5px; color: #1a1a1a; font-weight: 800; }}
            .report-meta {{ color: #777; margin-bottom: 60px; font-size: 1em; border-left: 4px solid #c0392b; padding-left: 20px; }}
            .content h2 {{ font-size: 1.8em; margin-top: 60px; border-bottom: 2px solid #eee; padding-bottom: 15px; color: #c0392b; }}
            .content p, .content li {{ line-height: 1.9; font-size: 1.15em; color: #333; }}
            .action-plan {{ background: #f9f9f9; border: 1px solid #ddd; padding: 40px; margin: 50px 0; }}
            .footer {{ margin-top: 100px; text-align: center; color: #aaa; font-size: 0.85em; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <div class="paper">
            <div class="top-header">
                <div class="brand">Bronson Strategy Lab</div>
                <div class="date">NO. {now}</div>
            </div>
            <h1>BRONSON<br>WEEKLY INTELLIGENCE</h1>
            <div class="report-meta">
                FOR SENIOR MD JU-WAN / EXCLUSIVE CONFIDENTIAL
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                &copy; 2026 BRONSON INTELLIGENCE UNIT. ALL RIGHTS RESERVED.
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
