"""
Docs Agent: SageMaker/Cloud Radar 공식 문서 기반 RAG Q&A 그래프
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

from .retriever import get_retriever


class DocsAgentState(TypedDict):
    question: str
    context: str
    answer: str
    result: dict


def retrieve_node(state: DocsAgentState) -> DocsAgentState:
    """검색 노드: 질문에 대한 관련 문서 검색"""
    retriever = get_retriever()
    context = retriever.get_relevant_context(state["question"])
    return {**state, "context": context}


def answer_node(state: DocsAgentState) -> DocsAgentState:
    """응답 노드: 컨텍스트를 바탕으로 답변 생성"""
    # TODO: LLM을 사용한 답변 생성 로직 구현
    question = state["question"]
    context = state["context"]
    
    if not context:
        answer = "죄송합니다. 해당 질문에 대한 관련 문서를 찾을 수 없습니다."
    else:
        # TODO: LLM 호출하여 답변 생성
        answer = f"문서 기반 답변: {question}에 대한 답변을 생성합니다."
    
    return {**state, "answer": answer}


def format_node(state: DocsAgentState) -> DocsAgentState:
    """포맷 노드: 최종 결과 포맷팅"""
    result = {
        "answer": state["answer"],
        "context": state["context"],
        "intent": "docs",
        "error": False
    }
    return {**state, "result": result}


# Docs Agent StateGraph 정의
graph = StateGraph(DocsAgentState)
graph.add_node("retrieve", retrieve_node)
graph.add_node("answer", answer_node)
graph.add_node("format", format_node)

graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "answer")
graph.add_edge("answer", "format")
graph.add_edge("format", END)

DOCS_GRAPH = graph.compile()


def ask(question: str) -> Dict[str, Any]:
    """
    Docs Agent 진입점: 문서 기반 질의응답
    
    Args:
        question: 사용자 질문
        
    Returns:
        문서 기반 답변 결과
    """
    try:
        state = {"question": question}
        final = DOCS_GRAPH.invoke(state)
        return final["result"]
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Docs Agent 처리 중 오류 발생: {str(e)}",
            "intent": "docs",
            "answer": "죄송합니다. 문서 검색 중 오류가 발생했습니다."
        }
