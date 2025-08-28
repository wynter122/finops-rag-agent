import pandas as pd
from typing import List, Optional
import redshift_connector
from tqdm import tqdm

from ..core.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)

# 기본 SQL 쿼리 템플릿 (필요한 컬럼만 선택)
BASE_SQL = """
SELECT 
    -- 청구 관련
    bill_billingperiodstartdate,
    bill_billingperiodenddate,
    billing_ym,
    
    -- 계정 및 리소스 정보
    lineitem_usageaccountid,
    lineitem_resourceid,
    
    -- 사용량 및 비용
    lineitem_usageamount,
    lineitem_unblendedcost,
    lineitem_blendedcost,
    lineitem_currencycode,
    
    -- 서비스 정보
    lineitem_productcode,
    lineitem_usagetype,
    lineitem_operation,
    lineitem_lineitemtype,
    
    -- 제품 정보
    product_productname,
    product_instancetype,
    product_instancetypefamily,
    product_region,
    
    -- 가격 정보
    pricing_unit,
    pricing_term,
    
    -- 태그 정보 (최대 10개)
    usertag0, usertag1, usertag2, usertag3, usertag4,
    usertag5, usertag6, usertag7, usertag8, usertag9
FROM {table}
WHERE billing_ym in ({billing_ym_list})
  AND lineitem_usageaccountid IN ({account_id_list})
  AND lineitem_lineitemtype IN ('Usage')
  AND POSITION('SageMaker' IN product_productname) > 0
{limit_clause};
"""

def build_sql(table: str, billing_ym: str, account_ids: List[str], limit: Optional[int] = None) -> str:
    """SQL 쿼리 빌드"""
    # billing_ym 정규화 (YYYY-MM -> YYYYMM)
    ym_val = billing_ym.replace('-', '')
    ym_list = f"('{ym_val}')"
    
    # 계정 ID 리스트 생성
    acc_list = ','.join([f"'{a.strip()}'" for a in account_ids if a.strip()])
    
    # LIMIT 절 추가
    limit_clause = f"LIMIT {int(limit)}" if limit else ""
    
    return BASE_SQL.format(
        table=table,
        billing_ym_list=ym_list,
        account_id_list=acc_list,
        limit_clause=limit_clause
    )

def extract_cur_from_redshift(billing_ym: str, account_ids: List[str], limit: Optional[int] = None) -> pd.DataFrame:
    """Redshift에서 CUR 데이터 추출"""
    if not Config.validate_redshift_config():
        raise ValueError("Redshift 연결 설정이 불완전합니다. .env 파일을 확인하세요.")
    
    logger.info(f"Redshift에서 CUR 데이터 추출 시작: billing_ym={billing_ym}, accounts={len(account_ids)}개")
    
    # SQL 쿼리 빌드
    sql = build_sql(Config.CUR_TABLE, billing_ym, account_ids, limit)
    logger.debug(f"실행 SQL: {sql}")
    
    try:
        # Redshift 연결
        conn = redshift_connector.connect(
            host=Config.REDSHIFT_HOST,
            port=Config.REDSHIFT_PORT,
            database=Config.REDSHIFT_DB,
            user=Config.REDSHIFT_USER,
            password=Config.REDSHIFT_PASSWORD,
            ssl=Config.REDSHIFT_SSL
        )
        
        logger.info("Redshift 연결 성공")
        
        # 데이터 추출
        df = pd.read_sql(sql, conn)
        
        logger.info(f"데이터 추출 완료: {len(df)}행")
        
        # 연결 종료
        conn.close()
        
        return df
        
    except Exception as e:
        logger.error(f"Redshift 데이터 추출 실패: {e}")
        raise

def load_raw_from_csv(csv_path: str) -> pd.DataFrame:
    """CSV 파일에서 원시 데이터 로드"""
    logger.info(f"CSV 파일에서 데이터 로드: {csv_path}")
    
    try:
        # 계정 ID를 문자열로 처리하기 위한 dtype 설정
        dtype_dict = {
            'lineitem_usageaccountid': str,
            'billing_ym': str
        }
        
        df = pd.read_csv(csv_path, dtype=dtype_dict)
        
        # 계정 ID가 숫자로 로드된 경우 문자열로 변환
        if 'lineitem_usageaccountid' in df.columns:
            df['lineitem_usageaccountid'] = df['lineitem_usageaccountid'].astype(str)
        
        logger.info(f"CSV 로드 완료: {len(df)}행, {len(df.columns)}컬럼")
        return df
    except Exception as e:
        logger.error(f"CSV 파일 로드 실패: {e}")
        raise

def save_raw(df: pd.DataFrame, billing_ym: str, output_paths: dict):
    """원시 데이터를 Parquet과 CSV로 저장"""
    logger.info(f"원시 데이터 저장 시작: {len(df)}행")
    
    try:
        # Parquet 저장
        df.to_parquet(output_paths['raw_parquet'], index=False)
        logger.info(f"Parquet 저장 완료: {output_paths['raw_parquet']}")
        
        # CSV 저장 (검증용, 최대 1000행)
        sample_size = min(1000, len(df))
        df_sample = df.head(sample_size)
        df_sample.to_csv(output_paths['raw_csv'], index=False, quoting=1)  # quoting=1: 모든 필드를 따옴표로 감싸기
        logger.info(f"CSV 샘플 저장 완료: {output_paths['raw_csv']} ({sample_size}행)")
        
    except Exception as e:
        logger.error(f"원시 데이터 저장 실패: {e}")
        raise
