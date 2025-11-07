import os
import re
from pathlib import Path
import streamlit as st
from openai import OpenAI

# ---------------- 기본 세팅 ----------------
st.set_page_config(page_title="유란시아서 강론 생성기 (인용 해설 버전)", layout="wide")
st.title("유란시아서 강론 생성기 (인용 해설 버전)")
st.write("장 형식: 예) 4:5 (4편 5장). 본문은 urantia_ko.txt 를 기준으로 합니다.")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

if not api_key:
    st.warning("⚠️ Render 환경변수에 OPENAI_API_KEY가 설정되어 있지 않습니다. 키를 추가 후 재배포하세요.")

# ---------------- 본문 로드 ----------------
TEXT_PATH = Path("urantia_ko.txt")
if not TEXT_PATH.exists():
    st.error("⚠️ urantia_ko.txt 파일을 찾을 수 없습니다. 같은 폴더에 두고 다시 실행해 주세요.")
    st.stop()

full_text = TEXT_PATH.read_text(encoding="utf-8")
lines = full_text.splitlines()

# ---------------- 본문 추출 함수 ----------------
def extract_section_lines(paper: str, section: str):
    """
    예: '4:5' -> 4편 5장에서 시작해 4:6. 또는 5:1. 나오면 종료
    """
    collected = []
    collecting = False
    pattern_start = re.compile(rf"^{paper}:{section}\.")
    pattern_next_section = re.compile(rf"^{paper}:(?!{section})\d+\.")
    pattern_next_paper = re.compile(rf"^{int(paper)+1}:\d+\.")

    for line in lines:
        raw = line.strip()
        if pattern_start.match(raw):
            collecting = True
        elif collecting:
            if pattern_next_section.match(raw) or pattern_next_paper.match(raw):
                break
        if collecting:
            collected.append(raw)
    return collected

# ---------------- 제목 찾기 ----------------
def find_section_title(paper: str, section: str):
    target_prefix = f"{paper}:{section}."
    first_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith(target_prefix):
            first_idx = idx
            break
    if first_idx is None:
        return f"{paper}편 {section}장"
    for back in range(first_idx - 1, -1, -1):
        l = lines[back].strip()
        if re.match(r"^\d+\.\s", l):
            return l.split(".", 1)[1].strip()
        if re.match(r"^제\s*\d+\s*편", l):
            return l.strip()
        if back < first_idx - 80:
            break
    return f"{paper}편 {section}장"

# ---------------- GPT 강론 생성 ----------------
def make_easy_commentary_gpt(title: str, source_lines):
    if client is None:
        return "⚠️ OpenAI API 키가 없어 자동 강론 생성을 수행할 수 없습니다."

    text = "\n".join(source_lines)
    if len(source_lines) < 3:
        return "⚠️ 선택한 장의 본문이 너무 짧거나 인식되지 않았습니다. urantia_ko.txt 형식을 다시 확인하세요."

    prompt = f"""
다음은 유란시아서의 실제 본문입니다. 이 원문을 반드시 인용하면서 해설문을 작성하세요.
- 인용 시 '원문에서 다음과 같이 말합니다:' 또는 '본문은 이렇게 설명합니다:' 같은 표현을 사용하세요.
- 강론문은 1000자 내외로, 도입 → 본문 해설 → 교훈 → 결론의 구조로 쓰세요.
- 인용 구절을 중심으로 신학적 의미를 풀어주세요.
- 유란시아서의 용어(예: 우주 아버지, 생각 조절자)는 그대로 유지하세요.

제목: "{title}"

본문:
{text}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 유란시아서를 인용하며 신학적으로 해설하는 설교가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ OpenAI API 호출 오류: {e}"

# ---------------- 슬라이드 생성 ----------------
def make_ppt_slides(title: str, paper: str, section: str, commentary: str):
    lines = [l.strip() for l in commentary.splitlines() if l.strip()]
    intro = lines[0][:80] + "..." if lines else "이 장의 핵심 내용을 요약합니다."
    key_points = [l for l in lines if "원문" in l][:3]  # 인용 구절 3개까지만 슬라이드에 반영

    slides = [
        {"title": title, "bullets": [f"본문: {paper}:{section}", intro, "원문 인용 중심 해설"]},
        {"title": "1. 본문 인용 요약", "bullets": key_points or ["본문 주요 구절을 중심으로 해설"]},
        {"title": "2. 핵심 교훈", "bullets": ["인격과 영적 성장의 관계", "하나님과 인간의 인격적 연결"]},
        {"title": "3. 적용", "bullets": ["삶 속에서 신성한 인격을 드러내기", "이웃과의 관계에서 사랑 실천"]},
        {"title": "4. 결론", "bullets": ["본문의 요점 정리", "영적 인격의 완성으로 나아가기"]},
    ]
    return slides

# ---------------- Streamlit UI ----------------
user_input = st.text_input("장/절을 입력하세요 (예: 4:5)", value="4:5")

if st.button("강론 생성하기"):
    if ":" not in user_input:
        st.error("형식이 올바르지 않습니다. 예: 4:5 처럼 입력해 주세요.")
    else:
        paper, section = user_input.split(":", 1)
        paper, section = paper.strip(), section.strip()

        section_lines = extract_section_lines(paper, section)
        if not section_lines:
            st.error("해당 장을 찾을 수 없습니다. urantia_ko.txt의 번호와 일치하는지 확인해 주세요.")
        else:
            title = find_section_title(paper, section)
            st.subheader("① 원문(추출된 줄)")
            st.code("\n".join(section_lines))

            st.subheader("② GPT 자동 생성 강론 (인용 기반 약 1,000자)")
            commentary = make_easy_commentary_gpt(title, section_lines)
            st.markdown(commentary)

            st.subheader("③ 자동 생성 슬라이드 (5장 요약)")
            slides = make_ppt_slides(title, paper, section, commentary)
            for i, slide in enumerate(slides, start=1):
                st.markdown(f"**슬라이드 {i}. {slide['title']}**")
                for b in slide["bullets"]:
                    st.write(f"- {b}")
                st.write("")
