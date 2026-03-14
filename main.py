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
            return f"[무신사 '{keyword}' 상품]: " + ", ".join(results) if results else ""
        return ""
    except:
        return ""

# 3. 네이버 API 통합 수집기 (쇼핑, 블로그, 카페글 모두 수집)
def get_naver_search(keyword, target="shop"):
    """target 종류: shop(쇼핑), blog(블로그), cafearticle(카페게시글)"""
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return f"[네이버 {target} '{keyword}']: API 키 누락"
    
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=3"
    
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request_obj)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            
            # HTML 태그(<b>, </b>, &quot;) 깔끔하게 제거
            def clean_text(text):
                return text.replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            
            results = []
            for item in data['items']:
                title = clean_text(item.get('title', ''))
                # 블로그와 카페는 내용(description)도 함께 수집하여 소비자 반응 파악
                if target in ['blog', 'cafearticle']:
                    desc = clean_text(item.get('description', ''))
                    results.append(f"제목: {title} (내용: {desc[:50]}...)")
                else:
                    results.append(title)
                    
            return f"[네이버 {target} '{keyword}']: \n" + "\n".join(results)
        return ""
    except Exception as e:
        return f"[네이버 {target} '{keyword}']: 에러({e})"

# 4. 전체 데이터 취합 본부 (키워드 튜닝 완료)
def collect_data():
    # 뾰족하게 정제된 실무형 키워드들 (만년필 등 노이즈 차단)
    target_keywords = ["남자 아메카지 코디", "남자 밀리터리 자켓", "워크웨어 팬츠", "남자 프레피룩 코디"]
    
    all_collected_info = []
    
    for kw in target_keywords:
        all_collected_info.append(f"--- 키워드: {kw} ---")
        all_collected_info.append(get_naver_search(kw, "shop"))         # 쇼핑 랭킹
        all_collected_info.append(get_naver_search(kw, "blog"))         # 블로그 리뷰/코디
        all_collected_info.append(get_naver_search(kw, "cafearticle"))  # 카페 질문/반응
        all_collected_info.append(get_musinsa_data(kw))                 # 무신사
        all_collected_info.append("\n")
        
    return "\n".join(all_collected_info)

# 5. 리포트 생성 및 저장 로직 (브론슨 맞춤형 프롬프트)
def generate_report(data):
    today = datetime.now()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    date_context = f"{last_monday.strftime('%Y년 %m월 %d일')} ~ {last_sunday.strftime('%Y년 %m월 %d일')}"
    
    prompt = f"""
    현재 기준일: {today.strftime('%Y년 %m월 %d일')}
    
    [수집된 실제 원본 데이터: 쇼핑, 블로그 코디, 카페 게시글 등]
    {data}
    
    너는 남성복 브랜드 '브론슨(Bronson)'과 여성복 브랜드 '스르비'의 수석 데이터 분석가야.
    제공된 원본 데이터를 바탕으로 '주완 MD'가 이번 시즌 신상품 기획 및 운영에 바로 써먹을 수 있는 아주 실무적인 트렌드 리포트를 작성해.
    
    [필수 포함 항목]
    1. {date_context} 커뮤니티 및 블로그 반응 요약 (소비자들이 코디할 때 어떤 핏/소재/아이템을 찾고 있는지)
    2. 떠오르는 세부 아이템 키워드 TOP 5 (예: 일반 치노팬츠가 아니라 '벌룬핏 치노팬츠'처럼 구체적으로)
    3. 브론슨(Bronson) 브랜드를 위한 신상품 기획 제안 (데이터에 기반하여 어떤 옷을 만들면 좋을지 제안)
    
    추측성 내용은 배제하고, 반드시 주어진 데이터(카페 질문, 블로그 리뷰 내용 등)를 근거로 작성해.
    전문적이고 깔끔한 HTML 코드로 반환해.
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
            h2 {{ color: #2c3e50; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
            li {{ margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>커뮤니티 기반 실무 트렌드 리포트</h1>
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
