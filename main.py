import os
import requests
import urllib.request
import urllib.parse
import json
import re
import markdown
import google.generativeai as genai
from datetime import datetime, timedelta

# 1. Gemini API 세팅
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") 
if not GEMINI_KEY: exit()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 데이터 수집 (외부 시장 팩트만 수집)
def get_naver_search(keyword, target="cafearticle"):
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id: return ""
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/{target}.json?query={encText}&display=20"
    request_obj = urllib.request.Request(url)
    request_obj.add_header("X-Naver-Client-Id", client_id)
    request_obj.add_header("X-Naver-Client-Secret", client_secret)
    try:
        response = urllib.request.urlopen(request_obj)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            clean = lambda x: x.replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            return "\n".join([f"- {clean(i['title'])}: {clean(i.get('description', ''))[:100]}" for i in data['items']])
    except: return ""
    return ""

def collect_data():
    # 기획에 필요한 진짜 타겟 키워드만 선별
    queries = [
        "남자 아메카지 트렌드", "밀리터리 자켓 핏", "워크웨어 팬츠 원단",
        "아웃스탠딩 사이즈", "에스피오나지 후기", "프리즘웍스 아쉬운점", 
        "리얼맥코이 버즈릭슨 대체", "RRL 가격", "웨어하우스 데님", "오어슬로우 오디너리핏츠 비교"
    ]
    raw_data = []
    for q in queries:
        raw_data.append(f"[{q}] 검색 결과:\n" + get_naver_search(q, "cafearticle"))
    return "\n".join(raw_data)

# 3. MD 맞춤형 리포트 생성 (가독성과 전략 중심)
def generate_report(data):
    today = datetime.now()
    w_start = (today - timedelta(days=7)).strftime('%m/%d')
    w_end = today.strftime('%m/%d')
    
    prompt = f"""
    당신은 패션 브랜드 '브론슨(Bronson)'의 시니어 전략 MD입니다. 
    아래 수집된 {w_start}~{w_end} 기간의 커뮤니티 데이터를 바탕으로, 기획팀이 즉시 참고할 수 있는 가장 실무적인 마크다운(Markdown) 리포트를 작성하세요.

    [작성 규칙 - 반드시 지킬 것]
    1. 군더더기 서론/결론, 인사말, 수신/발신 일절 생략. 바로 본론으로 들어갈 것.
    2. '습니다'체 사용 금지. 철저한 보고서 형식의 개조식(~함, ~임, ~확인됨) 사용.
    3. 아래의 3가지 섹션 헤딩(##)을 반드시 포함하고 양식에 맞출 것.
    4. 오디너리핏츠는 일본 브랜드로 간주할 것.

    [리포트 필수 구조]
    ## 1. 📈 주간 트렌드 급상승 키워드 & 아이템
    (데이터에서 가장 많이 언급된 구체적인 의류 아이템, 소재, 핏을 3~4개 불렛 포인트로 요약)

    ## 2. ⚔️ 경쟁사 vs 오리지널 브랜드 반응 분석
    (아래 항목을 포함하는 Markdown 표(Table)를 반드시 작성할 것)
    | 브랜드 구분 | 주요 언급 브랜드 | 소비자 긍정 반응 | 소비자 결핍/불만 (Pain Point) |
    | :--- | :--- | :--- | :--- |
    | 국내 도메스틱 | (예: 에스피오나지, 프리즘웍스 등) | ... | (예: 원단 내구성 아쉬움, 사이즈 애매함) |
    | 해외/오리지널 | (예: 리얼맥코이, RRL 등) | ... | (예: 가격 접근성 낮음, 구하기 힘듦) |

    ## 3. 🎯 브론슨(Bronson) 상품 기획 Action Plan
    (위의 '소비자 결핍'을 공략하여 브론슨이 기획해야 할 구체적인 아이템, 핏, 소싱해야 할 원단 방향성을 3가지 제안)

    [원본 데이터]
    {data}
    """
    response = model.generate_content(prompt)
    return response.text

# 4. 화면 깨짐 방지 & 대시보드 UI 적용
def save_to_html(content):
    now = datetime.now().strftime('%Y.%m.%d')
    
    # 핵심!: 마크다운을 정상적인 HTML 태그로 완벽히 번역 (표 포함)
    html_content = markdown.markdown(content, extensions=['tables'])
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>Bronson MD Dashboard</title>
        <style>
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
            :root {{ --primary: #2c3e50; --accent: #c0392b; --bg: #f8f9fa; --text: #333; }}
            body {{ font-family: 'Pretendard', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 40px; }}
            .dashboard {{ max-width: 1000px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; }}
            .header {{ background: var(--primary); color: #fff; padding: 30px 40px; display: flex; justify-content: space-between; align-items: center; }}
            .header h1 {{ margin: 0; font-size: 1.8em; letter-spacing: 1px; font-weight: 700; }}
            .header .date {{ background: rgba(255,255,255,0.2); padding: 5px 12px; border-radius: 4px; font-size: 0.9em; }}
            
            .content-area {{ padding: 40px; }}
            /* 렌더링된 마크다운 스타일링 */
            .content-area h2 {{ color: var(--primary); font-size: 1.4em; margin-top: 40px; margin-bottom: 20px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            .content-area h2:first-child {{ margin-top: 0; }}
            .content-area p, .content-area li {{ line-height: 1.8; font-size: 1.05em; color: #444; }}
            .content-area ul {{ padding-left: 20px; margin-bottom: 30px; }}
            
            /* 표(Table) 압도적 퀄리티 적용 */
            .content-area table {{ width: 100%; border-collapse: collapse; margin: 30px 0; font-size: 1em; background-color: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 0 10px rgba(0,0,0,0.03); }}
            .content-area th, .content-area td {{ padding: 16px 20px; text-align: left; border-bottom: 1px solid #eee; line-height: 1.5; }}
            .content-area th {{ background-color: #f1f3f5; color: var(--primary); font-weight: 700; border-bottom: 2px solid #dee2e6; }}
            .content-area tbody tr:hover {{ background-color: #f8f9fa; }}
            
            strong {{ color: var(--accent); }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1>BRONSON MARKET INTELLIGENCE</h1>
                <span class="date">UPDATE : {now}</span>
            </div>
            <div class="content-area">
                {html_content}
            </div>
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
