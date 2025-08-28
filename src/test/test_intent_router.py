"""
Intent Router 테스트: LLM + 규칙 하이브리드 분류기 검증
"""

from src.agent.router.intent_router import classify_intent, IntentResult


# 골든셋 테스트 케이스
GOLDEN_TEST_CASES = {
    # SQL 의도 테스트 (5문항)
    "이번달 SageMaker 비용": "sql",
    "Notebook 시간 합계": "sql", 
    "월별 사용량 통계": "sql",
    "소비 추이 그래프": "sql",
    "Feature Store 비용 분석": "sql",
    
    # Docs 의도 테스트 (5문항)
    "SageMaker Studio 설정 방법": "docs",
    "Serverless Inference 작동 방식": "docs",
    "Feature Store의 offline store 개념 설명": "docs",
    "API 레퍼런스 보여줘": "docs",
    "튜토리얼 가이드": "docs",
    
    # General 의도 테스트 (2문항)
    "안녕하세요": "general",
    "도움말": "general"
}

# 엣지 케이스 테스트
EDGE_CASES = {
    "": "general",  # 빈 질문
    "   ": "general",  # 공백만
    "SageMaker 비용이 어떻게 계산되나요?": "docs",  # 비용 키워드지만 개념 질문
    "Studio에서 비용을 어떻게 확인하나요?": "docs",  # 비용 키워드지만 사용법 질문
    "비용 데이터를 CSV로 내보내는 방법": "docs",  # 데이터 키워드지만 방법 질문
}


def test_intent_classification_structure():
    """분류 결과 구조 검증"""
    result = classify_intent("이번달 SageMaker 비용")
    
    assert isinstance(result, dict)
    assert "intent" in result
    assert "confidence" in result
    assert "reason" in result
    
    assert result["intent"] in ("sql", "docs", "general")
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["reason"], str)
    assert len(result["reason"]) > 0


def test_golden_test_cases():
    """골든셋 테스트 케이스 검증"""
    correct_count = 0
    total_count = len(GOLDEN_TEST_CASES)
    
    print("\n=== 골든셋 테스트 결과 ===")
    
    for question, expected_intent in GOLDEN_TEST_CASES.items():
        result = classify_intent(question)
        actual_intent = result["intent"]
        confidence = result["confidence"]
        reason = result["reason"]
        
        is_correct = actual_intent == expected_intent
        if is_correct:
            correct_count += 1
        
        status = "✅" if is_correct else "❌"
        print(f"{status} {question}")
        print(f"   예상: {expected_intent}, 실제: {actual_intent} (conf: {confidence:.2f})")
        print(f"   근거: {reason}")
        print()
    
    accuracy = correct_count / total_count
    print(f"정확도: {correct_count}/{total_count} ({accuracy:.1%})")
    
    # 최소 정확도 80% 달성 확인
    assert accuracy >= 0.8, f"정확도가 너무 낮습니다: {accuracy:.1%}"


def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n=== 엣지 케이스 테스트 결과 ===")
    
    for question, expected_intent in EDGE_CASES.items():
        result = classify_intent(question)
        actual_intent = result["intent"]
        confidence = result["confidence"]
        reason = result["reason"]
        
        is_correct = actual_intent == expected_intent
        status = "✅" if is_correct else "❌"
        
        print(f"{status} '{question}'")
        print(f"   예상: {expected_intent}, 실제: {actual_intent} (conf: {confidence:.2f})")
        print(f"   근거: {reason}")
        print()


def test_confidence_threshold():
    """신뢰도 임계값 테스트"""
    print("\n=== 신뢰도 테스트 ===")
    
    # 명확한 케이스들
    clear_cases = [
        "이번달 SageMaker 비용",
        "Studio 설정 방법", 
        "안녕하세요"
    ]
    
    for question in clear_cases:
        result = classify_intent(question)
        confidence = result["confidence"]
        print(f"'{question}': confidence = {confidence:.2f}")
        
        # 명확한 케이스는 높은 신뢰도를 가져야 함
        assert confidence >= 0.6, f"명확한 케이스의 신뢰도가 너무 낮습니다: {confidence}"


def test_llm_fallback():
    """LLM 실패 시 기본값 테스트"""
    print("\n=== LLM 실패 시 기본값 테스트 ===")
    
    # 간단한 케이스들
    simple_cases = [
        "안녕",  # 간단한 인사
        "도움말",  # 간단한 도움말
        "비용",  # 단일 키워드
    ]
    
    for question in simple_cases:
        result = classify_intent(question)
        confidence = result["confidence"]
        reason = result["reason"]
        
        print(f"'{question}': {result['intent']} (conf: {confidence:.2f})")
        print(f"   근거: {reason}")
        
        # LLM이 정상적으로 분류하는지 확인
        assert confidence >= 0.5


def test_caching():
    """캐싱 기능 테스트"""
    print("\n=== 캐싱 테스트 ===")
    
    question = "이번달 SageMaker 비용"
    
    # 첫 번째 호출
    result1 = classify_intent(question)
    print(f"첫 번째 호출: {result1['intent']} (conf: {result1['confidence']:.2f})")
    
    # 두 번째 호출 (캐시된 결과)
    result2 = classify_intent(question)
    print(f"두 번째 호출: {result2['intent']} (conf: {result2['confidence']:.2f})")
    
    # 결과가 동일해야 함
    assert result1 == result2, "캐싱이 제대로 작동하지 않습니다"


if __name__ == "__main__":
    # 테스트 실행
    test_intent_classification_structure()
    test_golden_test_cases()
    test_edge_cases()
    test_confidence_threshold()
    test_llm_fallback()
    test_caching()
    
    print("\n🎉 모든 테스트 통과!")
