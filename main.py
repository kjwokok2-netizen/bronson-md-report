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
    print("에러: Gemini API 키를 찾을 수 없습니다.")
    exit()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 무신사 검색 데이터 (안전장치 유지)
def get_musinsa_data(keyword):
    url = f"https://www.musinsa.com/search/musinsa/goods?q={keyword}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('.article_info p.list_info a')
            results = [item.text.strip() for item in items[:3]]
            return f"[무신사 '{keyword}']: " + ", ".join(results) if results else ""
        return ""
    except:
        return ""

# 3. 네이버 API 통합 수집기
def get_naver_search(keyword, target="shop"):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return ""
    
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=3"
    
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request_obj)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            
            def clean_text(text):
                return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            
            results = []
            for item in data['items']:
                title = clean_text(item.get('title', ''))
                if target in ['blog', 'cafearticle']:
                    desc = clean_text(item.get('description', ''))
                    results.append(f"제목: {title} (내용: {desc[:50]}...)")
                else:
                    results.append(title)
                    
            return f"[네이버 {target} '{keyword}']: \n" + "\n".join(results)
        return ""
    except Exception:
        return ""

# 4. 전체 데이터 취합 본부 (하이엔드/근본 브랜드 대거 확장)
def collect_data():
    target_keywords = [
        # 1. 장르 핵심 키워드
        "남자 아메카지 코디", "남자 밀리터리 코디", "워크웨어 셋업",
        
        # 2. 하이엔드 오리지널 & 일본 복각 3대장 등
        "리얼맥코이", "토이즈맥코이", "버즈릭슨", 
        "더블알엘 RRL", "웨어하우스 복각", "풀카운트 데님",
        "오어슬로우", "엔지니어드가먼츠", "캡틴선샤인", "아나토미카",
        
        # 3. 국내 주요 레퍼런스 & 가성비 경쟁 브랜드
        "에스피오나지", "프리즘웍스", "반츠", "유니폼브릿지", 
        "네이머클로딩", "레드토네이도", "오디너리핏츠",
        
        # 4. 자사 모니터링
        "브론슨 의류", "브론슨 자켓"
    ]
    
    all_collected_info = []
    
    for kw in target_keywords:
        all_collected_info.append(f"--- 키워드: {kw} ---")
        all_collected_info.append(get_naver_search(kw, "shop"))
        all_collected_info.append(get_naver_search(kw, "blog"))
        all_collected_info.append(get_naver_search(kw, "cafearticle"))
        all_collected_info.append(get_musinsa_data(kw))
        all_collected_info.append("\n")
        
    return "\n".join(all_collected_info)

# 5. 리포트 생성 및 저장 로직
def generate_report(data):
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    date_context = f"{last_monday.strftime('%Y년 %m월 %d일')} ~ {last_sunday.strftime('%Y년 %m월 %d일')}"
    
    prompt = f"""
    현재 기준일: {today.strftime('%Y년 %m월 %d일')}
    
    [수집된 실제 원본 데이터: 쇼핑, 블로그, 카페 게시글 등]
    {data}
    
    너는 남성복 브랜드 '브론슨(Bronson)'과 여성복 브랜드 '스르비'의 수석 데이터 분석가야.
    제공된 원본 데이터를 바탕으로 '주완 MD'가 이번 시즌 신상품 기획 및 운영에 바로 써먹을 수 있는 경쟁사 및 하이엔드 레퍼런스 분석 리포트를 작성해.
    
    [필수 포함 항목]
    1. {date_context} 오리지널/하이엔드 브랜드 동향: 리얼맥코이, 버즈릭슨, RRL 등 하이엔드 브랜드에서 현재 커뮤니티 유저들이 주목하는 디테일이나 아이템 요약
    2. 국내 도메스틱 브랜드 동향: 에스피오나지, 프리즘웍스 등 국내 경쟁사들의 주력 상품 반응 요약
    3. 브론슨(Bronson) 기획 제안: 하이엔드 브랜드의 감성을 원하지만 가격 부담을 느끼는 소비자들을 위해 브론슨이 공략해야 할 '대체품(가성비+핏)' 기획 아이디어 TOP 3
    
    1. 불확실하거나 수집되지 않은 브랜드 데이터에 대해서는 임의로 답변하지 말고 '관련 데이터가 부족합니다'라고 명확히 기재해.
    2. 확실한 근거 없이 추측이 포함될 경우, '추측한 내용입니다'라고 밝혀.
    3. 객관적이며 전문성을 유지하도록 깔끔한 HTML 코드로 구성해.
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

def save_to_html(content):
    now = datetime.now().strftime('%Y-%m-%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bronson & Seureubi MD Trend Report</title>
        <style>
            body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background-color: #f8f9fa; padding: 40px; line-height: 1.6; color: #333; }}
            .container {{ max-width: 900px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
            h1 {{ color: #1a1a1a; border-left: 5px solid #2c3e50; padding-left: 15px; }}
            .date {{ color: #7f8c8d; margin-bottom: 30px; font-weight: bold; }}
            .content {{ background: #fdfdfd; padding: 25px; border-radius: 8px; border: 1px solid #eee; }}
            h2 {{ color: #2c3e50; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; font-size: 1.3em; }}
            li {{ margin-bottom: 12px; }}
            .highlight {{ background-color: #e8f4f8; padding: 10px; border-left: 4px solid #3498db; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>글로벌 & 도메스틱 아메카지 브랜드 심층 분석 리포트</h1>
            <p class="date">발행일: {now} (매주 월요일 자동 업데이트)</p>
            <div class="content">{content}</div>
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
