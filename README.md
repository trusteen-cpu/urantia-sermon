
# 유란시아서 강론 생성기 (GPT 버전)

OpenAI API를 이용해 본문 내용을 기반으로 자동으로 **1,000자 강론문을 생성**하는 Streamlit 앱입니다.

## 실행 방법

1. 같은 폴더에 `urantia_ko.txt` 파일을 둡니다.
2. OpenAI API 키를 환경 변수로 설정합니다.

```bash
export OPENAI_API_KEY=sk-xxxx...
```

또는 Render 환경변수에서 추가:
| Key | Value |
|-----|--------|
| OPENAI_API_KEY | sk-xxxx... |

3. 필요한 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

4. 앱 실행:

```bash
streamlit run app_gpt.py
```
