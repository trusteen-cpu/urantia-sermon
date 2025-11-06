import streamlit as st
import re
from pathlib import Path

st.set_page_config(page_title="유란시아서 강론 생성기", layout="wide")
st.title("유란시아서 강론 생성기 (베타)")
st.write("장 형식: 예) 1:2  (1편 2장). 본문은 urantia_ko.txt 를 기준으로 합니다.")

TEXT_PATH = Path("urantia_ko.txt")
if not TEXT_PATH.exists():
    st.error("⚠️ urantia_ko.txt 파일을 찾을 수 없습니다. 같은 폴더에 두고 다시 실행해 주세요.")
    st.stop()

full_text = TEXT_PATH.read_text(encoding="utf-8")
lines = full_text.splitlines()

def extract_section_lines(paper: str, section: str):
    """'1:2'처럼 들어오면 1:2.로 시작하는 줄들을 수집한다."""
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
            # 같은 paper의 다른 section을 만나면 종료
            if re.match(rf"^{paper}:\d+\.", raw):
                break
            # 그 외 줄은 그대로 포함 (빈줄 제외)
            if raw:
                collected.append(raw)
    return collected

def find_section_title(paper: str, section: str):
    """
    1) 먼저 해당 섹션 첫 줄 위치를 찾는다.
    2) 그 위로 거슬러 올라가면서
       - '^\d+\.\s' 로 시작하는 줄 (예: '2. 하나님의 현실성')
       - 또는 '제 1 편' 같은 줄
       을 발견하면 그걸 제목으로 쓴다.
    3) 없으면 'paper편 section장'으로 대체.
    """
    target_prefix = f"{paper}:{section}."
    first_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith(target_prefix):
            first_idx = idx
            break

    if first_idx is None:
        return f"{paper}편 {section}장"

    # 거슬러 올라가며 제목 찾기
    for back in range(first_idx - 1, -1, -1):
        l = lines[back].strip()
        # 장 제목 패턴
        if re.match(r"^\d+\.\s", l):
            return l.split(".", 1)[1].strip()
        # 편 제목 패턴
        if re.match(r"^제\s*\d+\s*편", l):
            return l.strip()
        # 너무 위까지 올라가면 중단
        if back < first_idx - 80:
            break

    return f"{paper}편 {section}장"

def make_easy_commentary(title: str, source_lines):
    src_preview = " ".join(source_lines[:3])
    parts = []
    parts.append(f"**{title}**")
    parts.append("")
    parts.append("이 장에서는 유란시아서가 말하는 하나님과 우주, 그리고 인격의 관계를 좀 더 쉽게 설명해 보려 합니다. "
                 "원문은 매우 우주론적인 표현을 쓰지만, 핵심은 ‘하나님은 인격이시고, 우리 인격은 그분에게서 왔다’는 점입니다.")
    parts.append("")
    parts.append("첫째로, 유란시아서는 인격이 스스로 생기는 것이 아니라고 말합니다. "
                 "인격은 파라다이스 아버지가 주신 선물이며, 그래서 우리는 하나님을 알고 사랑할 수 있습니다. "
                 "우리가 생각하고 선택하고 예배할 수 있는 이유가 여기에 있습니다.")
    parts.append("")
    parts.append("둘째로, 같은 하나님을 두고도 관점에 따라 다르게 이해할 수 있다고 설명합니다. "
                 "과학은 하나님을 우주의 근원으로, 철학은 우주를 하나로 묶는 개념으로 봅니다. "
                 "그러나 종교적 체험에서는 하나님이 실제로 우리를 아시는 ‘아버지’로 나타납니다. "
                 "유란시아서는 이 인격적인 이해가 가장 완전하다고 강조합니다.")
    parts.append("")
    parts.append("셋째로, 인간 인격은 유한하지만 성장할 수 있는 인격이라고 설명합니다. "
                 "우리 안에 내주하는 생각 조절자와 협력하고, 도덕적으로 하나님을 닮아 갈 때, "
                 "우리는 더 높은 인격 수준으로 나아갈 수 있습니다. "
                 "신성한 인격과의 친밀함은 이렇게 영적 진보 속에서 깊어집니다.")
    parts.append("")
    parts.append("마지막으로, 이 장은 우리에게 다른 사람의 인격도 존중하라고 가르칩니다. "
                 "내 인격이 하나님께서 주신 것이듯, 다른 이의 인격도 같은 근원을 갖고 있기 때문입니다. "
                 "그래서 하나님을 힘이 아니라 인격적 아버지로 대하고, 이웃을 인격으로 대하는 것이 이 가르침의 실제 적용입니다.")
    return "\n".join(parts)

def make_ppt_slides(title: str, paper: str, section: str):
    slides = []

    slides.append({
        "title": title,
        "bullets": [
            f"본문: {paper}:{section}",
            "주제: 하나님은 인격이시다",
            "인간 인격은 그분의 선물"
        ]
    })
    slides.append({
        "title": "1. 인격의 근원",
        "bullets": [
            "인격은 저절로 생기지 않는다",
            "파라다이스 아버지의 증여",
            "관계 맺기 위한 능력"
        ]
    })
    slides.append({
        "title": "2. 하나님 이해의 관점",
        "bullets": [
            "과학: 우주의 원인",
            "철학: 통합의 개념",
            "종교: 사랑의 아버지"
        ]
    })
    slides.append({
        "title": "3. 인간 인격의 성장",
        "bullets": [
            "유한하지만 확장 가능",
            "생각 조절자와의 협력",
            "도덕·영적 유사성 필요"
        ]
    })
    slides.append({
        "title": "4. 적용",
        "bullets": [
            "하나님을 인격으로 예배하기",
            "이웃 인격 존중하기",
            "인격적 체험을 통해 하나님 알기"
        ]
    })
    return slides

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
            st.error("해당 장을 찾을 수 없습니다. urantia_ko.txt 안의 번호와 일치하는지 확인해 주세요.")
        else:
            title = find_section_title(paper, section)

            st.subheader("① 원문(추출된 줄)")
            st.code("\n".join(section_lines))

            commentary = make_easy_commentary(title, section_lines)
            st.subheader("② 중학생용 1,000자 강론")
            st.markdown(commentary)

            slides = make_ppt_slides(title, paper, section)
            st.subheader("③ 5장 PPT 요약")
            for i, slide in enumerate(slides, start=1):
                st.markdown(f"**슬라이드 {i}. {slide['title']}**")
                for b in slide["bullets"]:
                    st.write(f"- {b}")
                st.write("")
