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
당신은 유란시아서를 함께 읽는 소그룹의 발표자입니다.
아래의 유란시아서 실제 본문을 꼭 인용하면서 설명해 주세요.
어조는 "학문적이고 신중하되, 중간중간 설교형 감동체로 분위기를 고조"시키는 스타일입니다.

발표 형식은 반드시 아래 구조를 따르세요:

[슬라이드1]
본문: (여기에 원문 중 핵심 2~3줄을 그대로 넣으세요)
발표자: (이 본문이 무엇을 말하는지 설명하고, 왜 중요한지 부드럽게 말하세요)

---
[슬라이드2]
본문: (다음으로 중요한 원문 2~3줄)
발표자: (여기서는 신학적·우주론적 의미를 한 단계 깊게 풉니다. 학문적 어조 사용)

---
[슬라이드3]
본문: (사람들과 같이 읽었으면 하는 대목)
발표자: (이제 설교형 감동체로 전환해서 적용을 제안하세요. '우리 안에 내주하시는 생각 조절자' 같은 표현은 원문 용어 그대로 쓰세요.)

---
[슬라이드4]
본문: (짧은 한 줄만)
발표자: (오늘 본문을 통해 배운 것을 삶과 사역에 연결해 주세요.)

---
[슬라이드5]
본문: (선택) 오늘 장 전체를 대표하는 한 문장
발표자: (기도로 마무리하듯, 하나님 인격을 향해 나아가도록 격려하세요.)

조건:
- 유란시아서의 용어는 절대 바꾸지 말고 그대로 쓰세요.
- 인용은 짧게 여러 번 하세요.
- 너무 딱딱한 제목 대신, 발표자가 그대로 읽을 문장을 써 주세요.
- 전체 길이는 대략 1,000~1,200자 정도로 해 주세요.

제목: {title}
장 번호: {paper}:{section}

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

