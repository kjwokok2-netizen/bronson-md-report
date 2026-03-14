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
    # 무신사는 브랜드명 검색 시 결과가 다를 수 있어 일반 키워드 위주로 수집될 수 있습니다.
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

# 4. 전체 데이터 취합 본부 (브랜드 키워드 대거 투입)
def collect_data():
    # 주완 님의 기획 의도를 반영한 세분화된 키워드 리스트
    target_keywords = [
        # 카테고리 동향
        "남자 아메카지 코디", "남자 밀리터리 코디", 
        # 국내 레퍼런스/경쟁 브랜드
        "에스피오나지", "프리즘웍스", "반츠", "유니폼브릿지", "네이머클로딩",
        # 해외 레퍼런스/오리지널 브랜드
        "더블알엘 RRL", "웨어하우스 복각", "레드토네이도",
        # 자사 모니터링 (동명이인/영화 방지를 위한 튜닝)
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

# 5. 리포트 생성 및 저장 로직 (경쟁사 분석 프롬프트 적용)
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
    제공된 원본 데이터를 바탕으로 '주완 MD'가 이번 시즌 신상품 기획 및 운영에 바로 써먹을 수 있는 경쟁사 중심의 타겟 리포트를 작성해.
    
    [필수 포함 항목]
    1. {date_context} 레퍼런스 브랜드 동향: 에스피오나지, 프리즘웍스, 유니폼브릿지, RRL 등 타 브랜드의 현재 인기 아이템 및 소비자 반응(수집 데이터 기반)
    2. 시장 내 블루오션 아이템 발굴: 타 브랜드에서 많이 언급되지만 소비자가 아쉬워하는 점이나, 브론슨이 가성비/핏으로 대체할 수 있는 아이템 TOP 3
    3. 자사 브랜드(브론슨) 실무 기획 제안: 위 분석을 종합하여 주완 MD에게 제안하는 구체적인 이번 시즌 제작 아이템 및 마케팅(키워드) 전략
    
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
            <h1>경쟁사 및 레퍼런스 브랜드 심층 분석 리포트</h1>
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
