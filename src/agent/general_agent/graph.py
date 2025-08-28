"""
General Agent: 일반적인 대화/안내 응답 그래프
"""

import os
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class GeneralAgentState(TypedDict):
    question: str
    response: str
    result: dict


# 전역 체인 캐시
_GENERAL_CHAIN = None

SYSTEM_PROMPT = """당신은 FinOps RAG Agent의 General Assistant다.
역할: 일반 대화, 도움말, 사용 가이드(고수준), 라우팅 안내를 간결한 한국어로 제공한다.

원칙:
- 사실 기반, 불필요한 추측 금지. 모르면 모른다고 말한다.
- 비용 분석(정량 수치 질의)은 'SQL Agent'로 라우팅하라고 안내한다.
- SageMaker/Cloud Radar 상세 문서 답변은 'Docs Agent'가 담당한다고 안내한다.
- 답변은 3문장 이내, 목록이 필요하면 최대 5항목.
- 코드/명령은 코드블록으로. 링크는 텍스트로만.

도움말 예시:
- "무엇을 할 수 있어?" → 지원 영역을 항목으로 안내
- "도움" → 대표 예시 질의 3~5개 제시
- "이 시스템은 어떻게 써?" → 간단 워크플로 설명 후 라우팅 키워드 예시

금지:
- 임의 수치 제시 금지(비용/시간/합계 등). 그런 질문은 SQL Agent 권유.
- 문서의 정확한 인용/버전이 필요한 세부 절차는 Docs Agent 권유.
"""


def _make_llm():
    model = os.getenv("GENERAL_AGENT_MODEL", "gpt-4o-mini")
    try:
        temperature = float(os.getenv("GENERAL_AGENT_TEMPERATURE", "0.2"))
    except ValueError:
        temperature = 0.2
    try:
        timeout = float(os.getenv("GENERAL_AGENT_TIMEOUT", "20"))
    except ValueError:
        timeout = 20.0
    return ChatOpenAI(model=model, temperature=temperature, timeout=timeout)


def _get_general_chain():
    global _GENERAL_CHAIN
    if _GENERAL_CHAIN is None:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        _GENERAL_CHAIN = prompt | _make_llm() | StrOutputParser()
    return _GENERAL_CHAIN


def process_node(state: GeneralAgentState) -> GeneralAgentState:
    """처리 노드: LLM으로 일반 대화/안내 응답 생성"""
    chain = _get_general_chain()
    question = state["question"].strip()

    # 1) LLM 호출
    try:
        response = chain.invoke({"question": question}).strip()
    except Exception as e:
        # 실패 시 안전 폴백
        response = (
            "죄송합니다. 일반 대화 응답을 생성하는 중 오류가 발생했습니다. "
            "다시 시도해 주세요. 비용 수치가 궁금하시면 SQL Agent, "
            "설정/사용 가이드는 Docs Agent로 문의해 주세요."
        )

    # 2) 후처리(너무 길면 자르기)
    if len(response) > 1000:
        response = response[:1000] + " …"

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
