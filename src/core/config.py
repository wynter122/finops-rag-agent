import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    # Redshift 설정
    REDSHIFT_HOST = os.getenv('REDSHIFT_HOST', '')
    REDSHIFT_PORT = int(os.getenv('REDSHIFT_PORT', '5439'))
    REDSHIFT_DB = os.getenv('REDSHIFT_DB', '')
    REDSHIFT_USER = os.getenv('REDSHIFT_USER', '')
    REDSHIFT_PASSWORD = os.getenv('REDSHIFT_PASSWORD', '')
    REDSHIFT_IAM_ROLE = os.getenv('REDSHIFT_IAM_ROLE', '')
    REDSHIFT_SSL = os.getenv('REDSHIFT_SSL', 'true').lower() == 'true'
    
    # CUR 테이블 설정
    CUR_TABLE = os.getenv('CUR_TABLE', 'aws_cost_usage')
    
    # 출력 디렉토리
    OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', 'data'))
    
    # LLM 정규화 설정
    USE_LLM_NORMALIZATION = os.getenv('USE_LLM_NORMALIZATION', 'false').lower() == 'true'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    @classmethod
    def validate_redshift_config(cls) -> bool:
        """Redshift 연결 설정이 완전한지 검증"""
        required_fields = [
            cls.REDSHIFT_HOST,
            cls.REDSHIFT_DB,
            cls.REDSHIFT_USER,
            cls.REDSHIFT_PASSWORD
        ]
        return all(field for field in required_fields)
    
    @classmethod
    def validate_llm_config(cls) -> bool:
        """LLM 정규화 설정이 완전한지 검증"""
        if not cls.USE_LLM_NORMALIZATION:
            return True
        return bool(cls.OPENAI_API_KEY)

def parse_billing_ym(billing_ym: str) -> str:
    """billing_ym을 YYYYMM 형식으로 정규화"""
    # YYYY-MM 형식을 YYYYMM으로 변환
    if '-' in billing_ym:
        return billing_ym.replace('-', '')
    return billing_ym

def parse_account_ids(account_ids_str: str) -> List[str]:
    """쉼표로 구분된 계정 ID 문자열을 리스트로 변환"""
    return [acc.strip() for acc in account_ids_str.split(',') if acc.strip()]

def get_output_paths(billing_ym: str) -> dict:
    """출력 경로들을 반환"""
    processed_dir = Config.OUTPUT_DIR / 'processed' / billing_ym
    raw_dir = Config.OUTPUT_DIR / 'raw'
    
    return {
        'raw_parquet': raw_dir / f'sagemaker_cur_{billing_ym}.parquet',
        'raw_csv': raw_dir / f'sagemaker_cur_{billing_ym}.csv',
        'processed_dir': processed_dir,
        'manifest': processed_dir / 'manifest.json'
    }
