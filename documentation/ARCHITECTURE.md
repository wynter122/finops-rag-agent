# FinOps RAG Agent 아키텍처 문서

## 📋 개요

FinOps RAG Agent는 AWS SageMaker 비용 최적화를 위한 멀티에이전트 시스템입니다. 사용자 질문의 의도를 자동으로 분류하여 적절한 전문 에이전트로 라우팅하고, 각 에이전트는 특화된 기능을 제공합니다.

## 🏗️ 전체 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │    │  Agent Layer    │    │   Data Layer    │
│   (Streamlit)   │◄──►│   (Router)      │◄──►│   (ETL/Store)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
            ┌───────▼────┐ ┌──▼──┐ ┌────▼────┐
            │ SQL Agent  │ │Docs │ │General  │
            │ (CUR 분석) │ │Agent│ │ Agent   │
            └───────────┘ └─────┘ └─────────┘
```

## 🤖 Agent Layer 구조

### 1. Router Agent (`src/agent/router/`)

**역할**: 사용자 질문의 의도를 분석하여 적절한 전문 에이전트로 라우팅

**핵심 구성요소**:
- **Intent Router** (`intent_router.py`): LLM 기반 의도 분류기
  - 3가지 의도 분류: `sql`, `docs`, `general`
  - GPT-4o-mini 모델 사용
  - 신뢰도 점수와 분류 근거 제공
  - 캐싱으로 성능 최적화

- **Router Graph** (`graph.py`): LangGraph 기반 워크플로우
  - 상태 기반 그래프 실행
  - 조건부 라우팅 (의도별 분기)
  - 에러 핸들링 및 복구

**라우팅 로직**:
```python
# 의도 분류 기준
- sql: CUR/비용/사용량/집계/테이블/쿼리 등 수치 분석
- docs: SageMaker 기능/설정/개념/가이드/튜토리얼
- general: 인사/도움말/안내/잡담
```

### 2. SQL Agent (`src/agent/sql_agent/`)

**역할**: CUR(Cloud Usage Report) 데이터 기반 비용 분석 및 쿼리

**핵심 구성요소**:
- **NL2SQL** (`nl2sql.py`): 자연어 → SQL 변환
- **Executor** (`executor.py`): 안전한 SQL 실행
- **Summary** (`summary.py`): 결과 요약 및 시각화
- **Schema Provider** (`schema_provider.py`): 데이터 스키마 관리

**워크플로우**:
```
질문 → NL2SQL → SQL 실행 → 결과 요약 → 응답
```

**특징**:
- Parquet 파일 기반 고성능 쿼리
- 월별 데이터 자동 선택
- 안전한 SQL 실행 (읽기 전용)
- 구조화된 응답 (표, 차트, 요약)

### 3. Docs Agent (`src/agent/docs_agent/`)

**역할**: SageMaker/Cloud Radar 공식 문서 기반 RAG Q&A

**핵심 구성요소**:
- **Retriever** (`retriever.py`): 벡터 검색 (Chroma + OpenAI Embeddings)
- **Graph** (`graph.py`): 멀티스텝 RAG 워크플로우
- **Web Scraper** (`web_scraper.py`): 웹 문서 수집
- **Ingest** (`ingest.py`): 문서 처리 및 인덱싱

**RAG 워크플로우**:
```
질문 → 벡터 검색 → 컨텍스트 추출 → 답변 생성 → 품질 평가 → 웹 검색(필요시) → 최종 답변
```

**특징**:
- **Self-RAG**: 답변 품질 자동 평가
- **웹 검색 보완**: 문서 부족 시 실시간 웹 검색
- **멀티소스**: 공식 문서 + 웹 검색 결과
- **품질 기반 분기**: 품질이 낮으면 웹 검색으로 보완

### 4. General Agent (`src/agent/general_agent/`)

**역할**: 일반적인 대화, 안내, 도움말 응답

**구현 상태**: 기본 구조만 구현됨 (향후 확장 예정)

## 🔄 ETL Layer 구조 (`src/etl/`)

### 개요
AWS Redshift의 CUR 데이터를 추출하여 분석 가능한 형태로 변환하고 저장하는 파이프라인

### 핵심 구성요소

#### 1. Extract (`extract.py`)
- **Redshift 연결**: AWS CUR 데이터 추출
- **계약 관리**: `contracts.json` 기반 계정 그룹 관리
- **CSV 지원**: 로컬 CSV 파일 입력 지원
- **배치 처리**: 대용량 데이터 효율적 처리

#### 2. Transform (`transform.py`)
- **데이터 정규화**: AWS 서비스별 비용 집계
- **스키마 생성**: 자동 스키마 추론 및 JSON 생성
- **통계 계산**: 월별/서비스별 사용량 통계
- **메타데이터 추가**: 처리 정보 및 타임스탬프

#### 3. Clean (`clean.py`)
- **LLM 정규화**: 서비스명, 리소스명 자동 정규화
- **품질 보정**: 데이터 일관성 및 정확성 향상
- **검증 및 테스트 필요**

#### 4. Store (`store.py`)
- **Parquet 저장**: 고성능 컬럼형 저장
- **매니페스트**: 처리된 데이터 메타데이터 관리
- **버전 관리**: 월별 데이터 버전 관리
- **심볼릭 링크**: 최신 데이터 자동 연결

#### 5. Runner (`runner.py`)
- **파이프라인 조율**: 전체 ETL 워크플로우 관리
- **에러 핸들링**: 단계별 에러 처리 및 복구
- **로깅**: 상세한 처리 로그 및 메트릭
- **락 메커니즘**: 중복 실행 방지

### ETL 워크플로우
```
Redshift CUR → Extract → Transform → Clean(옵션) → Store → 매니페스트 생성
```

### 실행 방법
```bash
# 기본 실행
python -m src.run_etl --billing-ym 202508 --accounts 123456789101,112233445566

# 계약 사용
python -m src.run_etl --billing-ym 202508 --contract cloud-radar-prod

# 로컬 CSV 사용
python -m src.run_etl --billing-ym 202508 --input-csv data/raw/sample.csv
```

## 🖥️ UI Layer 구조 (`src/ui/`)

### 개요
Streamlit 기반 웹 인터페이스로 사용자와 AI 에이전트 간의 상호작용 제공

### 핵심 구성요소

#### 1. 메인 앱 (`app.py`)
- **세션 관리**: 대화 히스토리 및 상태 관리
- **에이전트 연동**: Router Agent와 직접 통신
- **응답 렌더링**: 의도별 차별화된 UI 표시
- **설정 관리**: 사용자 설정 및 토글 옵션

#### 2. 컴포넌트 (`components/`)
- **Chat Message** (`chat_message.py`): 메시지 렌더링
- **Citations** (`citations.py`): 참고문헌 표시
- **Metrics** (`metrics.py`): 수치 요약 표시

#### 3. 유틸리티 (`utils/`)
- **Session** (`session.py`): 세션 상태 관리

### UI 특징
- **실시간 채팅**: 자연스러운 대화형 인터페이스
- **의도별 아이콘**: SQL(🧮), Docs(📚), General(💬)
- **성능 메트릭**: 응답 시간 및 추적 ID 표시
- **확장 가능**: 디버그 모드 및 추가 정보 표시

## 🔧 기술 스택

### 핵심 기술
- **LangChain**: LLM 체인 및 워크플로우
- **LangGraph**: 멀티에이전트 그래프 실행
- **Chroma**: 벡터 데이터베이스
- **Streamlit**: 웹 UI 프레임워크
- **Pandas**: 데이터 처리 및 분석
- **PyArrow**: Parquet 파일 처리

### AI/ML 모델
- **GPT-4o-mini**: 의도 분류 및 답변 생성
- **OpenAI Embeddings**: 문서 벡터화
- **Tavily Search**: 웹 검색

### 데이터베이스
- **AWS Redshift**: CUR 데이터 소스
- **Chroma**: 문서 벡터 스토어
- **SQLite**: 메타데이터 저장

## 🚀 성능 최적화

### 캐싱 전략
- **LLM 응답 캐싱**: `@lru_cache` 데코레이터
- **벡터 검색 캐싱**: 임베딩 결과 재사용
- **스키마 캐싱**: 데이터 스키마 메모리 캐싱

### 병렬 처리
- **ETL 배치 처리**: 대용량 데이터 효율적 처리
- **벡터 검색 병렬화**: 다중 문서 동시 검색
- **웹 검색 비동기**: 실시간 정보 수집

### 모니터링
- **LangSmith 트레이싱**: LLM 호출 추적
- **성능 메트릭**: 응답 시간 및 처리량 측정
- **에러 로깅**: 상세한 에러 추적 및 복구

### 에러 처리
- **Graceful Degradation**: 부분 실패 시 기본 응답
- **재시도 메커니즘**: 일시적 오류 자동 복구
- **락 메커니즘**: 중복 실행 방지

### 개선 필요 사항
- [ ] 프롬프트 엔지니어링 고도화
- [ ] 세션 및 사용자 유지 기능 강화
- [ ] CUR 분석에 생성형 ai 도입
