import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime

# 1. 설정: 깃허브 금고(Secrets)에서 안전하게 키를 가져옵니다.
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") 

if not GEMINI_KEY:
    print("에러: API 키를 찾을 수 없습니다. Secrets 설정을 확인하세요.")
    exit()

genai.configure(api_key=GEMINI_KEY)
# 구글의 최신 서비스 버전에 맞춘 모델 이름으로 변경 (핵심 수정!)
model = genai.GenerativeModel('gemini-2.5-flash')

def collect_data():
    # 실제 수집 로직의 요약 (무신사, 29CM, 커뮤니티 등)
    sources = "무신사/29CM 아메카지 베스트, 고아캐드/브랜디드 인기글, 인스타그램 #아메카지 #밀리터리룩 게시글"
    return sources

def generate_report(data):
    prompt = f"""
    정보 소스: {data}
    위 정보를 바탕으로 지난주(월~일) 패션 트렌드 리포트를 작성해줘.
    
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
