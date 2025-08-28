import os
from typing import Dict, Any, List
from .schema_provider import resolve_base_dir, get_schema_json, scan_parquet_files
from .nl2sql import generate_sql, parse_sql_response
from .executor import execute_safe_sql
from .formatter import format_answer, format_error_response


def ask(question: str, month: str = "latest") -> Dict[str, Any]:
    """자연어 질문을 받아 SQL을 생성하고 실행하여 결과를 반환합니다.
    
    Args:
        question: 사용자 질문
        month: 분석할 월 폴더명 (기본값: "latest")
        
    Returns:
        분석 결과 딕셔너리
        
    Raises:
        FileNotFoundError: 데이터 폴더가 없는 경우
        ValueError: SQL 생성/파싱 실패
        RuntimeError: SQL 실행 오류
    """
    try:
        # 1. 기본 디렉토리 결정
        base_dir = resolve_base_dir(month)
        
        # 2. 스키마 정보 수집
        schema_json = get_schema_json(base_dir)
        source_files = [os.path.basename(f) for f in scan_parquet_files(base_dir)]
        
        # 3. SQL 생성
        sql_response = generate_sql(question, schema_json)
        sql = parse_sql_response(sql_response)
        
        # 4. SQL 실행
        df = execute_safe_sql(sql)
        
        # 5. 결과 포맷팅
        return format_answer(question, sql, df, source_files)
        
    except Exception as e:
        return format_error_response(question, e)


def ask_with_debug(question: str, month: str = "latest") -> Dict[str, Any]:
    """디버그 정보를 포함하여 질문을 처리합니다.
    
    Args:
        question: 사용자 질문
        month: 분석할 월 폴더명 (기본값: "latest")
        
    Returns:
        디버그 정보가 포함된 분석 결과 딕셔너리
    """
    try:
        # 1. 기본 디렉토리 결정
        base_dir = resolve_base_dir(month)
        
        # 2. 스키마 정보 수집
        schema_json = get_schema_json(base_dir)
        source_files = [os.path.basename(f) for f in scan_parquet_files(base_dir)]
        
        # 3. SQL 생성
        sql_response = generate_sql(question, schema_json)
        sql = parse_sql_response(sql_response)
        
        # 4. SQL 실행
        df = execute_safe_sql(sql)
        
        # 5. 결과 포맷팅
        result = format_answer(question, sql, df, source_files)
        
        # 6. 디버그 정보 추가
        result.update({
            "debug": {
                "base_dir": base_dir,
                "schema_json": schema_json,
                "sql_response": sql_response,
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
    """사용 가능한 월 폴더 목록을 반환합니다.
    
    Returns:
        월 폴더명 리스트
    """
    data_root = "data/processed"
    if not os.path.exists(data_root):
        return []
    
    months = []
    for item in os.listdir(data_root):
        item_path = os.path.join(data_root, item)
        if os.path.isdir(item_path):
            months.append(item)
    
    return sorted(months)


def get_schema_info(month: str = "latest") -> Dict[str, Any]:
    """지정된 월의 스키마 정보를 반환합니다.
    
    Args:
        month: 월 폴더명 (기본값: "latest")
        
    Returns:
        스키마 정보 딕셔너리
    """
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
