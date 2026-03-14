import os
import requests
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

# 2. 데이터 수집 모듈 A: 무신사 크롤링 시도 (오류 방어형)
def get_musinsa_data(keyword):
    url = f"https://www.musinsa.com/search/musinsa/goods?q={keyword}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 참고: 무신사 HTML 구조 변경 또는 봇 차단 시 빈 값이 나올 수 있음 (추측성 수집)
            items = soup.select('.article_info p.list_info a')
            results = [item.text.strip() for item in items[:5]]
            
            if results:
                return f"[무신사 '{keyword}' 상위 노출]: " + ", ".join(results)
            else:
                return f"[무신사 '{keyword}']: 크롤링이 차단되었거나 스크립트 렌더링으로 인해 데이터를 읽을 수 없습니다."
        else:
            return f"[무신사 '{keyword}']: 서버 접근 실패 (상태 코드: {response.status_code})"
    except Exception as e:
        return f"[무신사 '{keyword}']: 연결 에러 발생 ({e})"

# 3. 데이터 수집 모듈 B: 네이버 검색 API (키 확인형)
def get_naver_api_data(keyword):
    # 깃허브 Secrets에서 네이버 전용 열쇠를 찾습니다.
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return f"[네이버 쇼핑/검색 '{keyword}']: 보류됨. (이유: GitHub Secrets에 네이버 API 키가 등록되지 않았습니다.)"
    
    # 향후 네이버 키가 등록되면 작동할 실제 API 로직 공간
    return f"[네이버 '{keyword}']: API 연동 준비 완료."

# 4. 전체 데이터 취합 본부
def collect_data():
    target_keywords = ["아메카지", "밀리터리", "프레피"]
    all_collected_info = []
    
    for kw in target_keywords:
        all_collected_info.append(get_musinsa_data(kw))
        all_collected_info.append(get_naver_api_data(kw))
        
    return "\n".join(all_collected_info)

# 5. 리포트 생성 및 저장 로직
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
    2. 수집된 데이터를 바탕으로 한 세분화된 핵심 키워드 TOP 10
    3. 실무자를 위한 상품 기획 인사이트 제안
    
    브론슨과 스르비의 MD인 '주완'을 위한 형식으로 깔끔하게 작성해.
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
