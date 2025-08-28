# 의도 분류 테스트
python -m src.test.test_chat --test-intents

# 단일 질문 테스트
python -m src.test.test_chat --question "8월 SageMaker 비용이 얼마인가요?" --debug

# 모든 테스트 실행
python -m src.test.test_chat --test-all

# LLM 디버그
python -m src.test.debug_llm