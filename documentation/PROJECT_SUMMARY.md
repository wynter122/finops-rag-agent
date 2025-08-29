# FinOps RAG Agent 프로젝트 요약

## 🎯 프로젝트 개요

**FinOps RAG Agent**는 AWS SageMaker 비용 최적화를 위한 AI 기반 멀티에이전트 시스템입니다. 사용자가 자연어로 질문하면 자동으로 의도를 분석하여 적절한 전문 에이전트로 라우팅하고, 각 에이전트는 특화된 기능을 제공합니다.

## 🏗️ 핵심 아키텍처

```
사용자 질문 → Router Agent → 의도 분류 → 전문 에이전트 → 응답
```

### 3가지 전문 에이전트

1. **🧮 SQL Agent**: CUR 데이터 기반 비용 분석
2. **📚 Docs Agent**: SageMaker 문서 기반 RAG Q&A  
3. **💬 General Agent**: 일반 대화 및 안내

## 🚀 주요 특징

### 🤖 지능형 라우팅
- **LLM 기반 의도 분류**: GPT-4o-mini로 정확한 의도 파악
- **신뢰도 점수**: 분류 결과의 신뢰도 제공
- **자동 분기**: 의도에 따른 자동 에이전트 선택

### 📊 비용 분석 (SQL Agent)
- **NL2SQL**: 자연어 → SQL 자동 변환
- **실시간 쿼리**: Parquet 기반 고성능 분석
- **구조화된 응답**: 표, 차트, 요약 통계 제공

### 📚 문서 Q&A (Docs Agent)
- **Self-RAG**: 답변 품질 자동 평가
- **웹 검색 보완**: 문서 부족 시 실시간 검색
- **벡터 검색**: Chroma + OpenAI Embeddings

### 🔄 데이터 파이프라인 (ETL)
- **Redshift 연동**: AWS CUR 데이터 추출
- **자동 변환**: 비용 데이터 정규화 및 집계
- **Parquet 저장**: 고성능 컬럼형 저장

### 🖥️ 사용자 인터페이스
- **Streamlit**: 실시간 채팅 인터페이스
- **의도별 UI**: SQL(🧮), Docs(📚), General(💬)
- **성능 메트릭**: 응답 시간 및 추적 정보

## 🛠️ 기술 스택

### AI/ML
- **LangChain**: LLM 체인 및 워크플로우
- **LangGraph**: 멀티에이전트 그래프 실행
- **GPT-4o-mini**: 의도 분류 및 답변 생성
- **OpenAI Embeddings**: 문서 벡터화

### 데이터
- **Chroma**: 벡터 데이터베이스
- **Pandas**: 데이터 처리 및 분석
- **PyArrow**: Parquet 파일 처리
- **AWS Redshift**: CUR 데이터 소스

### UI/UX
- **Streamlit**: 웹 인터페이스
- **LangSmith**: LLM 호출 추적

## 📈 성능 최적화

### 캐싱
- **LLM 응답 캐싱**: `@lru_cache` 데코레이터
- **벡터 검색 캐싱**: 임베딩 결과 재사용
- **스키마 캐싱**: 데이터 스키마 메모리 캐싱

### 병렬 처리
- **ETL 배치 처리**: 대용량 데이터 효율적 처리
- **벡터 검색 병렬화**: 다중 문서 동시 검색
- **웹 검색 비동기**: 실시간 정보 수집


## 📁 프로젝트 구조

```
finops-rag-agent/
├── src/
│   ├── agent/           # 멀티에이전트 시스템
│   │   ├── router/      # 의도 분류 및 라우팅
│   │   ├── sql_agent/   # CUR 데이터 분석
│   │   ├── docs_agent/  # 문서 RAG Q&A
│   │   └── general_agent/ # 일반 대화
│   ├── etl/             # 데이터 파이프라인
│   │   ├── extract.py   # Redshift 데이터 추출
│   │   ├── transform.py # 데이터 변환
│   │   ├── clean.py     # LLM 정규화
│   │   └── store.py     # 데이터 저장
│   └── ui/              # Streamlit 인터페이스
├── data/                # 데이터 저장소
│   ├── raw/             # 원시 데이터
│   ├── processed/       # 처리된 데이터
│   └── docs/            # 문서 데이터
└── docs/                # 프로젝트 문서
```

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 의존성 설치
uv sync

# 환경변수 설정
cp .env.example .env
```

### 2. ETL 실행
```bash
# CUR 데이터 처리
python -m src.run_etl --billing-ym 202508 --accounts 123456789101,112233445566
```

### 3. UI 실행
```bash
# Streamlit 앱 실행
streamlit run src/ui/app.py
```

## 💡 사용 예시

### 비용 분석 질문
```
사용자: "이번달 SageMaker 비용이 얼마나 나왔어요?"
→ SQL Agent → 비용 분석 결과 + 차트
```

### 문서 질문
```
사용자: "SageMaker Studio 설정 방법을 알려주세요"
→ Docs Agent → 문서 기반 답변 + 참고문헌
```

### 일반 질문
```
사용자: "안녕하세요, 도움말을 보여주세요"
→ General Agent → 안내 메시지
```

---

**FinOps RAG Agent**는 AWS SageMaker 비용 최적화를 위한 차세대 AI 솔루션입니다. 🚀
