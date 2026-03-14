import os
import requests
import urllib.request
import urllib.parse
import json
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

# 2. 데이터 수집 모듈 (네이버 & 무신사 통합)
def get_naver_search(keyword, target="shop"):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id: return ""
    
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=8" # 수집량 증대
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request_obj)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            clean = lambda x: x.replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&#39;', "'")
            return "\n".join([f"- {clean(i['title'])}: {clean(i.get('description', ''))}" for i in data['items']])
    except: return ""
    return ""

# 3. 데이터 취합 (정밀 타겟팅)
def collect_data():
    target_keywords = [
        "아웃스탠딩 코디", "에스피오나지 자켓", "프리즘웍스 팬츠", "브론슨 의류 품질", # 국내 실질 반응
        "리얼맥코이 A-2", "버즈릭슨 치노", "웨어하우스 1101", "오어슬로우 105", "오디너리핏츠 앵클", # 해외 디테일
        "더블알엘 RRL 스타일", "남자 아메카지 코디 추천", "밀리터리 복각 브랜드 비교"
    ]
    all_info = []
    for kw in target_keywords:
        all_info.append(f"### [RAW DATA: {kw}] ###")
        all_info.append(get_naver_search(kw, "shop"))
        all_info.append(get_naver_search(kw, "blog"))
        all_info.append(get_naver_search(kw, "cafearticle"))
    return "\n".join(all_info)

# 4. 고도화된 전략 리포트 생성 (시니어 MD 페르소나 주입)
def generate_report(data):
    today = datetime.now()
    date_context = f"{(today - timedelta(days=7)).strftime('%Y/%m/%d')} - {today.strftime('%Y/%m/%d')}"
    
    prompt = f"""
    당신은 패션 업계 15년 차 시니어 MD이자 브랜드 전략 컨설턴트입니다. 
    제공된 데이터는 지난 7일간의 아메카지/밀리터리 시장의 실시간 데이터입니다. 
    이 데이터를 바탕으로 '브론슨(Bronson)'의 경영진과 기획팀이 감탄할 만한 '주간 전략 보고서'를 작성하세요.

    [데이터 소스]
    {data}

    [보고서 필수 구조 및 내용]
    1. EXECUTIVE SUMMARY: 이번 주 시장의 핵심 흐름을 한 문장으로 정의하고, 가장 주목해야 할 브랜드 1곳을 선정하세요.
    2. 브랜드별 심층 분석 (HERITAGE vs DOMESTIC):
       - 일본/해외 브랜드(맥코이, RRL 등)에서 현재 소비자들이 열광하는 '오리지널리티 디테일'이 무엇인지 분석하세요.
       - 국내 경쟁사(아웃스탠딩, 에스피오나지, 프리즘웍스)가 현재 밀고 있는 주력 아이템과 소비자들의 실제 구매 만족도/불만 사항을 대조하세요.
    3. 실무 기획 인사이트 (FABRIC & SILHOUETTE):
       - 데이터에 언급된 소재(예: 정글클로스, 샴브레이 등)와 실루엣(예: 와이드, 테이퍼드)의 변화를 포착하세요.
    4. BRONSON'S ACTION PLAN:
       - '주완 MD'가 이번 주 샘플실에 지시하거나 마케팅팀과 논의해야 할 구체적인 아이템 3가지를 우선순위별로 제안하세요.

    [작성 원칙]
    - 오디너리핏츠는 반드시 '일본 브랜드' 섹션에서 다룰 것.
    - 데이터에 기반하지 않은 막연한 유행어 사용을 지양하고, 실제 블로그/카페의 반응(VOC)을 인용할 것.
    - 한국어 비즈니스 문체로 작성하며, HTML 태그를 사용하여 가독성 있게 구성할 것.
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 5. 전문가용 디자인 적용 HTML
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Bronson & Seureubi Weekly Intelligence</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            body {{ font-family: 'Pretendard', sans-serif; background-color: #f1f2f6; color: #2f3542; margin: 0; padding: 40px 20px; }}
            .wrapper {{ max-width: 1100px; margin: auto; background: white; padding: 60px; border-radius: 2px; box-shadow: 0 20px 50px rgba(0,0,0,0.1); border-top: 10px solid #2f3542; }}
            .report-header {{ border-bottom: 2px solid #2f3542; padding-bottom: 20px; margin-bottom: 50px; display: flex; justify-content: space-between; align-items: flex-end; }}
            .report-header h1 {{ font-size: 2.5em; margin: 0; letter-spacing: -1.5px; text-transform: uppercase; }}
            .report-header .date {{ font-weight: 700; color: #747d8c; letter-spacing: 1px; }}
            .section {{ margin-bottom: 60px; }}
            .section h2 {{ font-size: 1.6em; background: #2f3542; color: white; padding: 10px 20px; display: inline-block; margin-bottom: 25px; border-radius: 0 15px 15px 0; }}
            .section p, .section li {{ font-size: 1.1em; line-height: 1.9; color: #57606f; }}
            .insight-box {{ background: #f8f9fa; border-left: 5px solid #ff4757; padding: 30px; margin: 30px 0; border-radius: 4px; }}
            .insight-box h4 {{ margin-top: 0; color: #ff4757; font-size: 1.2em; }}
            strong {{ color: #2f3542; }}
            hr {{ border: 0; border-top: 1px solid #eee; margin: 40px 0; }}
            .footer {{ text-align: center; color: #ced4da; font-size: 0.9em; margin-top: 80px; }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="report-header">
                <h1>Strategic Intelligence</h1>
                <div class="date">ISSUE NO. {now}</div>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                &copy; 2026 Bronson & Seureubi Brand Strategy Lab. All Rights Reserved.
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
