import os
import requests
import urllib.request
import urllib.parse
import json
import markdown
import google.generativeai as genai
from datetime import datetime, timedelta
try:
    from pytrends.request import TrendReq
except ImportError:
    pass

# 1. API 키 세팅
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") 
NAVER_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
YOUTUBE_KEY = os.environ.get("YOUTUBE_API_KEY")

if not GEMINI_KEY: exit()
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 데이터 수집 모듈 (네이버, 유튜브 정식 API, 구글 트렌드)
def get_naver_data(keyword, target="shop"):
    if not NAVER_ID or not NAVER_SECRET: return ""
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=20"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", NAVER_ID)
    req.add_header("X-Naver-Client-Secret", NAVER_SECRET)
    try:
        res = urllib.request.urlopen(req)
        if res.getcode() == 200:
            data = json.loads(res.read().decode('utf-8'))
            clean = lambda x: x.replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            return "\n".join([f"- {clean(i['title'])}: {clean(i.get('description', ''))[:80]}" for i in data['items']])
    except: return ""
    return ""

def get_youtube_data(keyword):
    if not YOUTUBE_KEY: return ""
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=10&q={urllib.parse.quote(keyword)}&type=video&regionCode=KR&key={YOUTUBE_KEY}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return "\n".join([f"- {item['snippet']['title']}" for item in data.get('items', [])])
    except: return ""
    return ""

def get_google_trends(keyword):
    try:
        pytrends = TrendReq(hl='ko-KR', tz=540)
        pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='KR')
        related = pytrends.related_queries()
        if keyword in related and related[keyword]['top'] is not None:
            top_queries = related[keyword]['top']['query'].tolist()[:10]
            return ", ".join(top_queries)
    except: return ""
    return ""

# 3. 전방위 크롤링 실행 (남/여 종합 패션)
def collect_all_data():
    queries = {
        "남성": ["남자 패션 트렌드", "20대 30대 남자 쇼핑몰", "남자 봄 코디", "남자 인기 브랜드"],
        "여성": ["여자 패션 트렌드", "20대 30대 여자 쇼핑몰", "여자 봄 코디", "여자 인기 브랜드"]
    }
    
    raw_data = []
    for gender, kw_list in queries.items():
        raw_data.append(f"\n========== [{gender} 패션 RAW DATA] ==========")
        for kw in kw_list:
            raw_data.append(f"\n[키워드: {kw}]")
            raw_data.append("--- 네이버 쇼핑/카페/블로그 ---")
            raw_data.append(get_naver_data(kw, "shop"))
            raw_data.append(get_naver_data(kw, "cafearticle"))
            raw_data.append(get_naver_data(kw, "blog"))
            raw_data.append("--- 유튜브 영상 제목 ---")
            raw_data.append(get_youtube_data(kw))
            raw_data.append("--- 구글 연관 검색어 ---")
            raw_data.append(get_google_trends(kw))
            
    return "\n".join(raw_data)

# 4. 리포트 생성 (정확한 Top 10 포맷 강제)
def generate_report(data):
    prompt = f"""
    당신은 대한민국 최고의 패션 데이터 분석가입니다.
    제공된 방대한 크롤링 데이터(네이버, 유튜브, 구글 트렌드)를 분석하여, 언급량과 트렌드 지수가 가장 높은 항목들을 추출하세요.

    [작성 규칙 - 반드시 지킬 것]
    1. 서론, 결론, 인사말 등 쓸데없는 말은 일절 생략하고 오직 아래의 마크다운 형식만 정확하게 출력하세요.
    2. 데이터가 부족하더라도 AI의 패션 도메인 지식을 활용하여 반드시 순위를 1위부터 10위까지 채우세요.
    3. 아래 양식의 헤딩(##, ###)과 리스트(1. 2. 3.) 포맷을 절대 변경하지 마세요.

    [출력 양식]
    ## 👱‍♂️ [남성] 주간 패션 트렌드 랭킹

    ### 🏆 검색량 높은 브랜드 TOP 10
    1. 
    2. 
    (10까지 작성)

    ### 🔑 검색량 높은 키워드 TOP 10
    1. 
    2. 
    (10까지 작성)

    ### 👕 검색량 높은 제품 TOP 10
    1. 
    2. 
    (10까지 작성)

    ---

    ## 👩‍🦰 [여성] 주간 패션 트렌드 랭킹

    ### 🏆 검색량 높은 브랜드 TOP 10
    1. 
    2. 
    (10까지 작성)

    ### 🔑 검색량 높은 키워드 TOP 10
    1. 
    2. 
    (10까지 작성)

    ### 👗 검색량 높은 제품 TOP 10
    1. 
    2. 
    (10까지 작성)

    [원본 데이터]
    {data}
    """
    response = model.generate_content(prompt)
    return response.text

# 5. 대시보드 UI (랭킹보드 최적화)
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_content = markdown.markdown(content)
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weekly Fashion Trend Ranking</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            :root {{ --bg: #f0f2f5; --card: #ffffff; --text: #1c1e21; --accent: #1877f2; --border: #e4e6eb; }}
            body {{ font-family: 'Pretendard', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 40px 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            
            /* Header */
            .header-box {{ background: var(--card); padding: 40px; border-radius: 16px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.04); margin-bottom: 40px; border-top: 6px solid #1a1a1a; }}
            .header-box h1 {{ margin: 0 0 10px 0; font-size: 2.5em; letter-spacing: -1px; font-weight: 800; }}
            .header-box .date {{ color: #65676b; font-weight: 600; font-size: 1.1em; }}

            /* Content Grid */
            .dashboard-content {{ display: flex; flex-direction: column; gap: 40px; }}
            
            /* Markdown Styling for Ranking Boards */
            .dashboard-content h2 {{ text-align: center; font-size: 2em; margin: 40px 0 20px 0; padding-bottom: 15px; border-bottom: 3px solid #1a1a1a; }}
            .dashboard-content h3 {{ color: var(--accent); font-size: 1.4em; margin-top: 30px; margin-bottom: 15px; display: flex; align-items: center; }}
            .dashboard-content ol {{ background: var(--card); padding: 30px 30px 30px 50px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); margin: 0; border: 1px solid var(--border); }}
            .dashboard-content li {{ padding: 12px 0; border-bottom: 1px solid #f1f1f1; font-size: 1.15em; font-weight: 500; color: #333; }}
            .dashboard-content li:last-child {{ border-bottom: none; padding-bottom: 0; }}
            
            hr {{ border: 0; border-bottom: 2px dashed #ccc; margin: 60px 0; }}
            
            /* Responsive layout for side-by-side lists if needed */
            @media(min-width: 1024px) {{
                .dashboard-content {{ display: block; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-box">
                <h1>주간 패션 트렌드</h1>
                <div class="date">DATA COMPILED: {now}</div>
            </div>
            <div class="dashboard-content">
                {html_content}
            </div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    raw_info = collect_all_data()
    report_text = generate_report(raw_info)
    save_to_html(report_text)
