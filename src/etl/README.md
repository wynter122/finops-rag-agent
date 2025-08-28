# ETL (Extract, Transform, Load) 모듈

AWS SageMaker 비용 분석을 위한 ETL 파이프라인입니다. Redshift CUR 데이터를 추출하여 분석 가능한 형태로 변환하고 저장합니다.

## 📁 모듈 구조

```
src/etl/
├── __init__.py      # 모듈 초기화 및 API 노출
├── extract.py       # Redshift 데이터 추출
├── transform.py     # 데이터 변환 및 집계
├── clean.py         # LLM 정규화 (선택사항)
├── store.py         # 데이터 저장
├── runner.py        # ETL 실행기
└── README.md        
```

## 🚀 실행 방법

### 0. 사전 준비

#### 의존성 설치
```bash
# 프로젝트 루트에서 실행
uv sync
```

#### 디렉토리 생성
```bash
# 데이터 저장 디렉토리 생성
mkdir -p data/raw data/processed
```

#### 환경변수 설정
```bash
# .env 파일 생성 및 설정
cp .env.example .env  # 예시 파일이 있는 경우
# 또는 직접 .env 파일 생성
```

### 1. 기본 실행

#### 메인 실행 파일 사용 (권장)
```bash
python -m src.run_etl --billing-ym 202508 --accounts 123456789101,112233445566
```

#### 직접 runner.py 실행
```bash
python src/etl/runner.py --billing-ym 202508 --accounts 123456789101,112233445566
```

### 2. 파라미터 설명

#### 필수 파라미터
- `--billing-ym`: 청구 연월
  ```bash
  --billing-ym 202508    # 2025년 8월
  --billing-ym 2025-08   # 동일 (하이픈 포함 가능)
  ```

#### 선택 파라미터
- `--accounts`: AWS 계정 ID 목록
  ```bash
  --accounts 123456789101,112233445566,987654321987
  ```

- `--contract`: 계약 ID 사용 (contracts.json에서 정의)
  ```bash
  --contract cloud-radar-prod
  ```

- `--input-csv`: 로컬 CSV 파일 사용 (Redshift 대신)
  ```bash
  --input-csv data/raw/sagemaker_cur_sample.csv
  ```

- `--limit`: Redshift 쿼리 제한 (디버그용)
  ```bash
  --limit 1000
  ```

- `--list-contracts`: 사용 가능한 계약 목록 출력
  ```bash
  --list-contracts
  ```

### 3. 실행 예시

#### Redshift에서 직접 추출
```bash
# 기본 실행
python -m src.run_etl --billing-ym 202508 --accounts 123456789101,112233445566

# 계약 사용
python -m src.run_etl --billing-ym 202508 --contract cloud-radar-prod

# 디버그용 제한
python -m src.run_etl --billing-ym 202508 --accounts 123456789101 --limit 1000
```

#### 로컬 CSV 파일 사용
```bash
python -m src.run_etl --billing-ym 202508 \
  --accounts 123456789101,112233445566 \
  --input-csv data/raw/sagemaker_cur_sample.csv
```

#### 계약 목록 확인
```bash
python -m src.run_etl --list-contracts
```

## 🔧 모듈별 기능

### extract.py - 데이터 추출

Redshift에서 SageMaker CUR 데이터를 추출합니다.

#### 주요 함수
- `extract_cur_from_redshift()`: Redshift에서 CUR 데이터 추출
- `load_raw_from_csv()`: 로컬 CSV 파일에서 데이터 로드
- `save_raw()`: 원시 데이터를 Parquet/CSV로 저장

#### 추출되는 컬럼
- 청구 정보: `bill_billingperiodstartdate`, `bill_billingperiodenddate`, `billing_ym`
- 계정/리소스: `lineitem_usageaccountid`, `lineitem_resourceid`
- 사용량/비용: `lineitem_usageamount`, `lineitem_unblendedcost`, `lineitem_blendedcost`
- 서비스 정보: `lineitem_productcode`, `lineitem_usagetype`, `lineitem_operation`
- 제품 정보: `product_productname`, `product_instancetype`, `product_region`
- 태그 정보: `usertag0` ~ `usertag9`

### transform.py - 데이터 변환

CUR 데이터를 분석 가능한 형태로 변환하고 집계합니다.

#### 생성되는 파생 컬럼
- `is_endpoint`: Endpoint 관련 사용량 여부
- `is_notebook`: Notebook 관련 사용량 여부
- `is_training`: Training 관련 사용량 여부
- `is_spot`: Spot 인스턴스 사용 여부
- `usage_hours`: 사용 시간 (시간 단위인 경우)

#### 생성되는 집계 테이블
1. **fact_sagemaker_costs**: 원시 데이터 + 파생 컬럼
2. **agg_endpoint_hours**: Endpoint 리소스별 사용 시간 및 비용
3. **agg_training_cost**: Training 인스턴스별 비용
4. **agg_notebook_hours**: Notebook 인스턴스별 사용 시간 및 비용
5. **agg_spot_ratio**: Spot vs OnDemand 비용 비율
6. **monthly_summary**: 월별 요약 통계

### clean.py - LLM 정규화 (선택사항)

OpenAI를 사용하여 사용 타입을 정규화합니다.

#### 기능
- SageMaker 사용 타입을 카테고리별로 분류
- 캐싱을 통한 성능 최적화
- 규칙 기반 정규화로 폴백

#### 카테고리
- **Endpoint**: 추론/인퍼런스 관련
- **Notebook**: 개발/실험용 노트북
- **Training**: 모델 훈련 관련
- **Processing**: 데이터 처리/전처리
- **Other**: 기타

### store.py - 데이터 저장

처리된 데이터를 다양한 형식으로 저장합니다.

#### 저장 형식
- **Parquet**: 압축된 컬럼 기반 형식 (기본)
- **CSV**: 검증 및 호환성을 위한 텍스트 형식

#### 생성되는 파일
- `manifest.json`: 메타데이터 및 파일 목록
- `latest/`: 최신 데이터에 대한 심볼릭 링크

## 📊 출력 데이터 구조

```
data/
├── raw/
│   ├── sagemaker_cur_202508.parquet    # 원시 데이터
│   └── sagemaker_cur_202508.csv
└── processed/
    └── 202508/
        ├── fact_sagemaker_costs.parquet    # 원시 + 파생 컬럼
        ├── fact_sagemaker_costs.csv
        ├── agg_endpoint_hours.parquet      # Endpoint 집계
        ├── agg_endpoint_hours.csv
        ├── agg_training_cost.parquet       # Training 집계
        ├── agg_training_cost.csv
        ├── agg_notebook_hours.parquet      # Notebook 집계
        ├── agg_notebook_hours.csv
        ├── agg_spot_ratio.parquet          # Spot 비율
        ├── agg_spot_ratio.csv
        ├── monthly_summary.parquet         # 월별 요약
        ├── monthly_summary.csv
        └── manifest.json                   # 메타데이터
```

## ⚙️ 환경 설정

### 필수 환경변수 (.env 파일)

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
```

### 선택 환경변수

```env
# LLM 정규화 설정
USE_LLM_NORMALIZATION=false
OPENAI_API_KEY=sk-your-openai-api-key
```

## 🔒 보안 및 안전성

### 중복 실행 방지
- ETL 락으로 동시 실행 방지 (5분 타임아웃)
- 파일 기반 락 메커니즘

### 에러 처리
- 상세한 로그 출력
- 예외 발생 시 명확한 에러 메시지
- 부분 실패 시에도 안전한 종료

### 데이터 검증
- 매니페스트 파일로 데이터 무결성 확인
- 행 수 및 파일 크기 정보 포함


## 로그 확인

```bash
# 상세 로그 확인
python -m src.run_etl --billing-ym 202508 --accounts 123456789101 2>&1 | tee etl.log

# 특정 단계 로그 필터링
grep "Redshift" etl.log
grep "변환" etl.log
```

## 📈 성능 최적화

### 추출 최적화
- 필요한 컬럼만 선택하여 네트워크 트래픽 최소화
- SageMaker 관련 데이터만 필터링

### 변환 최적화
- 벡터화된 연산 사용
- 메모리 효율적인 집계

### 저장 최적화
- Parquet 형식으로 압축 저장
- CSV는 검증용으로만 사용

## 🔄 API 사용

ETL 모듈을 Python 코드에서 직접 사용할 수 있습니다:

```python
from src.etl import extract_cur_from_redshift, transform_all, write_processed

# 데이터 추출
df_raw = extract_cur_from_redshift("202508", ["123456789101"])

# 데이터 변환
dfs_transformed = transform_all(df_raw)

# 데이터 저장
output_paths = get_output_paths("202508")
write_processed(dfs_transformed, "202508", output_paths)
```