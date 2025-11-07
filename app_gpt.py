import os
import re
from pathlib import Path

import streamlit as st
from openai import OpenAI

# ---------------- 기본 세팅 ----------------
st.set_page_config(page_title="유란시아서 강론 생성기 (GPT 버전)", layout="wide")
st.title("유란시아서 강론 생성기 (GPT 버전)")
st.write("장 형식: 예) 1:2 (1편 2장). 본문은 urantia_ko.txt 를 기준으로 합니다.")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

if not api_key:
    st.warning("⚠️ Render 환경변수에 OPENAI_API_KEY가 설정되어 있지 않습니다. 키를 넣고 다시 배포하세요.")

# ---------------- 본문 로드 ----------------
TEXT_PATH = Path("urantia_ko.txt")
if not TEXT_PATH.exists():
    st.error("⚠️ urantia_ko.txt 파일을 찾을 수 없습니다. 같은 폴더에 두고 다시 실행해 주세요.")
    st.stop()

full_text = TEXT_PATH.read_text(encoding="utf-8")
lines = full_text.splitlines()

# ---------------- 유틸 함수들 ----------------
def extract_section_lines(paper: str, section: str):
    """
    '1:2' -> '1:2.' 로 시작하는 줄부터 같은 편의 다음 장이 나올 때까지 모음
    """
    target_prefix = f"{paper}:{section}."
    collected = []
    collecting = False
    for line in lines:
        raw = line.strip()
        if raw.startswith(target_prefix):
            collecting = True
            collected.append(raw)
            continue
        if collecting:
            # 같은 편의 다른 장으로 넘어가면 중단
            if re.match(rf"^{paper}:\d+\.", raw):
                break
            if raw:
                collected.append(raw)
    return collected


def find_section_title(paper: str, section: str):
    """
    위쪽으로 올라가면서 '숫자. 제목' 이나 '제 n 편' 찾기
    없으면 'n편 m장'
    """
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
        # "2. 하나님의 현실성" 이런 줄
        if re.match(r"^\d+\.\s", l):
            return l.split(".", 1)[1].strip()
        # "제 1 편 ..." 이런 줄
        if re.match(r"^제\s*\d+\s*편", l):
            return l.strip()
        if back < first_idx - 80:
            break

    return f"{paper}편 {section}장"


def make_easy_commentary_gpt(title: str, source_lines):
    """
    OpenAI SDK 1.x 버전용 강론 생성
    """
    if client is None:
        return "⚠️ OpenAI API 키가 없어 자동 강론 생성을 수행할 수 없습니다."

    text = "\n".join(source_lines)
    prompt = f"""
유란시아서의 다음 본문을 바탕으로, 중학생이 이해할 수 있는 1000자 내외의 강론문을 작성해 주세요.
제목은 "{title}"입니다.

본문:
{text}

조건:
- 유란시아서의 용어(예: 우주 아버지, 생각 조절자)는 그대로 사용합니다.
- 구조: 도입 -> 본문 해설 -> 교훈 -> 결론
- 문장은 짧고 명확하게 씁니다.
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 유란시아서를 중학생에게 쉽게 설명하는 신학 강론가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ OpenAI API 호출 오류: {e}"


def make_ppt_slides(title: str, paper: str, section: str, commentary: str):
    """
    PPT를 항상 같은 템플릿이 아니라
    강론에서 첫 문단/첫 몇 줄을 가져와서 넣어주는 방식으로 살짝 동적화
    """
    # commentary에서 앞쪽 2~3줄만 뽑기
    lines = [l.strip() for l in commentary.splitlines() if l.strip()]
    preview = lines[0] if lines else "이 장의 핵심 내용을 요약합니다."

    slides = [
        {
            "title": title,
            "bullets": [
                f"본문: {paper}:{section}",
                preview,
                "유란시아서 용어는 원문 그대로 사용",
            ],
        },
        {
            "title": "1. 핵심 개념",
            "bullets": [
                "이 단락이 말하는 우주/하나님/인격의 중심 사상",
                "하나님을 인격적으로 이해해야 하는 이유",
            ],
        },
        {
            "title": "2. 본문이 가르치는 점",
            "bullets": [
                "인간 인격은 하나님에게서 온 선물",
                "영적 체험이 있을 때 인격적 하나님 이해가 깊어짐",
            ],
        },
        {
            "title": "3. 적용",
            "bullets": [
                "다른 사람의 인격도 존중하기",
                "하나님을 힘이 아닌 아버지로 대하기",
            ],
        },
        {
            "title": "4. 결론",
            "bullets": [
                "인격이 있다는 것은 우주가 인격적이라는 증거",
                "예배와 봉사로 인격적 응답하기",
            ],
        },
    ]
    return slides


# ---------------- UI ----------------
user_input = st.text_input("장/절을 입력하세요 (예: 1:2)", value="1:2")

if st.button("강론 생성하기"):
    if ":" not in user_input:
        st.error("형식이 올바르지 않습니다. 예: 1:2 처럼 입력해 주세요.")
    else:
        paper, section = user_input.split(":", 1)
        paper = paper.strip()
        section = section.strip()

        section_lines = extract_section_lines(paper, section)
        if not section_lines:
            st.error("해당 장을 찾을 수 없습니다. urantia_ko.txt의 번호와 일치하는지 확인해 주세요.")
        else:
            title = find_section_title(paper, section)

            st.subheader("① 원문(추출된 줄)")
            st.code("\n".join(section_lines))

            st.subheader("② GPT 자동 생성 강론 (약 1,000자)")
            commentary = make_easy_commentary_gpt(title, section_lines)
            st.markdown(commentary)

            st.subheader("③ 5장 PPT 요약")
            slides = make_ppt_slides(title, paper, section, commentary)
            for i, slide in enumerate(slides, start=1):
                st.markdown(f"**슬라이드 {i}. {slide['title']}**")
                for b in slide["bullets"]:
                    st.write(f"- {b}")
                st.write("")
