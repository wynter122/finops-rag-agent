import os
import glob
import duckdb
import json
from typing import Dict, List
from pathlib import Path


def get_project_root():
    """프로젝트 루트 디렉토리를 찾습니다."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "data").exists():
            return current
        current = current.parent
    return Path.cwd()

PROJECT_ROOT = get_project_root()
DATA_ROOT = str(PROJECT_ROOT / "data/processed")


def resolve_base_dir(month: str = "latest") -> str:
    """기본 디렉토리를 결정합니다.
    
    Args:
        month: 월 폴더명 또는 "latest"
        
    Returns:
        절대 경로
        
    Raises:
        FileNotFoundError: 폴더가 존재하지 않는 경우
    """
    base = os.path.join(DATA_ROOT, month)
    if not os.path.exists(base):
        raise FileNotFoundError(f"{base} 폴더가 없음")
    return base


def scan_parquet_files(base_dir: str) -> List[str]:
    """지정된 디렉토리에서 parquet 파일들을 찾습니다.
    
    Args:
        base_dir: 스캔할 디렉토리 경로
        
    Returns:
        parquet 파일 경로 리스트
    """
    return glob.glob(os.path.join(base_dir, "*.parquet"))


def extract_schema(file_path: str) -> Dict[str, List[str]]:
    """parquet 파일의 스키마를 추출합니다.
    
    Args:
        file_path: parquet 파일 경로
        
    Returns:
        {파일명: [컬럼명들]} 형태의 딕셔너리
    """
    sql = f"DESCRIBE SELECT * FROM read_parquet('{file_path}') LIMIT 0"
    df = duckdb.sql(sql).df()
    return {os.path.basename(file_path): df["column_name"].tolist()}


def get_schema_json(base_dir: str) -> str:
    """디렉토리의 모든 parquet 파일 스키마를 JSON으로 반환합니다.
    
    Args:
        base_dir: 스캔할 디렉토리 경로
        
    Returns:
        스키마 정보가 담긴 JSON 문자열
    """
    schema = {}
    for f in scan_parquet_files(base_dir):
        schema.update(extract_schema(f))
    return json.dumps(schema, ensure_ascii=False, indent=2)
