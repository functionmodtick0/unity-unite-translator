# Unity Unite Translator 사용 가이드

## 프로젝트 구조

```
src/unity_unite_translator/
├── __init__.py          # 모듈 초기화
├── parser.py            # RPG Maker 텍스트 추출 (번역 기능 통합)
├── applier.py           # 번역된 텍스트 적용
└── translator.py        # 번역 API 호출 함수
```

## 번역 서버 설정

번역 서버가 `http://localhost:8000` 에서 실행 중이어야 합니다.
서버는 다음 형식의 요청을 처리해야 합니다:

```
GET http://localhost:8000/?text={번역할텍스트}
```

## 사용 방법

### 1. 텍스트 추출 및 번역

```bash
python -m unity_unite_translator.parser
```

프로그램 실행 시:
1. 프로젝트 이름 입력
2. 자동 번역 여부 선택 (y/n)
   - `y`: 추출된 텍스트를 자동으로 번역
   - `n`: 번역하지 않고 원문만 추출

결과: `projects/{PROJECT_NAME}/rpgm_texts.csv` 생성

### 2. 번역 적용

```bash
python -m unity_unite_translator.applier
```

CSV 파일의 번역을 Unity 에셋 파일에 적용합니다.

## CSV 파일 형식

```csv
file,source,target
/path/to/file.asset,"원문 텍스트","번역된 텍스트"
```

- **file**: Unity 에셋 파일 경로
- **source**: 일본어 원문
- **target**: 한국어 번역

## 번역 함수 직접 사용

```python
from unity_unite_translator import translate, translate_batch

# 단일 텍스트 번역
translated = translate("こんにちは")

# 일괄 번역
texts = ["こんにちは", "ありがとう"]
translations = translate_batch(texts)
```

### 고급 옵션

```python
# 커스텀 URL 및 재시도 설정
translated = translate(
    text="こんにちは",
    base_url="http://localhost:8000",
    retry=3,
    delay=0.5
)

# 배치 번역 설정
translations = translate_batch(
    texts=["こんにちは", "ありがとう"],
    base_url="http://localhost:8000",
    batch_size=10,  # 진행상황 표시 주기
    show_progress=True
)
```

## 주의사항

1. 번역 서버가 실행 중이어야 합니다
2. YAML 형식의 이스케이프 문자(\n, \" 등)는 유지됩니다
3. 번역 실패 시 원문이 그대로 반환됩니다
4. 서버 부하를 방지하기 위해 요청 간 0.5초 대기 시간이 있습니다
