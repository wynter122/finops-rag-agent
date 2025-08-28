import pandas as pd
from typing import Dict, Any, List


def format_answer(question: str, sql: str, df: pd.DataFrame, source_files: List[str] = None) -> Dict[str, Any]:
    """SQL 실행 결과를 포맷팅합니다.
    
    Args:
        question: 원본 질문
        sql: 실행된 SQL 쿼리
        df: 실행 결과 DataFrame
        source_files: 사용된 소스 파일 목록
        
    Returns:
        포맷팅된 결과 딕셔너리
    """
    # 샘플 데이터 추출 (최대 5행)
    sample_rows = df.head(5).to_dict(orient="records")
    
    # 숫자 컬럼들의 요약 정보 생성
    numeric_summary = {}
    for col in df.select_dtypes(include=['number']).columns:
        numeric_summary[col] = {
            "sum": float(df[col].sum()),
            "mean": float(df[col].mean()),
            "min": float(df[col].min()),
            "max": float(df[col].max())
        }
    
    # 자연어 요약 생성 (주석처리)
    # answer = _generate_natural_language_summary(question, df, numeric_summary)
    
    # SQL문만 출력하도록 수정
    answer = f"생성된 SQL:\n{sql}"
    
    return {
        "answer": answer,
        "sql": sql,
        "sample_rows": sample_rows,
        "row_count": len(df),
        "column_count": len(df.columns),
        "numeric_summary": numeric_summary,
        "source_files": source_files or []
    }


def _generate_natural_language_summary(question: str, df: pd.DataFrame, numeric_summary: Dict[str, Any]) -> str:
    """자연어 요약을 생성합니다.
    
    Args:
        question: 원본 질문
        df: 결과 DataFrame
        numeric_summary: 숫자 컬럼 요약 정보
        
    Returns:
        자연어 요약 문자열
    """
    if len(df) == 0:
        return f"질문 '{question}'에 대한 결과가 없습니다."
    
    # 비용 관련 질문인지 확인
    cost_columns = [col for col in df.columns if 'cost' in col.lower()]
    if cost_columns and any('cost' in col.lower() for col in cost_columns):
        total_cost = sum(numeric_summary[col]['sum'] for col in cost_columns if col in numeric_summary)
        return f"질문 '{question}'에 대한 분석 결과입니다. 총 비용은 ${total_cost:,.2f}입니다."
    
    # 시간 관련 질문인지 확인
    time_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    if time_columns:
        return f"질문 '{question}'에 대한 시간별 분석 결과입니다. 총 {len(df)}개의 레코드가 있습니다."
    
    # 기본 응답
    return f"질문 '{question}'에 대한 SQL 실행 결과입니다. 총 {len(df)}개의 레코드가 있습니다."


def format_error_response(question: str, error: Exception) -> Dict[str, Any]:
    """에러 응답을 포맷팅합니다.
    
    Args:
        question: 원본 질문
        error: 발생한 에러
        
    Returns:
        에러 응답 딕셔너리
    """
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
