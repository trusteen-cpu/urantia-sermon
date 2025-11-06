
# 유란시아서 강론 생성기 (GPT 버전, OpenAI SDK 1.0 호환)

이 버전은 OpenAI 최신 SDK(`openai>=1.0.0`) 호환 버전으로, GPT-4o-mini 모델을 사용하여
본문 내용을 분석해 1,000자 강론문을 자동 생성합니다.

## 실행 방법

1. 같은 폴더에 `urantia_ko.txt` 파일을 둡니다.
2. Render 또는 로컬 환경에서 OpenAI API 키를 등록합니다:

```bash
export OPENAI_API_KEY=sk-xxxx...
```

3. 설치 및 실행:

```bash
pip install -r requirements.txt
streamlit run app_gpt.py
```

## Render 설정
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `streamlit run app_gpt.py --server.port $PORT --server.address 0.0.0.0`
