
# 유란시아서 강론 생성기 (v5)

장/절을 입력하면:
1. urantia_ko.txt 에서 해당 본문을 정확히 추출하고
2. GPT가 학문적이면서 감동적인 단일 설교 스크립트를 생성하고
3. 그 설교를 5장짜리 발표 슬라이드로 요약해 줍니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app_gpt.py
```

같은 폴더에 `urantia_ko.txt` 를 두세요.

## Render 설정

- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app_gpt.py --server.port $PORT --server.address 0.0.0.0`
- Env: `OPENAI_API_KEY=sk-...`
