#!/bin/bash

# FinOps RAG Agent Streamlit UI 실행 스크립트

echo "🚀 FinOps RAG Agent UI 시작 중..."

# 환경 변수 로드
if [ -f ".env" ]; then
    echo "📄 .env 파일 로드 중..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Streamlit 앱 실행
echo "🌐 Streamlit 서버 시작 중..."
echo "📍 접속 URL: http://localhost:8501"
echo ""

streamlit run src/ui/app.py --server.port 8501 --server.address 0.0.0.0
