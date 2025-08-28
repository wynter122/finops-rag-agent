# 📚 Docs Agent

SageMaker 문서 검색을 위한 RAG 에이전트

## 📁 프로젝트 구조

```
finops-rag-agent/
├── src/agent/docs_agent/
│   ├── README.md              # 이 파일
│   ├── __init__.py           # 모듈 초기화
│   ├── ingest.py             # 문서 수집 및 임베딩 (CLI)
│   ├── retriever.py          # 벡터 검색 (LangChain + Chroma)
│   ├── web_scraper.py        # 웹 스크래핑
│   ├── analyze_web_structure.py  # 웹 구조 분석 (CLI)
│   ├── doc_urls.py           # 문서 URL 관리
│   └── graph.py              # LangGraph 워크플로우
├── .chroma/sagemaker_web/    # Chroma 벡터스토어
├── data/
│   ├── docs/                 # 수집된 문서
│   └── web_structure/        # 웹 구조 분석 결과
└── src/test/                 # 테스트 파일들
```

## 🚀 사용법

### 1. 환경 설정
```bash
# .env 파일에 추가
LANGSMITH_TRACING="true"
LANGSMITH_API_KEY="your_api_key"
OPENAI_API_KEY="your_openai_key"
```

### 2. 웹 구조 분석
```bash
# SageMaker 문서 구조 분석
python src/agent/docs_agent/analyze_web_structure.py

# 특정 URL 분석
python src/agent/docs_agent/analyze_web_structure.py --url "https://docs.aws.amazon.com/sagemaker/latest/dg/training-compiler.html"
```

### 3. 문서 수집 및 임베딩
```bash
# SageMaker 문서 수집 및 Chroma 인덱스 생성
python src/agent/docs_agent/ingest.py --version-date "2025-01-28"

# 커스텀 설정으로 실행
python src/agent/docs_agent/ingest.py \
  --index ".chroma/sagemaker_web" \
  --version-date "2025-01-28" \
  --chunk-size 1200 \
  --chunk-overlap 120
```

### 4. 문서 검색
```python
from src.agent.docs_agent.retriever import retrieve

result = retrieve(
    question="Training Compiler는 어떻게 동작해?",
    top_k=20,      # 검색할 문서 수
    top_n=8,       # 반환할 컨텍스트 수
    threshold=0.35 # 신뢰 임계값
)

print(f"평균 점수: {result['avg_score']:.3f}")
print(f"컨텍스트 수: {len(result['contexts'])}")
```
## 🔧 파라미터

### 검색 파라미터 (retriever.py)

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `top_k` | 20 | 검색할 문서 수 |
| `top_n` | 8 | 반환할 컨텍스트 수 |
| `threshold` | 0.35 | 신뢰 임계값 (0~1) |

### 수집 파라미터 (ingest.py)

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `--index` | `.chroma/sagemaker_web` | Chroma 인덱스 경로 |
| `--version-date` | 필수 | 문서 버전 날짜 |
| `--chunk-size` | 1200 | 청크 크기 |
| `--chunk-overlap` | 120 | 청크 오버랩 |

## 🧪 테스트

```bash
# retriever 테스트
python src/test/test_retriever.py

# Chroma 인덱스 디버그
python src/test/debug_chroma.py
```
