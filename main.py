import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime, timedelta # timedelta(날짜 계산 도구) 추가

# 1. 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") 

if not GEMINI_KEY:
    print("에러: API 키를 찾을 수 없습니다. Secrets 설정을 확인하세요.")
    exit()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def collect_data():
    # 실제 수집 로직의 요약 (무신사, 29CM, 커뮤니티 등)
    sources = "무신사/29CM 아메카지 베스트, 고아캐드/브랜디드 인기글, 인스타그램 #아메카지 #밀리터리룩 게시글"
    return sources

def generate_report(data):
    # 오늘 날짜를 기준으로 '지난주 월요일~일요일' 날짜를 정확히 계산
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    date_context = f"{last_monday.strftime('%Y년 %m월 %d일')} ~ {last_sunday.strftime('%Y년 %m월 %d일')}"
    
    # AI에게 정확한 날짜를 지시하는 프롬프트로 수정
    prompt = f"""
    현재 기준일: {today.strftime('%Y년 %m월 %d일')}
    분석 대상 기간(지난주): {date_context}
    정보 소스: {data}
    
    위 정보를 바탕으로 반드시 '분석 대상 기간({date_context})'에 해당하는 패션 트렌드 리포트를 작성해줘. 
    보고서 본문의 날짜는 무작위로 지어내지 말고, 제공된 기간을 정확히 명시해야 해.
    
    [필수 포함 항목]
    1. 아메카지 관련 키워드 TOP 10
    2. 아메카지 관련 제품 TOP 10
    3. 전체 패션 관련 키워드 TOP 10
    4. 전체 패션 관련 제품 TOP 10
    
    브론슨과 스르비의 MD인 '주완'을 위한 전문적인 리포트 형식이어야 해.
    결과물은 HTML 코드 안에 들어갈 내용이므로 깔끔하게 작성해줘.
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
            <h1>주간 패션 트렌드 리포트</h1>
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
    report_text = generate_report(raw_info)
    save_to_html(report_text)
