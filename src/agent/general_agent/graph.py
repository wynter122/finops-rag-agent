"""
General Agent: 일반적인 대화/안내 응답 그래프
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END


class GeneralAgentState(TypedDict):
    question: str
    response: str
    result: dict


def process_node(state: GeneralAgentState) -> GeneralAgentState:
    """처리 노드: 일반적인 대화/안내 응답 생성"""
    question = state["question"]
    
    # TODO: LLM을 사용한 일반 대화 응답 생성 로직 구현
    # 간단한 규칙 기반 응답 (임시)
    if "안녕" in question or "hello" in question.lower():
        response = "안녕하세요! AWS SageMaker 비용 분석 챗봇입니다. 무엇을 도와드릴까요?"
    elif "도움" in question or "help" in question.lower():
        response = """다음과 같은 질문을 도와드릴 수 있습니다:

1. **비용 분석**: "8월 SageMaker 비용이 얼마인가요?"
2. **문서 질의**: "SageMaker 설정 방법을 알려주세요"
3. **일반 대화**: "안녕하세요"

어떤 도움이 필요하신가요?"""
    elif "감사" in question or "thank" in question.lower():
        response = "천만에요! 추가로 궁금한 점이 있으시면 언제든 말씀해 주세요."
    else:
        response = "죄송합니다. 질문을 이해하지 못했습니다. 비용 분석이나 문서 질의에 대해 물어보시거나, '도움'이라고 말씀해 주세요."
    
    return {**state, "response": response}


def format_node(state: GeneralAgentState) -> GeneralAgentState:
    """포맷 노드: 최종 결과 포맷팅"""
    result = {
        "answer": state["response"],
        "intent": "general",
        "error": False
    }
    return {**state, "result": result}


# General Agent StateGraph 정의
graph = StateGraph(GeneralAgentState)
graph.add_node("process", process_node)
graph.add_node("format", format_node)

graph.set_entry_point("process")
graph.add_edge("process", "format")
graph.add_edge("format", END)

GENERAL_GRAPH = graph.compile()


def ask(question: str) -> Dict[str, Any]:
    """
    General Agent 진입점: 일반적인 대화/안내 응답
    
    Args:
        question: 사용자 질문
        
    Returns:
        일반 대화 응답 결과
    """
    try:
        state = {"question": question}
        final = GENERAL_GRAPH.invoke(state)
        return final["result"]
        
    except Exception as e:
        return {
            "error": True,
            "message": f"General Agent 처리 중 오류 발생: {str(e)}",
            "intent": "general",
            "answer": "죄송합니다. 응답 생성 중 오류가 발생했습니다."
        }
