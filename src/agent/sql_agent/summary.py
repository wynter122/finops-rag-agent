import os, json
import pandas as pd
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 전역 요약 체인(singleton)
_SUMMARY_CHAIN = None

SUMMARY_PROMPT = """당신은 친근하고 도움이 되는 AWS SageMaker 비용 분석 어시스턴트입니다.
사용자가 비용 관련 질문을 했을 때, 아래 정보를 바탕으로 자연스럽고 이해하기 쉽게 답변해주세요.

답변 스타일:
- 친근하고 자연스러운 톤으로 대화하듯이 답해주세요
- 정확한 수치를 포함하되, 너무 딱딱하지 않게 표현해주세요
- 금액은 소수점 둘째 자리까지 표기하고 USD 단위를 붙여주세요
- 필요하면 "약", "총", "현재까지" 같은 표현을 사용해서 자연스럽게 만들어주세요
- 불확실한 경우에는 "현재 데이터 기준으로는", "확인된 범위 내에서는" 같은 표현을 사용해주세요
- 쿼리 결과 샘플에서 데이터를 찾을 수 없다면, 현재 해당 정보는 찾을 수 없어요. 라고 답해주세요

[질문]
{question}

[실행한 SQL]
{sql}

[쿼리 결과 샘플(JSON, 최대 5행)]
{sample}
"""

def _make_summary_llm():
    model = "gpt-4o-mini"
    temperature = 0.0
    timeout = 20.0
    return ChatOpenAI(model=model, temperature=temperature, timeout=timeout)

def _get_summary_chain():
    global _SUMMARY_CHAIN
    if _SUMMARY_CHAIN is None:
        prompt = ChatPromptTemplate.from_template(SUMMARY_PROMPT)
        _SUMMARY_CHAIN = prompt | _make_summary_llm() | StrOutputParser()
    return _SUMMARY_CHAIN

def _sample_for_prompt(rows: List[Dict[str, Any]]) -> str:
    return json.dumps(rows, ensure_ascii=False)

def summarize_answer(question: str, sql: str, df: pd.DataFrame, source_files: List[str] = None) -> Dict[str, Any]:
    """SQL 실행 결과를 포맷팅 + LLM 요약."""
    # 샘플 데이터 (최대 5행)
    sample_rows = df.head(5).to_dict(orient="records")

    # 숫자 컬럼 요약
    numeric_summary = {}
    for col in df.select_dtypes(include=['number']).columns:
        numeric_summary[col] = {
            "sum": float(df[col].sum()) if len(df) else 0.0,
            "mean": float(df[col].mean()) if len(df) else 0.0,
            "min": float(df[col].min()) if len(df) else 0.0,
            "max": float(df[col].max()) if len(df) else 0.0,
        }

    # LLM 요약 실행
    try:
        chain = _get_summary_chain()
        answer = chain.invoke({
            "question": question,
            "sql": sql,
            "sample": _sample_for_prompt(sample_rows)
        }).strip()
    except Exception as e:
        answer = f"[요약 생성 실패] {e} — SQL 결과를 반환합니다.\n생성된 SQL:\n{sql}"

    return {
        "answer": answer,
        "sql": sql,
        "sample_rows": sample_rows,
        "row_count": len(df),
        "column_count": len(df.columns),
        "numeric_summary": numeric_summary,
        "source_files": source_files or [],
        "intent": "sql",
        "error": False
    }

def summarize_error(question: str, error: Exception) -> Dict[str, Any]:
    """에러 응답 포맷."""
    return {
        "answer": f"질문 '{question}' 처리 중 오류가 발생했습니다: {str(error)}",
        "error": True,
        "error_message": str(error),
        "sql": None,
        "sample_rows": [],
        "row_count": 0,
        "column_count": 0,
        "numeric_summary": {},
        "source_files": [],
        "intent": "sql"
    }
