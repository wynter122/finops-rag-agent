# Agent 구현 상세 문서

## 🤖 Router Agent 상세 분석

### 의도 분류 시스템

#### LLM 기반 분류기 (`intent_router.py`)

**핵심 특징**:
- **GPT-4o-mini 모델**: 빠르고 정확한 의도 분류
- **구조화된 프롬프트**: 명확한 분류 기준과 예시 제공
- **신뢰도 점수**: 0.0~1.0 범위의 분류 신뢰도 제공
- **분류 근거**: 한국어로 분류 이유 설명

**분류 기준**:
```python
# SQL 의도 (수치 분석)
- CUR/비용/사용량/집계/테이블/쿼리/월별 비용
- 예시: "이번달 SageMaker 비용", "Notebook 시간 합계"

# Docs 의도 (문서 설명)
- SageMaker 기능/설정/개념/가이드/튜토리얼/레퍼런스
- 예시: "Studio 설정 방법", "Serverless Inference 작동 방식"

# General 의도 (일반 대화)
- 인사/도움말/안내
- 예시: "안녕", "도움말", "감사합니다"
```

**성능 최적화**:
- `@lru_cache(maxsize=512)`: 동일 질문 캐싱
- **LangSmith 트레이싱**: 분류 과정 추적
- **에러 복구**: LLM 실패 시 기본값 반환

#### LangGraph 워크플로우 (`graph.py`)

**상태 관리**:
```python
class RouterState(TypedDict):
    question: str                    # 원본 질문
    intent: IntentType              # 분류된 의도
    intent_confidence: float        # 신뢰도 점수
    intent_reason: str              # 분류 근거
    sql_result: Dict[str, Any]      # SQL Agent 결과
    docs_result: Dict[str, Any]     # Docs Agent 결과
    general_result: Dict[str, Any]  # General Agent 결과
    final_result: Dict[str, Any]    # 최종 응답
```

**그래프 구조**:
```
prepare → route → dispatch_{intent} → END
```

**조건부 라우팅**:
- 의도별 분기 처리
- 에러 핸들링 및 복구
- 결과 통합 및 반환

## 🧮 SQL Agent 상세 분석

### NL2SQL 변환 시스템

#### 자연어 → SQL 변환 (`nl2sql.py`)

**핵심 기능**:
- **스키마 인식**: Parquet 파일 스키마 자동 분석
- **컨텍스트 제공**: 테이블 구조 및 컬럼 정보 포함
- **안전한 쿼리**: 읽기 전용 SQL만 생성
- **월별 데이터**: 자동으로 해당 월 데이터 선택

**프롬프트 구조**:
```python
# 시스템 프롬프트
- 스키마 정보 제공
- 쿼리 제약사항 명시
- 예시 쿼리 포함

# 사용자 질문
- 자연어 질문 입력

# 컨텍스트
- 테이블 구조
- 컬럼 설명
- 샘플 데이터
```

#### SQL 실행기 (`executor.py`)

**안전성 보장**:
- **읽기 전용**: SELECT 쿼리만 허용
- **시간 제한**: 쿼리 실행 시간 제한
- **메모리 제한**: 대용량 결과 처리 제한
- **에러 처리**: SQL 오류 시 graceful degradation

**성능 최적화**:
- **Parquet 최적화**: 컬럼형 저장 형식 활용
- **인덱싱**: 자동 인덱스 생성
- **캐싱**: 자주 사용되는 쿼리 결과 캐싱

#### 결과 요약 (`summary.py`)

**응답 구조화**:
```python
{
    "answer": "한국어 요약 답변",
    "sql": "실행된 SQL 쿼리",
    "numeric_summary": {
        "total_cost": 1234.56,
        "service_breakdown": {...},
        "trend": "증가/감소/유지"
    },
    "sample_rows": [...],  # 샘플 데이터
    "metadata": {
        "source_files": [...],
        "execution_time": 1.23,
        "row_count": 1000
    }
}
```

## 📚 Docs Agent 상세 분석

### Self-RAG 시스템

#### 멀티스텝 RAG 워크플로우 (`graph.py`)

**핵심 특징**:
- **Self-RAG**: 답변 품질 자동 평가
- **웹 검색 보완**: 문서 부족 시 실시간 검색
- **품질 기반 분기**: 점수에 따른 동적 워크플로우

**워크플로우 단계**:
```
1. 벡터 검색 → 컨텍스트 추출
2. 답변 생성 → 품질 평가
3. 조건부 분기:
   - 고품질(≥6점): 최종 답변
   - 저품질(<6점): 웹 검색 → 재생성
4. 최종 답변 반환
```

#### 품질 평가 시스템

**평가 기준** (0-10점):
- **완성도**: 질문에 대한 답변 완전성
- **정확성**: 답변의 정확성과 신뢰성
- **구체성**: 구체적이고 실용적인 정보 포함
- **명확성**: 이해하기 쉽고 명확한 설명

**분기 조건**:
```python
needs_web_search = (
    overall_score < 6 or
    any_score < 4 or
    answer_too_short or
    incomplete_answer
)
```

#### 벡터 검색 시스템 (`retriever.py`)

**검색 엔진**:
- **Chroma**: 로컬 벡터 데이터베이스
- **OpenAI Embeddings**: text-embedding-3-small 모델
- **유사도 점수**: 코사인 유사도 기반

**검색 최적화**:
- **하이브리드 검색**: 키워드 + 시맨틱 검색
- **재순위화**: LLM 기반 결과 재순위
- **중복 제거**: 유사한 컨텍스트 제거
- **컨텍스트 윈도우**: 적절한 길이로 조정

**검색 파라미터**:
```python
{
    "top_k": 10,           # 검색 결과 수
    "score_threshold": 0.7, # 유사도 임계값
    "rerank_top_k": 5,     # 재순위화 대상 수
    "max_context_length": 4000  # 컨텍스트 최대 길이
}
```

#### 웹 검색 보완

**Tavily Search 연동**:
- **실시간 검색**: 최신 정보 수집
- **신뢰도 필터링**: 신뢰할 수 있는 소스만 사용
- **결과 통합**: 문서 + 웹 검색 결과 종합

**검색 전략**:
```python
# 검색 쿼리 생성
search_query = f"AWS SageMaker {question}"

# 검색 파라미터
{
    "search_depth": "advanced",
    "include_domains": ["aws.amazon.com", "docs.aws.amazon.com"],
    "max_results": 5
}
```

### 문서 처리 시스템

#### 웹 스크래퍼 (`web_scraper.py`)

**수집 대상**:
- AWS SageMaker 공식 문서
- Cloud Radar 문서
- 관련 블로그 및 가이드

**처리 파이프라인**:
```
URL 수집 → HTML 파싱 → 텍스트 추출 → 청킹 → 임베딩 → 저장
```

#### 문서 인덱싱 (`ingest.py`)

**청킹 전략**:
- **의미적 청킹**: 문장/단락 단위 분할
- **오버랩**: 청크 간 중복으로 컨텍스트 유지
- **메타데이터**: 출처, 섹션, 버전 정보 포함

**임베딩 최적화**:
- **배치 처리**: 대량 문서 효율적 처리
- **에러 복구**: 실패한 문서 재처리
- **진행률 추적**: 처리 상태 모니터링

## 💬 General Agent

### 현재 구현 상태
- **기본 구조**: LangGraph 기반 워크플로우 준비
- **확장 예정**: 일반 대화, 안내, 도움말 기능

### 향후 계획
- **대화 메모리**: 이전 대화 컨텍스트 유지
- **개인화**: 사용자별 맞춤 응답
- **멀티모달**: 이미지, 파일 등 다양한 입력 지원

## 🔄 ETL 시스템 상세 분석

### 데이터 파이프라인

#### Extract 단계 (`extract.py`)

**Redshift 연결**:
```python
# 연결 설정
{
    "host": "redshift-cluster.amazonaws.com",
    "port": 5439,
    "database": "cur_database",
    "user": "cur_user"
}

# CUR 쿼리 최적화
- 월별 파티션 활용
- 인덱스 기반 필터링
- 배치 처리로 메모리 효율성
```

**계약 관리**:
```python
# contracts.json 구조
{
    "cloud-radar-prod": {
        "name": "Cloud Radar Production",
        "accounts": ["123456789101", "112233445566"],
        "description": "Production 환경 계정들"
    }
}
```

#### Transform 단계 (`transform.py`)

**데이터 정규화**:
- **서비스 분류**: AWS 서비스별 자동 분류
- **비용 집계**: 시간/일/월 단위 집계
- **통계 계산**: 평균, 합계, 증감률 등

**스키마 생성**:
```python
# 자동 스키마 추론
{
    "tables": {
        "sagemaker_usage": {
            "columns": [...],
            "sample_data": [...],
            "statistics": {...}
        }
    }
}
```

#### Clean 단계 (`clean.py`)

**LLM 정규화**:
- **서비스명 정규화**: 다양한 표현을 표준명으로 통일
- **리소스명 정규화**: 인스턴스 타입, 리전명 등 표준화
- **품질 검증**: 데이터 일관성 및 정확성 확인

**정규화 예시**:
```
입력: "sagemaker notebook", "notebook instance", "SageMaker 노트북"
출력: "Amazon SageMaker Notebook Instance"
```

#### Store 단계 (`store.py`)

**Parquet 저장**:
- **컬럼형 압축**: 고성능 쿼리 지원
- **파티셔닝**: 월별/서비스별 파티션
- **메타데이터**: 처리 정보 및 통계 포함

**버전 관리**:
```python
# 디렉토리 구조
data/processed/
├── 202508/
│   ├── sagemaker_cur_202508.parquet
│   ├── manifest.json
│   └── schema.json
├── latest -> 202508/  # 심볼릭 링크
└── manifest.json      # 전체 매니페스트
```

## 🖥️ UI 시스템 상세 분석

### Streamlit 앱 구조

#### 메인 앱 (`app.py`)

**세션 관리**:
```python
# 세션 상태
{
    "history": [...],      # 대화 히스토리
    "settings": {...},     # 사용자 설정
    "debug_mode": False    # 디버그 모드
}
```

**에이전트 연동**:
- **Router Agent 호출**: 단일 진입점으로 모든 에이전트 접근
- **응답 처리**: 의도별 차별화된 UI 렌더링
- **에러 처리**: 사용자 친화적 에러 메시지

#### 컴포넌트 시스템

**Chat Message** (`chat_message.py`):
- **의도별 아이콘**: 시각적 구분
- **성능 메트릭**: 응답 시간 표시
- **추적 정보**: LangSmith trace ID 표시

**Citations** (`citations.py`):
- **참고문헌**: 문서 출처 표시
- **신뢰도**: 검색 점수 표시
- **링크**: 원본 문서 링크

**Metrics** (`metrics.py`):
- **수치 요약**: 비용 통계 표시
- **트렌드**: 증감 추이 표시
- **차트**: 시각적 데이터 표현

### 사용자 경험 (UX)

**실시간 채팅**:
- **자연스러운 대화**: 채팅 인터페이스
- **타이핑 표시**: 응답 생성 중 상태 표시
- **히스토리 유지**: 세션 간 대화 기록 보존

**의도별 UI**:
- **SQL 결과**: 표, 차트, 요약 통계
- **Docs 결과**: 참고문헌, 출처 링크
- **General 결과**: 간단한 텍스트 응답

**설정 옵션**:
- **디버그 모드**: 상세 정보 표시
- **참고문헌 표시**: 출처 정보 토글
- **메트릭 표시**: 수치 요약 토글

## 🚀 성능 최적화 상세

### 캐싱 전략

**LLM 응답 캐싱**:
```python
@lru_cache(maxsize=512)
def classify_intent(question: str) -> IntentResult:
    # 동일 질문에 대한 중복 LLM 호출 방지
```

**벡터 검색 캐싱**:
- **임베딩 캐싱**: 동일 텍스트 임베딩 재사용
- **검색 결과 캐싱**: 유사 질문 검색 결과 재사용
- **컨텍스트 캐싱**: 처리된 컨텍스트 메모리 저장

**스키마 캐싱**:
- **파일 스키마**: Parquet 파일 스키마 메모리 캐싱
- **JSON 스키마**: 생성된 스키마 JSON 캐싱
- **메타데이터 캐싱**: 파일 메타데이터 캐싱

### 병렬 처리

**ETL 배치 처리**:
- **청크 단위 처리**: 대용량 데이터를 청크로 분할
- **멀티프로세싱**: CPU 집약적 작업 병렬화
- **비동기 I/O**: 파일 읽기/쓰기 비동기 처리

**벡터 검색 병렬화**:
- **다중 쿼리**: 여러 검색 쿼리 동시 실행
- **배치 임베딩**: 여러 텍스트 동시 임베딩
- **결과 병합**: 병렬 검색 결과 통합

**웹 검색 비동기**:
- **동시 검색**: 여러 검색 엔진 동시 호출
- **타임아웃 관리**: 검색 시간 제한
- **결과 통합**: 비동기 검색 결과 종합

### 모니터링 및 추적

**LangSmith 트레이싱**:
```python
# 트레이싱 설정
config: RunnableConfig = {
    "tags": ["router", "intent", "llm"],
    "metadata": {"question": q[:200]}
}
```

**성능 메트릭**:
- **응답 시간**: 각 단계별 처리 시간 측정
- **처리량**: 초당 처리 가능한 요청 수
- **에러율**: 실패한 요청 비율
- **리소스 사용량**: CPU, 메모리, 네트워크 사용량

**에러 추적**:
- **상세 로깅**: 각 단계별 상세 로그
- **스택 트레이스**: 에러 발생 위치 추적
- **복구 메커니즘**: 자동 복구 및 대체 처리


## 🔮 향후 개발 계획

### 단기 개선 (1-3개월)

**General Agent 완전 구현**:
- [ ] 대화 메모리 시스템
- [ ] 개인화 기능
- [ ] 멀티모달 입력 지원

**대시보드 시각화 강화**:
- [ ] 인터랙티브 차트
- [ ] 실시간 데이터 업데이트
- [ ] 커스터마이징 가능한 대시보드

**성능 최적화**:
- [ ] 벡터 데이터베이스 최적화
- [ ] 쿼리 성능 향상
- [ ] 메모리 사용량 최적화

