import os
import re
from pathlib import Path

import streamlit as st
from openai import OpenAI

# ---------------- 기본 설정 ----------------
st.set_page_config(page_title="유란시아서 강론 생성기 (v5)", layout="wide")
st.title("유란시아서 강론 생성기 (v5)")
st.write("입력 예: 3:5  (3편 5장). 같은 폴더에 urantia_ko.txt 가 있어야 합니다.")

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
if not api_key:
    st.warning("⚠️ OPENAI_API_KEY 환경변수가 없습니다. Render나 로컬에서 키를 넣어주세요.")

# ---------------- 본문 로드 ----------------
TEXT_PATH = Path("urantia_ko.txt")
if not TEXT_PATH.exists():
    st.error("⚠️ urantia_ko.txt 파일을 찾을 수 없습니다. 같은 폴더에 두고 다시 실행해 주세요.")
    st.stop()

lines = TEXT_PATH.read_text(encoding="utf-8").splitlines()

# ---------------- 본문 추출 ----------------
def extract_section_lines(paper: str, section: str):
    collected = []
    collecting = False
    pattern_start = re.compile(rf"^{paper}:{section}\.")
    pattern_next_section = re.compile(rf"^{paper}:(?!{section})\d+\.")
    next_paper = int(paper) + 1
    pattern_next_paper = re.compile(rf"^제\s*{next_paper}\s*편")

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
        txt = lines[back].strip()
        if re.match(r"^\d+\.\s", txt):
            return txt.split(".", 1)[1].strip()
        if re.match(r"^제\s*\d+\s*편", txt):
            return txt.strip()
        if back < first_idx - 80:
            break
    return f"{paper}편 {section}장"

# ---------------- GPT 설교 생성 ----------------
def create_sermon(title: str, paper: str, section: str, source_lines):
    if client is None:
        return "⚠️ OpenAI API 키가 없어 설교를 만들 수 없습니다."
    text = "\n".join(source_lines)
    prompt = f"""다음은 유란시아서 제 {paper}편 {section}장 "{title}"의 실제 본문입니다.

당신은 유란시아서를 깊이 이해한 신중한 신학자이자 감동적인 설교자입니다.
아래 조건에 맞는 하나의 완성된 설교 스크립트를 작성하세요.

조건:
- 길이: 약 1000~1200자
- 구조: 도입 → 본문 해석 → 신학적 의미 → 개인적 적용 → 결론
- 본문 전체를 인용하지 말고, 핵심이 되는 1~2문장만 직접 인용하세요.
- 인용 시 반드시 (편:장.절) 형식을 덧붙이세요. 예: (3:5.2)
- 유란시아서 특유의 용어(우주 아버지, 생각 조절자 등)는 변경하지 마세요.
- 어조는 학문적이고 신중하되, 중간에 설교형 감동체로 고조시키세요.
- 설교문 안에는 슬라이드 구분을 넣지 마세요. 하나의 글로 자연스럽게 이어지게 하세요.

본문:
{text}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 유란시아서를 해설하는 신중한 신학자이자 감동적인 설교자입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ OpenAI API 호출 오류: {e}"

# ---------------- GPT 슬라이드 요약 ----------------
def create_slides_from_sermon(sermon: str):
    if client is None:
        # fallback: naive split
        paras = [p.strip() for p in sermon.split("\n") if len(p.strip()) > 50]
        slides = []
        for i, p in enumerate(paras[:5]):
            slides.append({
                "title": f"슬라이드 {i+1}",
                "quote": "",
                "content": p
            })
        return slides

    prompt = f"""다음은 유란시아서 강론 설교문입니다.

이 설교문의 핵심을 5장의 슬라이드로 요약해 주세요.

형식:
슬라이드 1. (짧은 제목)
본문 인용: (설교문 안에 (3:5.2) 처럼 표시된 인용이 있으면 그 문장만 넣고, 없으면 이 줄은 생략)
요약: (발표자가 그대로 읽을 2~3문장)

---
슬라이드 2. ...
---
슬라이드 3. ...
---
슬라이드 4. ...
---
슬라이드 5. ...

설교문:
{sermon}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "너는 설교문을 발표용 슬라이드로 뽑아내는 조교다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        text = resp.choices[0].message.content.strip()
        # 단순 파서: --- 로 나눔
        parts = [p.strip() for p in text.split("---") if p.strip()]
        slides = []
        for p in parts:
            lines = p.splitlines()
            title = lines[0].strip() if lines else "슬라이드"
            quote = ""
            content_lines = []
            for ln in lines[1:]:
                if ln.startswith("본문 인용:"):
                    quote = ln.replace("본문 인용:", "").strip()
                elif ln.startswith("요약:"):
                    content_lines.append(ln.replace("요약:", "").strip())
                else:
                    content_lines.append(ln.strip())
            slides.append({
                "title": title,
                "quote": quote,
                "content": "\n".join(content_lines).strip()
            })
        return slides[:5]
    except Exception:
        # fallback
        paras = [p.strip() for p in sermon.split("\n") if len(p.strip()) > 50]
        slides = []
        for i, p in enumerate(paras[:5]):
            slides.append({
                "title": f"슬라이드 {i+1}",
                "quote": "",
                "content": p
            })
        return slides


# ---------------- UI ----------------
user_input = st.text_input("장/절을 입력하세요", value="3:5")

if st.button("생성하기"):
    if ":" not in user_input:
        st.error("형식이 올바르지 않습니다. 예: 3:5")
    else:
        paper, section = user_input.split(":", 1)
        paper, section = paper.strip(), section.strip()

        section_lines = extract_section_lines(paper, section)
        if not section_lines:
            st.error("해당 장을 찾지 못했습니다. urantia_ko.txt 형식을 확인하세요.")
        else:
            title = find_section_title(paper, section)

            st.markdown(f"### 📖 제{paper}편 {section}장 {title}")
            st.subheader("① 추출된 원문")
            st.code("\n".join(section_lines))

            st.subheader("② GPT 설교 스크립트")
            sermon = create_sermon(title, paper, section, section_lines)
            st.markdown(sermon)

            st.subheader("③ PPT 슬라이드 (요약 5장)")
            slides = create_slides_from_sermon(sermon)
            for i, slide in enumerate(slides, start=1):
                st.markdown(f"**{slide['title']}**")
                if slide["quote"]:
                    st.markdown(f"> {slide['quote']}")
                st.write(slide["content"])
                st.write("")
