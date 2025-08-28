"""
SageMaker 비용 분석 챗봇 패키지

이 패키지는 ETL 산출물을 기반으로 자연어 질문을 SQL로 변환하고
DuckDB로 실행하여 결과를 반환하는 기능을 제공합니다.
"""

from .ask import ask, ask_with_debug, get_available_months, get_schema_info
from .schema_provider import resolve_base_dir, get_schema_json
from .nl2sql import generate_sql
from .executor import execute_safe_sql, validate_sql
from .formatter import format_answer, format_error_response

__all__ = [
    # 메인 함수들
    "ask",
    "ask_with_debug",
    "get_available_months", 
    "get_schema_info",
    
    # 스키마 관련
    "resolve_base_dir",
    "get_schema_json",
    
    # SQL 생성 관련
    "generate_sql",
    
    # SQL 실행 관련
    "execute_safe_sql",
    "validate_sql",
    
    # 포맷팅 관련
    "format_answer",
    "format_error_response",
]

__version__ = "0.1.0"
