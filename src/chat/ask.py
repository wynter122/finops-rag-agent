import os
from typing import Dict, Any, List

from .schema_provider import resolve_base_dir, get_schema_json, scan_parquet_files
from .nl2sql import generate_sql
from .executor import execute_safe_sql
from .formatter import format_answer, format_error_response


def ask(question: str, month: str = "latest") -> Dict[str, Any]:
    """자연어 질문 → (NL2SQL 체인) → SQL 실행 → (요약 체인) → 결과 반환"""
    try:
        # 1) 데이터 폴더
        base_dir = resolve_base_dir(month)

        # 2) 스키마 수집
        schema_json = get_schema_json(base_dir)
        source_files = [os.path.basename(f) for f in scan_parquet_files(base_dir)]

        # 3) NL2SQL 체인: 실행 가능한 SQL 생성 (경로 보정 포함)
        sql = generate_sql(question, schema_json, base_dir)

        # 4) SQL 실행
        df = execute_safe_sql(sql)

        # 5) 요약/포맷
        return format_answer(question, sql, df, source_files)

    except Exception as e:
        return format_error_response(question, e)


def ask_with_debug(question: str, month: str = "latest") -> Dict[str, Any]:
    """디버그 정보를 포함하여 질문 처리"""
    try:
        base_dir = resolve_base_dir(month)
        schema_json = get_schema_json(base_dir)
        source_files = [os.path.basename(f) for f in scan_parquet_files(base_dir)]

        sql = generate_sql(question, schema_json, base_dir)
        df = execute_safe_sql(sql)
        result = format_answer(question, sql, df, source_files)

        result.update({
            "debug": {
                "base_dir": base_dir,
                "schema_json": schema_json,
                "source_files": source_files
            }
        })
        return result

    except Exception as e:
        error_result = format_error_response(question, e)
        error_result["debug"] = {
            "error_type": type(e).__name__,
            "error_details": str(e)
        }
        return error_result


def get_available_months() -> List[str]:
    data_root = "data/processed"
    if not os.path.exists(data_root):
        return []
    return sorted([d for d in os.listdir(data_root) if os.path.isdir(os.path.join(data_root, d))])


def get_schema_info(month: str = "latest") -> Dict[str, Any]:
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
