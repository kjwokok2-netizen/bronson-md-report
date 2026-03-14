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
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=5"
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request_obj)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            clean = lambda x: x.replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            return "\n".join([f"- {clean(i['title'])}: {clean(i.get('description', ''))[:60]}" for i in data['items']])
    except: return ""
    return ""

# 3. 데이터 취합 (브랜드 타겟팅 정밀화)
def collect_data():
    target_keywords = [
        "아웃스탠딩", "에스피오나지", "프리즘웍스", "브론슨 의류", # 국내 4대장
        "리얼맥코이", "버즈릭슨", "웨어하우스 복각", "오어슬로우", "오디너리핏츠", # 해외/일본
        "더블알엘 RRL", "남자 아메카지 코디", "밀리터리 복각 자켓"
    ]
    all_info = []
    for kw in target_keywords:
        all_info.append(f"### [KEYWORD: {kw}] ###")
        all_info.append(get_naver_search(kw, "shop"))
        all_info.append(get_naver_search(kw, "blog"))
        all_info.append(get_naver_search(kw, "cafearticle"))
    return "\n".join(all_info)

# 4. 고도화된 전략 리포트 생성 (MD 전용 프롬프트)
def generate_report(data):
    today = datetime.now()
    date_context = f"{(today - timedelta(days=7)).strftime('%Y/%m/%d')} - {today.strftime('%Y/%m/%d')}"
    
    prompt = f"""
    당신은 글로벌 패션 트렌드 분석가이자 '브론슨(Bronson)'의 수석 브랜드 매니저입니다.
    다음 원본 데이터를 바탕으로 현업 MD들이 신상품 기획 회의에서 즉시 활용할 수 있는 수준의 '심층 트렌드 분석 리포트'를 작성하세요.

    [데이터 소스]
    {data}

    [작성 가이드라인]
    1. 시장 지형도: 국내 도메스틱(아웃스탠딩, 에스피오나지, 프리즘웍스, 브론슨)과 해외/일본 브랜드(맥코이, 웨어하우스, RRL, 오디너리핏츠 등)의 동향을 엄격히 분리하여 분석할 것.
    2. 마이크로 트렌드 포착: 데이터에서 반복적으로 언급되는 '소재(예: 헤링본, 몰스킨)', '디테일(예: 핀락 지퍼, 튜블러)', '핏(예: 릴렉스 스트레이트)'을 구체적으로 추출할 것.
    3. 소비자 결핍 분석: 카페나 블로그에서 소비자들이 아쉬워하는 점(가격, 사이즈 품절, 내구성 등)을 찾아내어 브론슨의 기회 요소로 전환할 것.
    4. MD's Decision: 브론슨 기획팀이 이번 주에 당장 착수해야 할 샘플링 리스트 3가지를 제안할 것.

    [어투]
    - 매우 전문적이고 분석적이며, 격식 있는 비즈니스 문체를 사용할 것.
    - 불확실한 데이터는 '추측'임을 명시하고 근거를 제시할 것.
    - 결과물은 시각적으로 구조화된 HTML 코드로 출력할 것.
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 5. 전문가용 UI 적용 HTML 템플릿
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Bronson & Seureubi Strategy Report</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            body {{ font-family: 'Pretendard', sans-serif; background-color: #f4f4f2; color: #1a1a1a; margin: 0; padding: 50px 20px; }}
            .report-card {{ max-width: 1000px; margin: auto; background: #ffffff; padding: 60px; border-radius: 4px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-top: 8px solid #2c3e50; }}
            .header {{ border-bottom: 1px solid #eee; padding-bottom: 30px; margin-bottom: 40px; }}
            .header h1 {{ font-size: 2.2em; letter-spacing: -1px; margin: 0; color: #2c3e50; }}
            .header .meta {{ color: #888; margin-top: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }}
            .content h2 {{ font-size: 1.5em; border-left: 4px solid #c0392b; padding-left: 15px; margin: 40px 0 20px; }}
            .content p, .content li {{ line-height: 1.8; font-size: 1.05em; color: #444; }}
            .md-action {{ background: #f9f9f9; border: 1px dashed #ddd; padding: 25px; margin-top: 40px; border-radius: 8px; }}
            .md-action h3 {{ margin-top: 0; color: #c0392b; font-size: 1.2em; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 15px; border-bottom: 1px solid #eee; text-align: left; }}
            th {{ background: #f8f9fa; color: #666; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="report-card">
            <div class="header">
                <h1>WEEKLY STRATEGY REPORT</h1>
                <div class="meta">Bronson & Seureubi MD Intelligence / {now} Issued</div>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="md-action">
                <h3>※ MD's Final Decision Note</h3>
                <p>본 리포트는 네이버 쇼핑/블로그/카페 및 구글 트렌드의 실시간 데이터를 Gemini 2.5 Flash 모델이 분석한 결과입니다. 브랜드 내부 기획 회의 시 참고 자료로 활용하시기 바랍니다.</p>
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
