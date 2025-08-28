"""
SQL Agent: CUR 기반 비용 분석 질의 응답 그래프
기존 ask.py의 SQL 체인 (nl2sql → exec → summary)을 이동
"""

import os
from typing import Dict, Any, List, TypedDict

from langgraph.graph import StateGraph, END

# SQL Agent 내부 모듈들 import
from .schema_provider import resolve_base_dir, get_schema_json, scan_parquet_files
from .nl2sql import generate_sql
from .executor import execute_safe_sql
from .summary import summarize_answer, summarize_error


class SQLAgentState(TypedDict):
    question: str
    month: str
    base_dir: str
    schema_json: str
    source_files: list
    sql: str
    df: Any
    result: dict


def nl2sql_node(state: SQLAgentState) -> SQLAgentState:
    """NL2SQL 노드: 자연어 질문을 SQL로 변환"""
    sql = generate_sql(state["question"], state["schema_json"], state["base_dir"])
    return {**state, "sql": sql}


def exec_node(state: SQLAgentState) -> SQLAgentState:
    """실행 노드: SQL을 실행하여 DataFrame 반환"""
    df = execute_safe_sql(state["sql"])
    return {**state, "df": df}


def summary_node(state: SQLAgentState) -> SQLAgentState:
    """요약 노드: SQL 실행 결과를 요약"""
    result = summarize_answer(
        state["question"], 
        state["sql"], 
        state["df"], 
        state["source_files"]
    )
    return {**state, "result": result}


# SQL Agent StateGraph 정의
graph = StateGraph(SQLAgentState)
graph.add_node("nl2sql", nl2sql_node)
graph.add_node("exec", exec_node)
graph.add_node("summary", summary_node)

graph.set_entry_point("nl2sql")
graph.add_edge("nl2sql", "exec")
graph.add_edge("exec", "summary")
graph.add_edge("summary", END)

SQL_GRAPH = graph.compile()


def ask(question: str, month: str = "latest") -> Dict[str, Any]:
    """
    SQL Agent 진입점: 자연어 질문 → (NL2SQL 체인) → SQL 실행 → (요약 체인) → 결과 반환
    
    Args:
        question: 사용자 질문
        month: 분석할 월 (기본값: "latest")
        
    Returns:
        SQL 분석 결과
    """
    try:
        base_dir = resolve_base_dir(month)
        schema_json = get_schema_json(base_dir)
        source_files = [os.path.basename(f) for f in scan_parquet_files(base_dir)]
        
        state = {
            "question": question,
            "month": month,
            "base_dir": base_dir,
            "schema_json": schema_json,
            "source_files": source_files
        }
        
        final = SQL_GRAPH.invoke(state)
        return final["result"]
        
    except Exception as e:
        return summarize_error(question, e)


def ask_with_debug(question: str, month: str = "latest") -> Dict[str, Any]:
    """디버그 정보를 포함하여 질문 처리"""
    try:
        base_dir = resolve_base_dir(month)
        schema_json = get_schema_json(base_dir)
        source_files = [os.path.basename(f) for f in scan_parquet_files(base_dir)]
        
        state = {
            "question": question,
            "month": month,
            "base_dir": base_dir,
            "schema_json": schema_json,
            "source_files": source_files
        }
        
        final = SQL_GRAPH.invoke(state)
        result = final["result"]
        
        # 디버그 정보 추가
        result.update({
            "debug": {
                "base_dir": base_dir,
                "schema_json": schema_json,
                "source_files": source_files,
                "state": final  # 전체 상태 정보 포함
            }
        })
        return result
        
    except Exception as e:
        error_result = summarize_error(question, e)
        error_result["debug"] = {
            "error_type": type(e).__name__,
            "error_details": str(e)
        }
        return error_result


def get_available_months() -> List[str]:
    """사용 가능한 월 목록 반환"""
    data_root = "data/processed"
    if not os.path.exists(data_root):
        return []
    return sorted([d for d in os.listdir(data_root) if os.path.isdir(os.path.join(data_root, d))])


def get_schema_info(month: str = "latest") -> Dict[str, Any]:
    """스키마 정보 반환"""
    try:
        base_dir = resolve_base_dir(month)
        schema_json = get_schema_json(base_dir)
        source_files = [os.path.basename(f) for f in scan_parquet_files(base_dir)]
        return {
            "month": month,
            "base_dir": base_dir,
            "schema": schema_json,
            "source_files": source_files,
            "file_count": len(source_files)
        }
    except Exception as e:
        return {
            "month": month,
            "error": str(e),
            "schema": None,
            "source_files": [],
            "file_count": 0
        }
