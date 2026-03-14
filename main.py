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

# 2. 유튜브 검색 결과 수집 (제목 위주)
def get_youtube_data(keyword):
    encoded_query = urllib.parse.quote(keyword)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        # 유튜브는 JS 기반이라 정규식으로 비디오 제목 데이터를 일부 추출합니다.
        titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]+)"\}', response.text)
        results = [t for t in titles if len(t) > 5][:5] # 너무 짧은 텍스트 제외
        return f"[YouTube '{keyword}' 관련 영상]: " + " / ".join(results)
    except:
        return ""

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

# 4. 데이터 취합 본부 (유튜브 포함)
def collect_data():
    target_keywords = [
        "아웃스탠딩", "에스피오나지", "프리즘웍스", "브론슨 의류", # 국내
        "리얼맥코이", "버즈릭슨", "더블알엘 RRL", "웨어하우스 복각", "오디너리핏츠", # 해외/일본
        "남자 아메카지 코디", "밀리터리 복각 자켓"
    ]
    all_info = []
    for kw in target_keywords:
        all_info.append(f"### [SOURCE: {kw}] ###")
        all_info.append(get_naver_search(kw, "shop"))
        all_info.append(get_naver_search(kw, "cafearticle")) # 고아캐드, 브랜디드 반응
        all_info.append(get_youtube_data(kw)) # 유튜브 트렌드
        all_info.append("\n")
    return "\n".join(all_info)

# 5. 시니어 MD 전략 보고서 생성
def generate_report(data):
    today = datetime.now()
    date_context = f"{(today - timedelta(days=7)).strftime('%Y/%m/%d')} - {today.strftime('%Y/%m/%d')}"
    
    prompt = f"""
    당신은 15년 차 시니어 패션 MD이자 브랜드 전략가입니다.
    다음 수집된 '유튜브 제목, 카페 게시글, 네이버 쇼핑 데이터'를 바탕으로 브론슨(Bronson) 팀원들에게 공유할 전문 보고서를 작성하세요.

    [수집된 원본 데이터]
    {data}

    [보고서 작성 가이드라인]
    1. 시장 지형 변화 (Global & Domestic): 경쟁 브랜드(에스피오나지 등)와 근본 브랜드(RRL 등)의 현재 시장 온도 차이를 분석하세요.
    2. 유튜브/커뮤니티 여론 해부: 유튜브에서 유행하는 키워드와 고아캐드/브랜디드에서 소비자들이 가장 많이 질문하는 '고민 사항'을 추출하세요.
    3. 상품 기획적 통찰: 단순 유행이 아닌, '어떤 소재와 어떤 실루엣'이 다음 주 판매를 견인할지 구체적으로 제안하세요.
    4. 브론슨(Bronson)을 위한 Critical Action: 주완 MD가 이번 주에 바로 실행해야 할 기획/마케팅 액션 3가지를 우선순위별로 제시하세요.

    오디너리핏츠는 일본 브랜드로 명확히 구분하고, 전문 비즈니스 문체를 사용하며 HTML 형식을 갖추어 작성하세요.
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 6. 전문가용 프리미엄 UI 디자인
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Bronson & Seureubi MD Strategy Insight</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            body {{ font-family: 'Pretendard', sans-serif; background-color: #1e1e1e; color: #e0e0e0; margin: 0; padding: 40px 20px; }}
            .paper {{ max-width: 1000px; margin: auto; background: #ffffff; color: #333; padding: 70px; border-radius: 4px; box-shadow: 0 30px 60px rgba(0,0,0,0.3); }}
            .top-bar {{ display: flex; justify-content: space-between; border-bottom: 3px solid #333; padding-bottom: 10px; margin-bottom: 50px; }}
            .top-bar .title {{ font-size: 0.9em; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; }}
            h1 {{ font-size: 3em; line-height: 1; margin: 20px 0; letter-spacing: -2px; color: #1a1a1a; }}
            .meta-info {{ color: #999; margin-bottom: 60px; font-size: 0.9em; }}
            .content h2 {{ font-size: 1.8em; margin-top: 50px; border-bottom: 1px solid #eee; padding-bottom: 15px; color: #c0392b; }}
            .content p, .content li {{ line-height: 1.8; font-size: 1.1em; color: #444; }}
            .highlight-box {{ background: #fdf2f2; border-left: 6px solid #c0392b; padding: 30px; margin: 40px 0; }}
            .footer {{ border-top: 1px solid #eee; margin-top: 100px; padding-top: 20px; text-align: center; color: #ccc; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div class="paper">
            <div class="top-bar">
                <div class="title">Bronson & Seureubi Strategy Lab</div>
                <div class="no">ISSUE NO. {now}</div>
            </div>
            <h1>WEEKLY<br>MARKET INTELLIGENCE</h1>
            <div class="meta-info">CONFIDENTIAL REPORT FOR MD TEAM</div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                본 보고서는 AI가 실시간 웹 데이터를 분석하여 생성한 브랜딩 전략 자료입니다.
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
