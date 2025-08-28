# FinOps RAG Agent

AWS SageMaker 비용 분석을 위한 ETL 파이프라인과 RAG(Retrieval-Augmented Generation) 기반 AI 에이전트입니다.

## 🚀 기능

- **Redshift CUR 추출**: AWS Cost & Usage Report 데이터 자동 추출 (최적화된 컬럼 선택)
- **데이터 변환**: SageMaker 비용 데이터 정규화 및 집계
- **LLM 정규화**: OpenAI를 활용한 데이터 카테고리 정규화 (예정)
- **LLM 기반 의도 분류**: GPT-4o-mini를 활용한 정확한 질문 의도 분류
- **멀티 에이전트 라우팅**: SQL, Docs, General 에이전트로의 지능형 라우팅
- **RAG 기반 질의응답**: 문서 기반 지능형 응답 시스템
- **비용 최적화 추천**: AI 기반 비용 절감 방안 제안 (예정)

## 📋 요구사항

- Python 3.12+
- uv (Python 패키지 관리자)
- Redshift 접근 권한 (또는 CUR CSV 파일)

## 🛠️ 설치

1. **저장소 클론**
```bash
git clone <repository-url>
cd finops-rag-agent
```

2. **가상환경 생성 및 활성화**
```bash
uv venv --python 3.12
source .venv/bin/activate  # macOS/Linux
# 또는 .venv\Scripts\activate  # Windows
```

3. **의존성 설치**
```bash
uv sync
```

4. **환경변수 설정**
```bash
# .env 파일을 생성하고 Redshift 연결 정보 입력
cp .env.example .env  # 예시 파일이 있는 경우
# 또는 직접 .env 파일 생성
```



## 🏃‍♂️ 실행

### ETL 파이프라인 실행

#### Redshift에서 직접 추출
```bash
python -m src.run_etl --billing-ym 202508 \
  --accounts 123456789101,112233445566,987654321987
```

#### 로컬 CSV 파일 사용
```bash
python -m src.run_etl --billing-ym 202508 \
  --accounts 123456789101,112233445566,987654321987 \
  --input-csv data/raw/sagemaker_cur_sample.csv \
  --limit 100
```

### Streamlit UI 실행

#### 방법 1: 실행 스크립트 사용
```bash
./run_ui.sh
```

#### 방법 2: 직접 실행
```bash
streamlit run src/ui/app.py
```

#### 방법 3: 개발 모드
```bash
streamlit run src/ui/app.py --server.port 8501 --server.address 0.0.0.0
```

### 개발 서버 실행 (예정)
```bash
# RAG 챗봇 서버 (예정)
uv run uvicorn src.rag.chatbot:app --reload
```

## 📁 프로젝트 구조

```
finops-rag-agent/
├── src/                   # 소스 코드
│   ├── agent/            # AI 에이전트 모듈
│   │   ├── docs_agent/   # 문서 기반 RAG 에이전트
│   │   │   ├── graph.py      # LangGraph 워크플로우
│   │   │   ├── ingest.py     # 문서 수집 및 처리
│   │   │   └── retriever.py  # 벡터 검색 및 검색
│   │   ├── sql_agent/    # SQL 생성 및 실행 에이전트
│   │   │   ├── graph.py      # LangGraph 워크플로우
│   │   │   ├── nl2sql.py     # 자연어를 SQL로 변환
│   │   │   ├── executor.py   # SQL 실행기
│   │   │   ├── schema_provider.py # 데이터베이스 스키마 제공
│   │   │   └── summary.py    # SQL 결과 요약
│   │   ├── general_agent/ # 일반 대화 에이전트
│   │   │   └── graph.py      # LangGraph 워크플로우
│   │   └── router/       # 의도 분류 및 라우팅
│   │       ├── graph.py      # LangGraph 워크플로우
│   │       └── intent_router.py # LLM 기반 의도 분류기
│   ├── core/             # 핵심 모듈
│   │   ├── config.py     # 설정 관리
│   │   └── contracts.py  # 계약 관리 (cloud radar 시스템 전용)
│   ├── etl/              # ETL 파이프라인
│   │   ├── extract.py    # Redshift 데이터 추출 (최적화된 컬럼 선택)
│   │   ├── transform.py  # CUR 데이터 변환
│   │   ├── clean.py      # LLM 정규화
│   │   ├── store.py      # 데이터 저장
│   │   ├── runner.py     # ETL 실행기
│   │   └── README.md     # ETL 문서
│   ├── rag/              # RAG 챗봇 (예정)
│   │   └── __init__.py
│   ├── ui/               # Streamlit UI
│   │   ├── app.py        # 메인 Streamlit 앱
│   │   ├── components/   # UI 컴포넌트
│   │   │   ├── chat_message.py  # 채팅 메시지 렌더링
│   │   │   ├── citations.py     # 참고문헌 카드
│   │   │   └── metrics.py       # 숫자 요약 메트릭
│   │   └── utils/        # UI 유틸리티
│   │       └── session.py       # 세션 상태 관리
│   ├── test/             # 테스트 및 디버깅
│   │   ├── test_chat.py  # 챗봇 테스트
│   │   ├── debug_llm.py  # LLM 디버깅
│   │   └── README.md     # 테스트 문서
│   ├── utils/            # 유틸리티
│   │   ├── logging.py    # 로깅 설정
│   │   └── lock.py       # 파일 락
│   └── run_etl.py        # ETL 메인 실행 파일
├── data/                 # 데이터 저장소
│   ├── raw/             # 원시 데이터
│   ├── processed/       # 처리된 데이터 (Parquet + CSV)
│   └── logs/            # ETL 로그 파일
├── contracts.json        # 계약 정의 파일
├── mvp-design-doc.md     # MVP 설계 문서
├── pyproject.toml        # Python 프로젝트 설정
├── uv.lock              # uv 의존성 잠금 파일
├── encrypt.sh           # 환경변수 암호화 스크립트
├── decrypt.sh           # 환경변수 복호화 스크립트
├── env_crypto.py        # 환경변수 암호화/복호화 도구
└── README.md
```

## 📝 환경 변수

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# Redshift 연결 설정
REDSHIFT_HOST=your-redshift-cluster.region.redshift.amazonaws.com
REDSHIFT_PORT=5439
REDSHIFT_DB=your_database_name
REDSHIFT_USER=your_username
REDSHIFT_PASSWORD=your_password
REDSHIFT_SSL=true

# CUR 테이블 설정
CUR_TABLE=aws_cost_usage

# 출력 디렉토리
OUTPUT_DIR=data

# LLM 정규화 설정 (선택사항)
USE_LLM_NORMALIZATION=false
OPENAI_API_KEY=sk-your-openai-api-key

# LangSmith 트레이싱 설정 (UI용)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=finops-rag-agent

# Chroma 벡터 저장소 설정 (RAG용, 예정)
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## 🔐 환경 변수 암호화

프로젝트에는 `.env` 파일을 안전하게 암호화/복호화할 수 있는 도구가 포함되어 있습니다.

### 암호화
```bash
./encrypt.sh "안전한비밀번호"
```

### 복호화
```bash
./decrypt.sh "안전한비밀번호"
```

### 수동 사용
```bash
# 암호화
python3 env_crypto.py encrypt -i .env -o .env.encrypted -p "비밀번호"

# 복호화
python3 env_crypto.py decrypt -i .env.encrypted -o .env -p "비밀번호"
```

## 📊 출력 데이터

ETL 파이프라인은 다음 데이터를 생성합니다:

- **fact_sagemaker_costs**: 원시 데이터 + 파생 컬럼 (is_endpoint, is_notebook, is_training, is_spot, usage_hours)
- **agg_endpoint_hours**: Endpoint 리소스별 사용 시간 및 비용 집계
- **agg_training_cost**: Training 인스턴스별 비용 집계
- **agg_notebook_hours**: Notebook 인스턴스별 사용 시간 및 비용 집계
- **agg_spot_ratio**: Spot vs OnDemand 비용 비율
- **monthly_summary**: 월별 요약 통계

모든 데이터는 Parquet와 CSV 형식으로 저장됩니다.

**주의**: `.env` 파일은 민감한 정보를 포함하므로 Git에 커밋하지 마세요. 대신 `.env.encrypted` 파일을 커밋하고 필요할 때 복호화하여 사용하세요.
