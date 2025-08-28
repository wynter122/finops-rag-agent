import os
import duckdb
import pandas as pd
from typing import Optional


def run_sql(sql: str) -> pd.DataFrame:
    """DuckDB로 SQL을 실행합니다.
    
    Args:
        sql: 실행할 SQL 쿼리
        
    Returns:
        실행 결과 DataFrame
        
    Raises:
        RuntimeError: SQL 실행 중 오류가 발생한 경우
    """
    try:
        # DuckDB 연결 생성
        con = duckdb.connect()
        
        # SQL 실행
        df = con.execute(sql).df()
        con.close()
        
        return df
    except Exception as e:
        raise RuntimeError(f"SQL 실행 오류: {e}")


def validate_sql(sql: str) -> bool:
    """SQL의 안전성을 검증합니다.
    
    Args:
        sql: 검증할 SQL 쿼리
        
    Returns:
        안전한 경우 True, 그렇지 않으면 False
    """
    sql_upper = sql.upper().strip()
    
    # 위험한 명령어 차단
    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
        'TRUNCATE', 'GRANT', 'REVOKE', 'EXECUTE', 'CALL'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    
    # SELECT로 시작하는지 확인
    if not sql_upper.startswith('SELECT'):
        return False
    
    return True


def execute_safe_sql(sql: str) -> pd.DataFrame:
    """안전한 SQL만 실행합니다.
    
    Args:
        sql: 실행할 SQL 쿼리
        
    Returns:
        실행 결과 DataFrame
        
    Raises:
        ValueError: 안전하지 않은 SQL인 경우
        RuntimeError: SQL 실행 중 오류가 발생한 경우
    """
    if not validate_sql(sql):
        raise ValueError(f"안전하지 않은 SQL: {sql}")
    
    return run_sql(sql)
