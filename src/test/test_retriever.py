"""
Retriever 테스트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.docs_agent.retriever import retrieve, DocumentRetriever, get_retriever


def test_retrieve_function():
    """retrieve 함수 테스트"""
    print("🔍 retrieve 함수 테스트 시작...")
    
    # 테스트 질의
    test_questions = [
        "Training Compiler",
        "Warm Pools",
        "How it works",
        "존재하지 않는 기능에 대한 질문"  # 낮은 점수 예상
    ]
    
    for question in test_questions:
        print(f"\n📝 질의: {question}")
        
        try:
            result = retrieve(
                question=question,
                top_k=10,
                top_n=3,
                threshold=0.05  # 임계값을 더 낮춤
            )
            
            print(f"✅ 평균 점수: {result['avg_score']:.3f}")
            print(f"⏱️  응답 시간: {result['latency_ms']}ms")
            print(f"📊 컨텍스트 수: {len(result['contexts'])}")
            
            if result['contexts']:
                print("📄 상위 컨텍스트:")
                for i, ctx in enumerate(result['contexts'][:2]):
                    metadata = ctx['metadata']
                    print(f"  {i+1}. {metadata.get('title', 'Unknown')} - {metadata.get('section', '')}")
                    print(f"     점수: {ctx['score']:.3f}")
                    print(f"     텍스트: {ctx['text'][:100]}...")
            else:
                print("❌ 임계값 미달로 빈 컨텍스트 반환")
                
        except Exception as e:
            print(f"❌ 에러 발생: {e}")


def test_document_retriever_class():
    """DocumentRetriever 클래스 테스트"""
    print("\n🔍 DocumentRetriever 클래스 테스트 시작...")
    
    try:
        retriever = get_retriever()
        
        # search 메서드 테스트
        print("📝 search 메서드 테스트...")
        docs = retriever.search("Training Compiler", top_k=3)
        print(f"✅ 검색된 문서 수: {len(docs)}")
        
        # get_relevant_context 메서드 테스트
        print("📝 get_relevant_context 메서드 테스트...")
        context = retriever.get_relevant_context("Warm Pools", top_k=2)
        print(f"✅ 컨텍스트 길이: {len(context)} 문자")
        if context:
            print(f"📄 컨텍스트 미리보기: {context[:200]}...")
        else:
            print("❌ 빈 컨텍스트 반환")
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")


def test_error_handling():
    """에러 처리 테스트"""
    print("\n🔍 에러 처리 테스트 시작...")
    
    # 존재하지 않는 인덱스 디렉토리로 테스트
    try:
        result = retrieve(
            question="테스트",
            index_dir="존재하지_않는_경로",
            top_k=5,
            top_n=3
        )
        
        print(f"✅ 에러 처리 결과: {result.get('error', '에러 없음')}")
        print(f"✅ 빈 컨텍스트 반환: {len(result['contexts']) == 0}")
        
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {e}")


if __name__ == "__main__":
    print("🚀 Retriever 테스트 시작\n")
    
    # 1. retrieve 함수 테스트
    test_retrieve_function()
    
    # 2. DocumentRetriever 클래스 테스트
    test_document_retriever_class()
    
    # 3. 에러 처리 테스트
    test_error_handling()
    
    print("\n✅ 모든 테스트 완료!")

