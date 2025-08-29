"""
Docs Agent: SageMaker/Cloud Radar 공식 문서 기반 RAG Q&A 그래프
"""

import os
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_tavily import TavilySearch
from functools import lru_cache
import json

from .retriever import get_retriever


# 전역 체인 캐시
_ANSWER_CHAIN = None
_QUALITY_CHAIN = None
_WEB_SEARCH_CHAIN = None

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

# 품질 평가 프롬프트
QUALITY_EVALUATION_PROMPT = """당신은 답변 품질 평가 전문가입니다. 주어진 질문과 답변을 분석하여 품질을 평가해주세요.

평가 기준:
1. **완성도**: 질문에 대한 답변이 완전한가? (0-10점)
2. **정확성**: 답변이 정확하고 신뢰할 수 있는가? (0-10점)
3. **구체성**: 답변이 구체적이고 실용적인가? (0-10점)
4. **명확성**: 답변이 이해하기 쉽고 명확한가? (0-10점)

평가 결과는 JSON 형식으로 반환하세요:
{{
    "overall_score": 0-10,
    "completeness": 0-10,
    "accuracy": 0-10,
    "specificity": 0-10,
    "clarity": 0-10,
    "needs_web_search": true/false,
    "reason": "평가 근거"
}}

needs_web_search가 true인 경우:
- 전체 점수가 6점 미만이거나
- 특정 점수가 4점 미만이거나
- 답변이 너무 짧거나 불완전한 경우

[질문]
{question}

[답변]
{answer}

[컨텍스트 길이]
{context_length}자

평가 결과:"""

# 웹 검색 기반 답변 생성 프롬프트
WEB_ANSWER_PROMPT = """당신은 AWS SageMaker 전문가입니다. 문서 컨텍스트와 웹 검색 결과를 종합하여 최적의 답변을 생성해주세요.

답변 원칙:
1. **문서 우선**: 문서 컨텍스트를 우선적으로 사용하세요.
2. **웹 보완**: 문서에 부족한 정보는 웹 검색 결과로 보완하세요.
3. **출처 구분**: 문서 내용과 웹 검색 내용을 구분하여 표시하세요.
4. **정확성**: 신뢰할 수 있는 정보만 사용하세요.
5. **한국어**: 모든 답변은 한국어로 작성하세요.

[사용자 질문]
{question}

[문서 컨텍스트]
{docs_context}

[웹 검색 결과]
{web_results}

위의 정보를 종합하여 질문에 답변해주세요:"""


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


def _get_quality_chain():
    """품질 평가 체인 반환 (싱글톤 패턴)"""
    global _QUALITY_CHAIN
    
    if _QUALITY_CHAIN is None:
        llm = _make_llm()
        prompt = ChatPromptTemplate.from_template(QUALITY_EVALUATION_PROMPT)
        _QUALITY_CHAIN = prompt | llm | JsonOutputParser()
    
    return _QUALITY_CHAIN


def _get_web_search_chain():
    """웹 검색 기반 답변 생성 체인 반환 (싱글톤 패턴)"""
    global _WEB_SEARCH_CHAIN
    
    if _WEB_SEARCH_CHAIN is None:
        llm = _make_llm()
        prompt = ChatPromptTemplate.from_template(WEB_ANSWER_PROMPT)
        _WEB_SEARCH_CHAIN = prompt | llm | StrOutputParser()
    
    return _WEB_SEARCH_CHAIN


def _evaluate_answer_quality(question: str, answer: str, context_length: int) -> Dict[str, Any]:
    """답변 품질 평가"""
    try:
        quality_chain = _get_quality_chain()
        result = quality_chain.invoke({
            "question": question,
            "answer": answer,
            "context_length": context_length
        })
        return result
    except Exception as e:
        # 평가 실패 시 기본값 반환
        return {
            "overall_score": 5,
            "completeness": 5,
            "accuracy": 5,
            "specificity": 5,
            "clarity": 5,
            "needs_web_search": True,
            "reason": f"품질 평가 실패: {str(e)}"
        }


def _web_search(question: str) -> str:
    """Tavily 웹 검색 수행"""
    try:
        # Tavily API 키 확인
        if not os.getenv('TAVILY_API_KEY'):
            return "웹 검색을 사용할 수 없습니다. TAVILY_API_KEY 환경 변수가 설정되지 않았습니다."
        
        # Tavily 검색 도구 초기화
        search_tool = TavilySearch(max_results=5, topic="technology")
        search_results = search_tool.invoke(question)
        
        # 검색 결과 포맷팅
        formatted_results = []
        if 'results' in search_results:
            for result in search_results['results']:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'url': result.get('url', '')
                })
        
        return json.dumps(formatted_results, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"웹 검색 실패: {str(e)}"


def _generate_enhanced_answer(question: str, docs_context: str, web_results: str) -> str:
    """웹 검색 결과를 포함한 향상된 답변 생성"""
    try:
        web_chain = _get_web_search_chain()
        answer = web_chain.invoke({
            "question": question,
            "docs_context": docs_context,
            "web_results": web_results
        })
        return answer
    except Exception as e:
        return f"향상된 답변 생성 실패: {str(e)}"


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
    """응답 노드: 컨텍스트를 바탕으로 답변 생성 (품질 평가 및 웹 검색 포함)"""
    question = state["question"]
    context = state["context"]
    
    try:
        if not context:
            answer = "죄송합니다. 해당 질문에 대한 관련 문서를 찾을 수 없습니다. 다른 키워드로 질문해주시거나, 더 구체적인 질문을 해주세요."
        else:
            # 컨텍스트가 리스트인 경우 문자열로 변환
            if isinstance(context, list):
                context_text = "\n\n".join([str(ctx) for ctx in context])
            else:
                context_text = str(context)
            
            # 1단계: 기본 답변 생성
            answer_chain = _get_answer_chain()
            initial_answer = answer_chain.invoke({
                "question": question,
                "context": context_text
            })
            
            # 2단계: 답변 품질 평가
            quality_result = _evaluate_answer_quality(
                question=question,
                answer=initial_answer,
                context_length=len(context_text)
            )
            
            # 3단계: 품질이 낮은 경우 웹 검색 수행
            if quality_result.get("needs_web_search", False):
                print(f"🔍 답변 품질이 낮습니다 (점수: {quality_result.get('overall_score', 0)}/10). 웹 검색을 수행합니다...")
                
                # 웹 검색 수행
                web_results = _web_search(question)
                
                # 웹 검색 결과를 포함한 향상된 답변 생성
                enhanced_answer = _generate_enhanced_answer(
                    question=question,
                    docs_context=context_text,
                    web_results=web_results
                )
                
                # 향상된 답변의 품질 재평가
                enhanced_quality = _evaluate_answer_quality(
                    question=question,
                    answer=enhanced_answer,
                    context_length=len(context_text)
                )
                
                # 향상된 답변이 더 좋은 경우 사용
                if enhanced_quality.get("overall_score", 0) > quality_result.get("overall_score", 0):
                    answer = enhanced_answer
                    print(f"✅ 웹 검색을 통해 답변 품질이 향상되었습니다 (점수: {enhanced_quality.get('overall_score', 0)}/10)")
                else:
                    answer = initial_answer
                    print(f"⚠️ 웹 검색 결과가 기존 답변보다 나지 않아 기본 답변을 유지합니다")
            else:
                answer = initial_answer
                print(f"✅ 답변 품질이 양호합니다 (점수: {quality_result.get('overall_score', 0)}/10)")
            
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
