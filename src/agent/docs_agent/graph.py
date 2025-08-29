"""
Docs Agent: SageMaker/Cloud Radar 공식 문서 기반 RAG Q&A 그래프
"""

import os
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from functools import lru_cache

from .retriever import get_retriever


# 전역 체인 캐시
_ANSWER_CHAIN = None

# 시스템 프롬프트 정의
DOCS_ANSWER_PROMPT = """당신은 AWS SageMaker 전문가입니다. 제공된 문서 컨텍스트를 바탕으로 정확하고 도움이 되는 답변을 생성해주세요.

답변 원칙:
1. **정확성**: 제공된 문서 내용만을 기반으로 답변하세요. 추측이나 일반적인 지식은 사용하지 마세요.
2. **구체성**: 가능한 한 구체적인 정보를 포함하세요 (단계, 설정, 제한사항 등).
3. **구조화**: 복잡한 답변은 단계별로 나누어 설명하세요.
4. **한국어**: 모든 답변은 한국어로 작성하세요.
5. **출처 명시**: 답변의 근거가 되는 문서 섹션을 언급하세요.

주의사항:
- 문서에 없는 내용은 "문서에 해당 정보가 없습니다"라고 답변하세요.
- 불확실한 내용은 "문서에 명확히 나와있지 않습니다"라고 표현하세요.
- 코드나 명령어는 코드 블록으로 표시하세요.
- URL이나 참조 링크가 있다면 포함하세요.

[사용자 질문]
{question}

[관련 문서 컨텍스트]
{context}

위의 문서 내용을 바탕으로 질문에 답변해주세요:"""


def _make_llm():
    """LLM 인스턴스 생성"""
    model = "gpt-4o-mini"
    temperature = 0.1
    timeout = 30.0
    return ChatOpenAI(model=model, temperature=temperature, timeout=timeout)


def _get_answer_chain():
    """답변 생성 체인 반환 (싱글톤 패턴)"""
    global _ANSWER_CHAIN
    
    if _ANSWER_CHAIN is None:
        llm = _make_llm()
        prompt = ChatPromptTemplate.from_template(DOCS_ANSWER_PROMPT)
        _ANSWER_CHAIN = prompt | llm | StrOutputParser()
    
    return _ANSWER_CHAIN


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
    question = state["question"]
    context = state["context"]
    
    try:
        if not context:
            answer = "죄송합니다. 해당 질문에 대한 관련 문서를 찾을 수 없습니다. 다른 키워드로 질문해주시거나, 더 구체적인 질문을 해주세요."
        else:
            # LLM 체인을 사용하여 답변 생성
            answer_chain = _get_answer_chain()
            
            # 컨텍스트가 리스트인 경우 문자열로 변환
            if isinstance(context, list):
                context_text = "\n\n".join([str(ctx) for ctx in context])
            else:
                context_text = str(context)
            
            # LLM 호출하여 답변 생성
            answer = answer_chain.invoke({
                "question": question,
                "context": context_text
            })
            
            # 답변이 너무 길 경우 요약
            if len(answer) > 2000:
                answer = answer[:2000] + "...\n\n(답변이 길어서 일부만 표시됩니다. 더 구체적인 질문을 해주세요.)"
    
    except Exception as e:
        # LLM 호출 실패 시 기본 답변
        answer = f"문서 기반 답변을 생성하는 중 오류가 발생했습니다: {str(e)}. 제공된 컨텍스트를 직접 확인해주세요."
    
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
