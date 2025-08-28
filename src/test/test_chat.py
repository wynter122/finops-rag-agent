#!/usr/bin/env python3
"""
SageMaker 비용 챗봇 테스트 스크립트
새로운 멀티에이전트 구조에 맞게 수정
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agent import router_ask
from src.agent.sql_agent import get_available_months, get_schema_info
from src.agent.general_agent.graph import ask as general_ask


def test_general_agent():
    """General Agent LLM 기반 응답 테스트"""
    print("=== General Agent 테스트 ===")
    
    test_cases = [
        ("안녕하세요", "인사"),
        ("도움말을 보여주세요", "도움말"),
        ("이 시스템은 어떻게 사용하나요?", "사용법 안내"),
        ("무엇을 할 수 있어요?", "기능 안내"),
        ("감사합니다", "감사 응답"),
        ("비용이 얼마인가요?", "라우팅 안내"),
        ("SageMaker 설정 방법을 알려주세요", "라우팅 안내"),
        ("테스트 질문입니다", "일반 응답")
    ]
    
    for question, expected_type in test_cases:
        print(f"\n질문: {question}")
        print(f"예상 유형: {expected_type}")
        try:
            result = general_ask(question)
            print(f"의도: {result.get('intent', 'unknown')}")
            print(f"답변: {result['answer']}")
            print(f"오류: {result.get('error', False)}")
        except Exception as e:
            print(f"오류: {e}")
    
    print()


def test_general_agent_routing():
    """General Agent 라우팅 안내 테스트"""
    print("=== General Agent 라우팅 안내 테스트 ===")
    
    routing_test_cases = [
        ("8월 비용이 얼마인가요?", "SQL Agent로 라우팅 안내"),
        ("SageMaker 설정 문서를 보여주세요", "Docs Agent로 라우팅 안내"),
        ("Notebook 인스턴스 비용 분석", "SQL Agent로 라우팅 안내"),
        ("API 문서는 어디서 찾을 수 있나요?", "Docs Agent로 라우팅 안내"),
        ("총 비용 통계를 알려주세요", "SQL Agent로 라우팅 안내")
    ]
    
    for question, expected_behavior in routing_test_cases:
        print(f"\n질문: {question}")
        print(f"예상 동작: {expected_behavior}")
        try:
            result = general_ask(question)
            print(f"답변: {result['answer']}")
            
            # 라우팅 키워드 확인
            has_sql_mention = "SQL" in result['answer'] or "sql" in result['answer'].lower()
            has_docs_mention = "Docs" in result['answer'] or "docs" in result['answer'].lower()
            
            if has_sql_mention:
                print("✅ SQL Agent 라우팅 안내 포함")
            elif has_docs_mention:
                print("✅ Docs Agent 라우팅 안내 포함")
            else:
                print("❌ 라우팅 안내 없음")
                
        except Exception as e:
            print(f"오류: {e}")
    
    print()


def test_general_agent_response_length():
    """General Agent 응답 길이 제한 테스트"""
    print("=== General Agent 응답 길이 테스트 ===")
    
    long_questions = [
        "이 시스템에 대해 자세히 설명해주세요. 모든 기능과 사용법을 포함해서 알려주세요.",
        "AWS SageMaker의 모든 서비스와 비용 구조, 그리고 최적화 방법에 대해 상세히 설명해주세요.",
        "FinOps와 비용 관리에 대한 모든 정보를 제공해주세요."
    ]
    
    for question in long_questions:
        print(f"\n질문: {question[:50]}...")
        try:
            result = general_ask(question)
            response_length = len(result['answer'])
            print(f"응답 길이: {response_length}자")
            print(f"응답: {result['answer'][:100]}...")
            
            if response_length <= 1000:
                print("✅ 응답 길이 제한 준수")
            else:
                print("❌ 응답 길이 초과")
                
        except Exception as e:
            print(f"오류: {e}")
    
    print()


def test_general_agent_error_handling():
    """General Agent 오류 처리 테스트"""
    print("=== General Agent 오류 처리 테스트 ===")
    
    # 빈 질문 테스트
    try:
        result = general_ask("")
        print(f"빈 질문 응답: {result['answer']}")
    except Exception as e:
        print(f"빈 질문 오류: {e}")
    
    # 매우 긴 질문 테스트
    long_question = "테스트" * 1000
    try:
        result = general_ask(long_question)
        print(f"긴 질문 응답 길이: {len(result['answer'])}자")
    except Exception as e:
        print(f"긴 질문 오류: {e}")
    
    # 특수 문자 포함 질문 테스트
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    try:
        result = general_ask(special_chars)
        print(f"특수 문자 질문 응답: {result['answer'][:50]}...")
    except Exception as e:
        print(f"특수 문자 질문 오류: {e}")
    
    print()


def test_schema_info():
    """스키마 정보 테스트"""
    print("=== 스키마 정보 테스트 ===")
    
    # 사용 가능한 월 확인
    months = get_available_months()
    print(f"사용 가능한 월: {months}")
    
    # latest 스키마 정보 확인
    schema_info = get_schema_info("latest")
    print(f"Latest 스키마 정보:")
    print(json.dumps(schema_info, indent=2, ensure_ascii=False))
    
    print()


def test_basic_questions():
    """기본 질문 테스트"""
    print("=== 기본 질문 테스트 ===")
    
    questions = [
        "이번달 SageMaker 비용이 얼마인가요?",
        "SageMaker 서비스별 비용을 알려주세요",
        "가장 비용이 많이 든 서비스는 무엇인가요?",
        "Notebook 인스턴스의 비용 분포를 알려주세요."
    ]
    
    for question in questions:
        print(f"\n질문: {question}")
        try:
            result = router_ask(question)
            print(f"의도: {result.get('intent', 'unknown')}")
            print(f"답변: {result['answer']}")
            if 'sql' in result:
                print(f"SQL: {result['sql']}")
                print(f"행 수: {result['row_count']}")
                if result['sample_rows']:
                    print(f"샘플 데이터: {result['sample_rows'][:2]}")
        except Exception as e:
            print(f"오류: {e}")
    
    print()


def test_debug_mode():
    """디버그 모드 테스트"""
    print("=== 디버그 모드 테스트 ===")
    
    question = "이번달 총 비용은 얼마인가요?"
    print(f"질문: {question}")
    
    try:
        result = router_ask(question)
        print(f"의도: {result.get('intent', 'unknown')}")
        print(f"답변: {result['answer']}")
        if 'sql' in result:
            print(f"SQL: {result['sql']}")
            print(f"행 수: {result['row_count']}")
            if result['sample_rows']:
                print(f"샘플 데이터: {result['sample_rows'][:2]}")
    except Exception as e:
        print(f"오류: {e}")
    
    print()


def test_error_handling():
    """에러 처리 테스트"""
    print("=== 에러 처리 테스트 ===")
    
    # 존재하지 않는 월 테스트 (현재는 month 파라미터 지원 안함)
    try:
        result = router_ask("테스트 질문")
        print(f"일반 테스트: {result['answer']}")
    except Exception as e:
        print(f"일반 테스트 오류: {e}")
    
    print()


def test_multiple_intents():
    """다양한 의도 테스트"""
    print("=== 다양한 의도 테스트 ===")
    
    test_cases = [
        ("8월 SageMaker 비용이 얼마인가요?", "SQL"),
        ("SageMaker 설정 방법을 알려주세요", "Docs"),
        ("안녕하세요", "General"),
        ("도움말을 보여주세요", "General"),
        ("Notebook 인스턴스 비용 분석", "SQL"),
        ("API 문서는 어디서 찾을 수 있나요?", "Docs")
    ]
    
    for question, expected_intent in test_cases:
        print(f"\n질문: {question}")
        print(f"예상 의도: {expected_intent}")
        try:
            result = router_ask(question)
            actual_intent = result.get('intent', 'unknown')
            print(f"실제 의도: {actual_intent}")
            print(f"답변: {result['answer'][:100]}...")
            print(f"정확도: {'✅' if actual_intent.lower() in expected_intent.lower() else '❌'}")
        except Exception as e:
            print(f"오류: {e}")
    
    print()


def ask_single_question(question: str, debug: bool = False):
    """단일 질문을 처리하는 함수"""
    print(f"질문: {question}")
    print(f"디버그 모드: {debug}")
    print("-" * 50)
    
    try:
        result = router_ask(question)
        
        print(f"의도: {result.get('intent', 'unknown')}")
        print(f"답변: {result['answer']}\n")
        
        if 'sql' in result:
            print(f"SQL: {result['sql']}\n")
            print(f"SQL 쿼리 결과 행 수: {result['row_count']}")
            
            if result['sample_rows']:
                print(f"SQL 쿼리 결과 샘플 데이터: {result['sample_rows'][:3]}")
        
        if debug:
            print(f"\n전체 응답:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print(f"오류: {e}")
        return None


def main():
    """메인 테스트 함수"""
    parser = argparse.ArgumentParser(description="SageMaker 비용 챗봇 테스트")
    parser.add_argument("--question", "-q", type=str, help="질문할 내용")
    parser.add_argument("--debug", "-d", action="store_true", help="디버그 모드 활성화")
    parser.add_argument("--test-all", "-t", action="store_true", help="모든 테스트 실행")
    parser.add_argument("--test-intents", "-i", action="store_true", help="의도 분류 테스트")
    parser.add_argument("--test-general", "-g", action="store_true", help="General Agent 테스트")
    parser.add_argument("--test-general-routing", "-r", action="store_true", help="General Agent 라우팅 테스트")
    parser.add_argument("--test-general-length", "-l", action="store_true", help="General Agent 응답 길이 테스트")
    parser.add_argument("--test-general-error", "-e", action="store_true", help="General Agent 오류 처리 테스트")
    
    args = parser.parse_args()
    
    print("SageMaker 비용 챗봇 테스트 시작\n")
    
    # 환경 변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("LLM 기능을 테스트하려면 API 키를 설정해주세요.\n")
    
    # 데이터 디렉토리 확인 (프로젝트 루트 기준)
    data_dir = project_root / "data" / "processed"
    if not data_dir.exists():
        print(f"경고: {data_dir} 디렉토리가 존재하지 않습니다.")
        print("ETL 데이터를 먼저 생성해주세요.\n")
        return
    
    # 질문이 제공된 경우 단일 질문 처리
    if args.question:
        ask_single_question(args.question, args.debug)
        return
    
    # General Agent 테스트들
    if args.test_general:
        test_general_agent()
        return
    
    if args.test_general_routing:
        test_general_agent_routing()
        return
    
    if args.test_general_length:
        test_general_agent_response_length()
        return
    
    if args.test_general_error:
        test_general_agent_error_handling()
        return
    
    # 모든 테스트 실행
    if args.test_all:
        test_schema_info()
        test_basic_questions()
        test_debug_mode()
        test_error_handling()
        test_multiple_intents()
        test_general_agent()
        test_general_agent_routing()
        test_general_agent_response_length()
        test_general_agent_error_handling()
        print("테스트 완료!")
        return
    
    # 의도 분류 테스트
    if args.test_intents:
        test_multiple_intents()
        return
    
    # 기본 안내 메시지
    print("사용법:")
    print("  python -m src.test.test_chat --question '이번달 총 비용은 얼마인가요?'")
    print("  python -m src.test.test_chat -q 'Notebook 인스턴스별 비용을 알려주세요' -d")
    print("  python -m src.test.test_chat --test-all")
    print("  python -m src.test.test_chat --test-intents")
    print("  python -m src.test.test_chat --test-general")
    print("  python -m src.test.test_chat --test-general-routing")
    print("  python -m src.test.test_chat --test-general-length")
    print("  python -m src.test.test_chat --test-general-error")
    print("\n사용 가능한 월:", get_available_months())


if __name__ == "__main__":
    main()
