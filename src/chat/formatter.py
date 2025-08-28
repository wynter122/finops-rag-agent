import os, json
import pandas as pd
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 전역 요약 체인(singleton)
_SUMMARY_CHAIN = None

SUMMARY_PROMPT = """너는 AWS SageMaker 비용 분석 어시스턴트다.
아래 정보를 바탕으로 '정확한 수치'만 사용해 짧고 명확한 한국어 문장으로 요약하라.
- 금액은 소수점 둘째 자리까지 표기하고 USD 단위를 붙여라.
- 한 문장으로 간결하게 답해라.
- 불확실하면 '제공된 결과에서 확인된 값만 기준으로 요약'이라고 명시하라.

[질문]
{question}

[실행한 SQL]
{sql}

[쿼리 결과 샘플(JSON, 최대 5행)]
{sample}
"""

def _make_summary_llm():
    model = os.getenv("LLM_SUMMARY_MODEL", "gpt-4o-mini")
    try:
        temperature = float(os.getenv("LLM_SUMMARY_TEMPERATURE", "0.0"))
    except ValueError:
        temperature = 0.0
    try:
        timeout = float(os.getenv("LLM_SUMMARY_TIMEOUT", "20"))
    except ValueError:
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

def format_answer(question: str, sql: str, df: pd.DataFrame, source_files: List[str] = None) -> Dict[str, Any]:
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
        "source_files": source_files or []
    }

def format_error_response(question: str, error: Exception) -> Dict[str, Any]:
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
        "source_files": []
    }
