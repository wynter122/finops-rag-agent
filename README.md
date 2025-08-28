# FinOps RAG Agent

클라우드 비용 최적화를 위한 RAG(Retrieval-Augmented Generation) 기반 AI 에이전트입니다.

## 🚀 기능

- **클라우드 비용 분석**: AWS SageMaker 비용 데이터 분석
- **RAG 기반 질의응답**: 문서 기반 지능형 응답 시스템
- **비용 최적화 추천**: AI 기반 비용 절감 방안 제안

## 📋 요구사항

- Python 3.12+
- uv (Python 패키지 관리자)

## 🛠️ 설치

1. **저장소 클론**
```bash
git clone <repository-url>
cd finops-rag-agent
```

2. **가상환경 생성 및 활성화**
```bash
uv venv --python 3.12
source .venv/bin/activate
```

3. **의존성 설치**
```bash
uv sync
```

## 🏃‍♂️ 실행

### 개발 서버 실행
```bash
uv run uvicorn app.main:app --reload
```

### 테스트 실행
```bash
uv run pytest
```

## 📁 프로젝트 구조

```
```

## 🔧 개발 환경 설정

```

## 📝 환경 변수

`.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Cloud Providers
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# Database
DATABASE_URL=your_database_url
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

**주의**: `.env` 파일은 민감한 정보를 포함하므로 Git에 커밋하지 마세요. 대신 `.env.encrypted` 파일을 커밋하고 필요할 때 복호화하여 사용하세요.
