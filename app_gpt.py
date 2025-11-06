import streamlit as st
from openai import OpenAI
import os, re
from pathlib import Path

st.set_page_config(page_title="유란시아서 강론 생성기 (GPT 버전)", layout="wide")
st.title("유란시아서 강론 생성기 (GPT 버전)")
st.write("장 형식: 예) 1:2 (1편 2장). 본문은 urantia_ko.txt 를 기준으로 합니다.")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    st.warning("⚠️ OpenAI API 키가 설정되어 있지 않습니다. Render 환경변수에 OPENAI_API_KEY를 추가하세요.")

TEXT_PATH = Path("urantia_ko.txt")
if not TEXT_PATH.exists():
    st.error("⚠️ urantia_ko.txt 파일을 찾을 수 없습니다. 같은 폴더에 두고 다시 실행해 주세요.")
    st.stop()

full_text = TEXT_PATH.read_text(encoding="utf-8")
lines = full_text.splitlines()

def extract_section_lines(paper: str, section: str):
    target_prefix = f"{paper}:{section}."
    collected, collecting = [], False
    for line in lines:
        raw = line.strip()
        if raw.startswith(target_prefix):
            collecting = True
            collected.append(raw)
            continue
        if collecting:
            if re.match(rf"^{paper}:\d+\.", raw):
                break
            if raw:
                collected.append(raw)
    return collected

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

def make_easy_commentary_gpt(title: str, source_lines):
    text = "\n".join(source_lines)
    if not os.getenv("OPENAI_API_KEY"):
        return "⚠️ OpenAI API 키가 없어 자동 강론 생성을 수행할 수 없습니다."
    prompt = f"""
유란시아서의 다음 본문을 바탕으로, 중학생이 이해할 수 있는 1000자 내외의 강론문을 작성해 주세요.
제목은 "{title}"입니다.

본문:
{text}

조건:
- 유란시아서의 용어(예: 우주 아버지, 생각 조절자)는 그대로 사용합니다.
- 구조: 도입 → 본문 해설 → 교훈 → 결론
- 문장은 짧고 명확하게 씁니다.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 유란시아서를 중학생에게 쉽게 설명하는 신학 강론가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ OpenAI API 호출 오류: {e}"

def make_ppt_slides(title: str, paper: str, section: str, commentary: str):
    slides = [
        {"title": title, "bullets": [f"본문: {paper}:{section}", "핵심 요약", "중학생도 이해할 수 있는 해설"]},
        {"title": "1. 핵심 개념", "bullets": ["본문이 전하는 주된 사상", "하나님, 인격, 우주 관계"]},
        {"title": "2. 주요 교훈", "bullets": ["본문을 통해 배울 수 있는 신앙적 통찰", "하나님과 인간 인격의 관계"]},
        {"title": "3. 실제 적용", "bullets": ["일상에서 적용할 수 있는 태도", "하나님을 인격적으로 이해하기"]},
        {"title": "4. 결론", "bullets": ["핵심 요약 및 느낀 점", "사랑과 봉사의 실천으로 마무리"]},
    ]
    return slides

user_input = st.text_input("장/절을 입력하세요 (예: 1:2)", value="1:2")

if st.button("강론 생성하기"):
    if ":" not in user_input:
        st.error("형식이 올바르지 않습니다. 예: 1:2 처럼 입력해 주세요.")
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
