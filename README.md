# 유란시아서 강론 생성기 (발표 스크립트 버전)

이 앱은 `urantia_ko.txt`에서 지정한 장(예: `4:5`)을 추출해서,
그 본문을 인용하며 발표자가 그대로 읽을 수 있는 5장 분량의 스크립트를 생성합니다.

특징:
- 원문을 반드시 포함 (공부용)
- 어조: 학문적이고 신중 + 중간중간 설교형 감동체
- 슬라이드마다 발표자가 읽을 스크립트 자동 생성
- OpenAI Python SDK 1.x 방식 사용

## 실행

```bash
pip install -r requirements.txt
streamlit run app_gpt.py
