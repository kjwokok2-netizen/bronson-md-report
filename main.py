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
# 최신 작동 모델 확인 완료
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 무신사 검색 데이터 수집
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

# 3. 네이버 API 통합 수집기 (쇼핑, 블로그, 카페)
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
    except:
        return ""

# 4. 전체 데이터 취합 본부 (주완 MD 요청 브랜드 리스트 반영)
def collect_data():
    target_keywords = [
        # 1. 국내 핵심 도메스틱 (브론슨 포함 4대장)
        "아웃스탠딩", "에스피오나지", "프리즘웍스", "브론슨 의류",
        
        # 2. 일본 복각 및 해외 근본 브랜드 (오디너리핏츠 국적 정정 완료)
        "리얼맥코이", "버즈릭슨", "더블알엘 RRL", "웨어하우스 복각", 
        "오어슬로우", "오디너리핏츠", "엔지니어드가먼츠", "캡틴선샤인",
        
        # 3. 카테고리 트렌드
        "남자 아메카지 코디", "남자 밀리터리 자켓"
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

# 5. 리포트 생성 (엄격한 국적 구분 프롬프트 적용)
def generate_report(data):
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    date_context = f"{last_monday.strftime('%Y년 %m월 %d일')} ~ {last_sunday.strftime('%Y년 %m월 %d일')}"
    
    prompt = f"""
    현재 기준일: {today.strftime('%Y년 %m월 %d일')}
    
    [수집된 실제 원본 데이터]
    {data}
    
    너는 '브론슨(Bronson)'의 수석 데이터 분석가야. 주완 MD를 위한 리포트를 작성해.
    
    [분석 지침 - 반드시 엄수할 것]
    1. 국내 브랜드 분석 섹션: 반드시 '아웃스탠딩', '에스피오나지', '프리즘웍스', '브론슨'의 데이터만 활용하여 국내 동향을 요약해.
    2. 해외 브랜드 분석 섹션: 리얼맥코이, 버즈릭슨, RRL, 오디너리핏츠 등은 '해외/일본 브랜드 레퍼런스'로 명확히 구분해. (오디너리핏츠를 절대 국내 브랜드로 분류하지 마.)
    3. 실무 제안: 경쟁사 3곳(아웃스탠딩, 에스피오나지, 프리즘웍스) 대비 브론슨이 가져갈 수 있는 기획 우위 포인트를 제안해.
    
    전문적이고 깔끔한 HTML 코드로 작성해줘.
    """
    response = model.generate_content(prompt)
    return response.text.replace('```html', '').replace('```', '')

# 6. HTML 저장
def save_to_html(content):
    now = datetime.now().strftime('%Y-%m-%d')
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bronson & Seureubi MD Report</title>
        <style>
            body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background-color: #f8f9fa; padding: 40px; line-height: 1.6; color: #333; }}
            .container {{ max-width: 900px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
            h1 {{ color: #1a1a1a; border-left: 5px solid #2c3e50; padding-left: 15px; }}
            .content {{ background: #fdfdfd; padding: 25px; border-radius: 8px; border: 1px solid #eee; }}
            h2 {{ color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; font-size: 1.3em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>국내외 아메카지 시장 분석 리포트</h1>
            <p>발행일: {now}</p>
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
