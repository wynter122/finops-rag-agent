#!/usr/bin/env python3
"""
LLM 응답 디버그 스크립트
새로운 멀티에이전트 구조에 맞게 수정
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agent.sql_agent import get_schema_info, generate_sql


def debug_llm_response():
    """LLM 응답 디버그"""
    print("LLM 응답 디버그 시작\n")
    
    # 스키마 정보 가져오기
    schema_info = get_schema_info("latest")
    schema_json = schema_info["schema"]
    
    print(f"스키마 정보 길이: {len(schema_json)}")
    print(f"스키마 미리보기: {schema_json[:200]}...")
    print()
    
    # 테스트 질문
    question = "이번달 SageMaker 비용이 얼마인가요?"
    print(f"질문: {question}")
    
    try:
        # LLM 응답 생성 (이제 직접 SQL 반환)
        print("LLM 호출 중...")
        sql = generate_sql(question, schema_json, schema_info["base_dir"])
        print(f"생성된 SQL: {sql}")
        print(f"SQL 길이: {len(sql)}")
        print()
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    debug_llm_response()


if __name__ == "__main__":
    main()
