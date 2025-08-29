#!/usr/bin/env python3
"""
Docs Agent 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from src.agent.docs_agent.graph import ask

# .env 파일 로드
load_dotenv()

def test_docs_agent():
    """Docs Agent 테스트"""
    print("🔍 Docs Agent 테스트 시작...")
    print("=" * 60)
    
    # 테스트 질문들
    test_questions = [
        "SageMaker Canvas란 무엇인가요?",
        "SageMaker에서 모델 훈련은 어떻게 하나요?",
        "SageMaker Studio의 기능은 무엇인가요?",
        "SageMaker의 비용은 어떻게 계산되나요?",
        "SageMaker에서 서버리스 추론은 어떻게 사용하나요?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 테스트 {i}: {question}")
        print("-" * 50)
        
        try:
            result = ask(question)
            
            if result.get("error"):
                print(f"❌ 오류: {result.get('message', '알 수 없는 오류')}")
            else:
                print(f"✅ 답변:")
                print(result.get("answer", "답변이 없습니다"))
                
                # 컨텍스트 정보도 표시 (간단히)
                context = result.get("context", "")
                if context:
                    if isinstance(context, list):
                        print(f"\n📚 참조 문서 수: {len(context)}개")
                    else:
                        print(f"\n📚 컨텍스트 길이: {len(str(context))}자")
            
        except Exception as e:
            print(f"❌ 예외 발생: {e}")
        
        print()

if __name__ == "__main__":
    test_docs_agent()
