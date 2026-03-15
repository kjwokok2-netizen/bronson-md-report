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

# 2. 데이터 수집 모듈
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
        "남성": ["남자 패션 트렌드", "20대 30대 남자 쇼핑몰", "남자 봄 코디", "남자 인기 브랜드", "남자 아우터 추천"],
        "여성": ["여자 패션 트렌드", "20대 30대 여자 쇼핑몰", "여자 봄 코디", "여자 인기 브랜드", "여자 아우터 추천"]
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

# 4. 리포트 생성 (전환율/인사이트/동향 분석 강제)
def generate_report(data):
    today = datetime.now()
    prompt = f"""
    당신은 최고 수준의 패션 데이터 분석가이자 시니어 MD입니다.
    제공된 방대한 크롤링 데이터(네이버, 유튜브, 구글 트렌드)를 바탕으로, 기획 실무에 즉시 적용할 수 있는 전략 리포트를 작성하세요.

    [작성 규칙 - 절대 엄수]
    1. 쓸데없는 서론/결론 금지. 
    2. 보고서 형식이므로 '습니다'체 절대 사용 금지. 철저한 개조식(~함, ~임, ~확인됨, ~필요)으로 작성.
    3. 단순 랭킹 나열은 금지. 전주 대비 트렌드 변화(급상승, 신규 진입 등)를 분석하고, "왜 이게 떴는지", "어떻게 기획에 녹일지(소재, 핏, 소구점)"에 대한 [💡 MD Insight]를 반드시 포함할 것.
    4. 출력 양식의 헤딩(##, ###)과 포맷을 완벽하게 따를 것.

    [출력 양식]
    ## 📊 주간 패션 시장 종합 동향 (Market Overview)
    > (데이터를 관통하는 이번 주 남/여성 패션의 가장 큰 흐름과 전주 대비 가장 두드러진 변화점 2~3줄 요약)

    ---

    ## 👱‍♂️ [남성] 주간 트렌드 분석 & 액션 플랜

    ### 🏆 급상승 브랜드 TOP 10 (검색량 기반)
    1. 브랜드명 (🔺급상승 원인 한 줄 요약)
    2. 브랜드명 (🆕신규 진입 원인 한 줄 요약)
    ... (10위까지 작성)

    ### 🔑 핵심 반응 키워드 TOP 10
    1. 키워드 
    ... (10위까지 작성)

    ### 👕 주목해야 할 라이징 아이템 TOP 10 & 기획 인사이트
    1. 아이템명
    2. 아이템명
    ... (10위까지 작성)
    
    **💡 MD Insight (남성복 기획 적용점):** - (위 데이터에서 뽑아낸 구체적인 기획 제안 1 - 예: 특정 원단의 수요 증가, 아우터 두께감 변화 등)
    - (구체적인 기획 제안 2 - 타겟층의 결핍 포인트 공략법)

    ---

    ## 👩‍🦰 [여성] 주간 트렌드 분석 & 액션 플랜

    ### 🏆 급상승 브랜드 TOP 10 (검색량 기반)
    1. 브랜드명 (🔺급상승 원인 한 줄 요약)
    2. 브랜드명 (🆕신규 진입 원인 한 줄 요약)
    ... (10위까지 작성)

    ### 🔑 핵심 반응 키워드 TOP 10
    1. 키워드
    ... (10위까지 작성)

    ### 👗 주목해야 할 라이징 아이템 TOP 10 & 기획 인사이트
    1. 아이템명
    2. 아이템명
    ... (10위까지 작성)
    
    **💡 MD Insight (여성복 기획 적용점):**
    - (위 데이터에서 뽑아낸 구체적인 기획 제안 1)
    - (구체적인 기획 제안 2)

    [원본 데이터]
    {data}
    """
    response = model.generate_content(prompt)
    return response.text

# 5. 대시보드 UI (인사이트 강조 디자인)
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    html_content = markdown.markdown(content)
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fashion Intelligence Report</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            :root {{ --bg: #f4f5f7; --card: #ffffff; --text: #202124; --accent: #2962ff; --highlight: #e8f0fe; --border: #dadce0; }}
            body {{ font-family: 'Pretendard', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 40px 20px; }}
            .container {{ max-width: 1100px; margin: 0 auto; }}
            
            /* Header */
            .header-box {{ background: var(--text); color: #fff; padding: 40px 50px; border-radius: 12px; margin-bottom: 40px; display: flex; justify-content: space-between; align-items: flex-end; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header-box h1 {{ margin: 0; font-size: 2.2em; letter-spacing: -1px; font-weight: 800; }}
            .header-box .date {{ font-weight: 600; font-size: 1em; opacity: 0.8; }}

            /* Dashboard Content */
            .dashboard-content {{ background: var(--card); padding: 50px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); border: 1px solid var(--border); }}
            
            /* Markdown Styling */
            .dashboard-content h2 {{ color: var(--text); font-size: 1.8em; margin: 50px 0 20px 0; padding-bottom: 15px; border-bottom: 2px solid var(--text); }}
            .dashboard-content h2:first-child {{ margin-top: 0; }}
            .dashboard-content h3 {{ color: var(--accent); font-size: 1.3em; margin-top: 40px; margin-bottom: 15px; }}
            
            /* Overviews & Insights Box */
            blockquote {{ margin: 0 0 30px 0; padding: 25px 30px; background: #fff8e1; border-left: 6px solid #ffc107; border-radius: 0 8px 8px 0; font-size: 1.15em; line-height: 1.7; color: #5d4037; font-weight: 500; }}
            p:has(strong:contains("MD Insight")) {{ background: var(--highlight); padding: 30px; border-radius: 8px; border: 1px solid #c6dafc; margin-top: 30px; line-height: 1.8; font-size: 1.1em; color: #174ea6; }}
            
            /* Lists */
            .dashboard-content ol, .dashboard-content ul {{ padding-left: 20px; line-height: 1.8; font-size: 1.1em; color: #3c4043; }}
            .dashboard-content li {{ margin-bottom: 8px; }}
            
            hr {{ border: 0; border-bottom: 1px solid var(--border); margin: 60px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-box">
                <div>
                    <div style="font-size: 0.9em; letter-spacing: 2px; color: #9aa0a6; margin-bottom: 10px;">STRATEGIC MD REPORT</div>
                    <h1>WEEKLY TREND & ACTION PLAN</h1>
                </div>
                <div class="date">DATA EXTRACTED: {now}</div>
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
