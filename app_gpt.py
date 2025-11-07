import os
import re
from pathlib import Path

import streamlit as st
from openai import OpenAI

# ---------------- 기본 세팅 ----------------
st.set_page_config(page_title="유란시아서 강론 생성기 (발표 스크립트 버전)", layout="wide")
st.title("유란시아서 강론 생성기 (발표 스크립트 버전)")
st.write("예: 4:5 (4편 5장). 같은 폴더에 urantia_ko.txt 가 있어야 합니다.")

# OpenAI 클라이언트
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
if not api_key:
    st.warning("⚠️ OPENAI_API_KEY 환경변수가 없습니다. Render나 로컬에서 키를 넣어주세요.")

# ---------------- 본문 로드 ----------------
TEXT_PATH = Path("urantia_ko.txt")
if not TEXT_PATH.exists():
    st.error("⚠️ urantia_ko.txt 파일을 찾을 수 없습니다. 같은 폴더에 두고 다시 실행해 주세요.")
    st.stop()

full_text = TEXT_PATH.read_text(encoding="utf-8")
lines = full_text.splitlines()


# ---------------- 본문 추출 ----------------
def extract_section_lines(paper: str, section: str):
    """
    4:5 -> 4:5. 로 시작하는 줄부터
    4:6. 이나 "제 5 편"이 나오기 전까지 모은다
    """
    collected = []
    collecting = False

    pattern_start = re.compile(rf"^{paper}:{section}\.")
    pattern_next_section = re.compile(rf"^{paper}:(?!{section})\d+\.")

    # 다음 편 제목: "제 5 편", "제5편" 모두 잡기
    next_paper_num = int(paper) + 1
    pattern_next_paper = re.compile(rf"^제\s*{next_paper_num}\s*편")

    for line in lines:
        raw = line.strip()

        if pattern_start.match(raw):
            collecting = True
        elif collecting:
            # 같은 편의 다음 장 or 다음 편 제목이 나오면 멈춘다
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

    # 위로 올라가며 장 제목 또는 편 제목 찾기
    for back in range(first_idx - 1, -1, -1):
        l = lines[back].strip()
        # "2. 하나님의 현실성" 형태
        if re.match(r"^\d+\.\s", l):
            return l.split(".", 1)[1].strip()
        # "제 4 편 ..." 형태
        if re.match(r"^제\s*\d+\s*편", l):
            return l.strip()
        # 너무 위로는 안 올라가게
        if back < first_idx - 80:
            break

    return f"{paper}편 {section}장"


# ---------------- GPT 발표 스크립트 생성 ----------------
def make_presentation_script(title: str, paper: str, section: str, source_lines):
    if client is None:
        return "⚠️ OpenAI API 키가 없어 스크립트를 만들 수 없습니다."

    text = "\n".join(source_lines)
    if len(source_lines) < 2:
        return "⚠️ 이 장에서 가져온 본문이 너무 짧습니다. urantia_ko.txt 형식을 확인하세요."

    # 강화된 인용 + 발표자 스크립트 프롬프트
prompt = f"""
다음은 유란시아서의 실제 본문입니다.
이 본문 전체를 인용하지 말고, 핵심 한두 구절만 선택하여 짧게 인용해 주세요.
그 인용에는 (편:장.절) 형식을 함께 표기하세요. 예: (4:5.3)

당신은 유란시아서를 해설하는 신중한 신학자이자 감동적인 설교자입니다.
어조는 '학문적이고 신중하되, 중간중간 설교형 감동체로 분위기를 고조'시키는 스타일입니다.

조건:
- 전체 설교문은 하나로 이어지는 완성된 흐름 (약 1000~1200자)
- 슬라이드 구분 없이 자연스럽게 이어지는 강론문
- 필요할 때만 본문 일부 인용 (1~2회)
- 인용문은 전체가 아니라 대표 문장만
- 인용 시 (편:장.절) 형태로 표시
- 유란시아서 용어는 그대로 유지

제목: {title}
본문 장: {paper}:{section}

유란시아서 본문:
{text}
"""


    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 유란시아서를 해설하는 신중한 신학자이자 감동적인 설교자입니다.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ OpenAI API 호출 오류: {e}"


# ---------------- 슬라이드 파서 ----------------
def parse_slides(script: str):
    """
    GPT가
    [슬라이드1] ... --- [슬라이드2] ...
    형태로 보낸 걸 슬라이드별로 쪼갠다.
    """
    parts = [p.strip() for p in script.split("---") if p.strip()]
    slides = []
    for p in parts:
        lines = p.splitlines()
        # 맨 윗줄이 [슬라이드X]이면 버림
        if lines and lines[0].startswith("[슬라이드"):
            lines = lines[1:]
        content = "\n".join(lines).strip()
        slides.append(content)
    return slides


# ---------------- UI ----------------
user_input = st.text_input("장/절을 입력하세요", value="4:5")

if st.button("발표 스크립트 생성"):
    if ":" not in user_input:
        st.error("형식이 올바르지 않습니다. 예: 4:5 처럼 입력해 주세요.")
    else:
        paper, section = user_input.split(":", 1)
        paper, section = paper.strip(), section.strip()

        section_lines = extract_section_lines(paper, section)
        if not section_lines:
            st.error("해당 장을 찾을 수 없습니다. urantia_ko.txt 형식과 번호를 확인해 주세요.")
        else:
            title = find_section_title(paper, section)

            st.subheader("① 추출된 원문")
            st.code("\n".join(section_lines))

            st.subheader("② GPT 발표 스크립트")
            script = make_presentation_script(title, paper, section, section_lines)
            st.markdown(script)

            st.subheader("③ 슬라이드 미리보기 (발표자가 읽을 내용)")
            slides = parse_slides(script)
            for i, s in enumerate(slides, start=1):
                st.markdown(f"**슬라이드 {i}**")
                st.write(s)
                st.write("")

