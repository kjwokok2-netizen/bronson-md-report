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

# 2. 무신사 데이터 수집 (방어형)
def get_musinsa_data(keyword):
    url = f"https://www.musinsa.com/search/musinsa/goods?q={keyword}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('.article_info p.list_info a')
            results = [item.text.strip() for item in items[:5]]
            if results:
                return f"[무신사 '{keyword}' 상위 상품]: " + ", ".join(results)
            else:
                return f"[무신사 '{keyword}']: 동적 렌더링 또는 봇 차단으로 데이터 읽기 실패."
        else:
            return f"[무신사 '{keyword}']: 서버 접근 실패 (코드: {response.status_code})"
    except Exception as e:
        return f"[무신사 '{keyword}']: 에러 발생 ({e})"

# 3. 네이버 쇼핑 API 데이터 수집 (실제 가동)
def get_naver_api_data(keyword):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return f"[네이버 쇼핑 '{keyword}']: API 키 누락으로 보류됨."
    
    encText = urllib.parse.quote(keyword)
    url = "https://openapi.naver.com/v1/search/shop.json?query=" + encText + "&display=5"
    
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request_obj)
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            data = json.loads(response_body.decode('utf-8'))
            # <b> 태그 제거 및 상품명 추출
            items = [item['title'].replace('<b>', '').replace('</b>', '') for item in data['items']]
            return f"[네이버 쇼핑 '{keyword}' 인기 검색]: " + ", ".join(items)
        else:
            return f"[네이버 쇼핑 '{keyword}']: 에러 발생 (상태 코드: {rescode})"
    except Exception as e:
        return f"[네이버 쇼핑 '{keyword}']: 호출 실패 ({e})"

# 4. 구글 트렌드 데이터 수집 (pytrends 라이브러리 활용)
def get_google_trends(keyword):
    try:
        from pytrends.request import TrendReq
        # 한국 지역 설정으로 구글 트렌드 접속
        pytrends = TrendReq(hl='ko-KR', tz=540)
        pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='KR', gprop='')
        related_queries = pytrends.related_queries()
        
        if keyword in related_queries and related_queries[keyword]['top'] is not None:
            top_queries = related_queries[keyword]['top']['query'].tolist()[:5]
            return f"[구글 트렌드 '{keyword}' 연관검색어]: " + ", ".join(top_queries)
        else:
            return f"[구글 트렌드 '{keyword}']: 유의미한 연관검색어 데이터가 부족합니다."
    except Exception as e:
        return f"[구글 트렌드 '{keyword}']: 수집 실패 (해외 IP 차단 가능성 등) - {e}"

# 5. 전체 데이터 취합 본부
def collect_data():
    target_keywords = ["아메카지", "밀리터리", "프레피"]
    all_collected_info = []
    
    for kw in target_keywords:
        all_collected_info.append(get_musinsa_data(kw))
        all_collected_info.append(get_naver_api_data(kw))
        all_collected_info.append(get_google_trends(kw))
        
    return "\n".join(all_collected_info)

# 6. 리포트 생성 및 저장 로직
def generate_report(data):
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    date_context = f"{last_monday.strftime('%Y년 %m월 %d일')} ~ {last_sunday.strftime('%Y년 %m월 %d일')}"
    
    prompt = f"""
    현재 기준일: {today.strftime('%Y년 %m월 %d일')}
    분석 대상 기간(지난주): {date_context}
    
    [수집된 실제 원본 데이터]
    {data}
    
    위 '수집된 실제 원본 데이터'를 최우선 근거로 삼아 패션 트렌드 리포트를 작성해줘. 
    만약 원본 데이터 수집이 에러/차단으로 인해 부족하다면, 부족한 부분은 AI의 지식으로 보완하되 "해당 내용은 데이터 수집 제한으로 인해 자체 분석한 내용입니다"라고 명시해. (근거 없는 임의 추측 금지)
    
    [필수 포함 항목]
    1. {date_context} 기준 브랜드별/키워드별 트렌드 요약
    2. 수집된 데이터를 바탕으로 한 세분화된 핵심 키워드 TOP 10 (출처 표기)
    3. 실무자를 위한 상품 기획 인사이트 제안
    
    브론슨과 스르비의 MD인 '주완'을 위한 형식으로 객관적이고 전문적으로 작성해.
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
            body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background-color: #f8f9fa; padding: 40px; line-height: 1.6; }}
            .container {{ max-width: 900px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
            h1 {{ color: #1a1a1a; border-left: 5px solid #2c3e50; padding-left: 15px; }}
            .date {{ color: #7f8c8d; margin-bottom: 30px; }}
            .content {{ background: #fdfdfd; padding: 20px; border-radius: 8px; border: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>통합 패션 트렌드 리포트</h1>
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
