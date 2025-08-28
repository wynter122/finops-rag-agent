"""
Router Agent: 사용자 질문을 의도에 따라 적절한 Agent로 라우팅하는 메인 그래프
"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

from .intent_router import classify_intent, IntentType


class RouterState(TypedDict):
    question: str
    intent: IntentType
    sql_result: Dict[str, Any]
    docs_result: Dict[str, Any]
    general_result: Dict[str, Any]
    final_result: Dict[str, Any]


def prepare_node(state: RouterState) -> RouterState:
    """준비 노드: 질문의 의도를 분류"""
    intent = classify_intent(state["question"])
    return {**state, "intent": intent}


def route_node(state: RouterState) -> RouterState:
    """라우팅 노드: 의도에 따라 다음 노드 결정 (조건부 엣지용)"""
    return state


def dispatch_sql_node(state: RouterState) -> RouterState:
    """SQL Agent로 디스패치"""
    from ..sql_agent import ask as sql_ask
    
    try:
        result = sql_ask(state["question"])
        return {**state, "sql_result": result, "final_result": result}
    except Exception as e:
        error_result = {
            "error": True,
            "message": f"SQL Agent 처리 중 오류 발생: {str(e)}",
            "intent": "sql"
        }
        return {**state, "sql_result": error_result, "final_result": error_result}


def dispatch_docs_node(state: RouterState) -> RouterState:
    """Docs Agent로 디스패치"""
    # TODO: Docs Agent 호출 구현
    from ..docs_agent.graph import ask as docs_ask
    
    try:
        result = docs_ask(state["question"])
        return {**state, "docs_result": result, "final_result": result}
    except Exception as e:
        error_result = {
            "error": True,
            "message": f"Docs Agent 처리 중 오류 발생: {str(e)}",
            "intent": "docs"
        }
        return {**state, "docs_result": error_result, "final_result": error_result}


def dispatch_general_node(state: RouterState) -> RouterState:
    """General Agent로 디스패치"""
    # TODO: General Agent 호출 구현
    from ..general_agent.graph import ask as general_ask
    
    try:
        result = general_ask(state["question"])
        return {**state, "general_result": result, "final_result": result}
    except Exception as e:
        error_result = {
            "error": True,
            "message": f"General Agent 처리 중 오류 발생: {str(e)}",
            "intent": "general"
        }
        return {**state, "general_result": error_result, "final_result": error_result}


def route_condition(state: RouterState) -> str:
    """라우팅 조건: 의도에 따라 다음 노드 결정"""
    return state["intent"]


# Router StateGraph 정의
graph = StateGraph(RouterState)

# 노드 추가
graph.add_node("prepare", prepare_node)
graph.add_node("route", route_node)
graph.add_node("dispatch_sql", dispatch_sql_node)
graph.add_node("dispatch_docs", dispatch_docs_node)
graph.add_node("dispatch_general", dispatch_general_node)

# 엣지 설정
graph.set_entry_point("prepare")
graph.add_edge("prepare", "route")
graph.add_conditional_edges(
    "route",
    route_condition,
    {
        "sql": "dispatch_sql",
        "docs": "dispatch_docs", 
        "general": "dispatch_general"
    }
)
graph.add_edge("dispatch_sql", END)
graph.add_edge("dispatch_docs", END)
graph.add_edge("dispatch_general", END)

ROUTER_GRAPH = graph.compile()


def ask(question: str) -> Dict[str, Any]:
    """
    메인 진입점: 사용자 질문을 받아 적절한 Agent로 라우팅
    
    Args:
        question: 사용자 질문
        
    Returns:
        선택된 Agent의 응답 결과
    """
    try:
        state = {"question": question}
        final = ROUTER_GRAPH.invoke(state)
        return final["final_result"]
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Router Agent 처리 중 오류 발생: {str(e)}",
            "intent": "unknown"
        }
