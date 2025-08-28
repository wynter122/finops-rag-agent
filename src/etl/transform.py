import pandas as pd
import numpy as np
from typing import Dict
from ..utils.logging import get_logger

logger = get_logger(__name__)

def _like(s: pd.Series, keyword: str) -> pd.Series:
    """대소문자 구분 없는 문자열 포함 여부 확인"""
    return s.str.contains(keyword, case=False, na=False)

def transform_all(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """CUR 데이터를 변환하고 집계"""
    logger.info(f"데이터 변환 시작: {len(df)}행")
    
    # 원본 데이터 복사
    fact = df.copy()
    
    # 파생 컬럼 생성
    logger.info("파생 컬럼 생성 중...")
    
    # 서비스 타입 판별 (개선된 로직)
    fact['is_endpoint'] = (
        _like(fact['lineitem_usagetype'], 'Host') |  # Endpoint 호스팅 비용
        _like(fact['lineitem_usagetype'], 'Endpoint')  # 직접 Endpoint
    )
    fact['is_notebook'] = (
        _like(fact['lineitem_usagetype'], 'Notebook') |
        _like(fact['lineitem_usagetype'], 'Notebk')
    )
    fact['is_training'] = (
        _like(fact['lineitem_usagetype'], 'Train') |  # Training 인스턴스
        _like(fact['lineitem_operation'], 'Train')
    )
    fact['is_spot'] = _like(fact['lineitem_usagetype'], 'Spot')
    
    # 추가 파생 컬럼 (규칙 기반 개선)
    fact['is_studio'] = _like(fact['lineitem_usagetype'], 'Studio')
    fact['is_featurestore'] = _like(fact['lineitem_usagetype'], 'FeatureStore')
    fact['is_processing'] = _like(fact['lineitem_usagetype'], 'Processing')
    fact['is_data_transfer'] = (
        _like(fact['lineitem_usagetype'], 'Data-Bytes') |
        _like(fact['lineitem_usagetype'], 'DataTransfer')
    )
    fact['is_storage'] = (
        _like(fact['lineitem_usagetype'], 'VolumeUsage') |
        _like(fact['lineitem_usagetype'], 'Storage')
    )
    
    # usage_hours 계산 (보수적 접근)
    has_hrs = (
        _like(fact['pricing_unit'], 'Hrs') | 
        _like(fact['pricing_unit'], 'Hours') |
        _like(fact['pricing_unit'], 'Hour')
    )
    fact['usage_hours'] = fact['lineitem_usageamount'].where(has_hrs, other=None)
    
    # 비용 컬럼 정규화 (None 값 처리)
    cost_columns = ['lineitem_unblendedcost', 'lineitem_blendedcost']
    for col in cost_columns:
        if col in fact.columns:
            fact[col] = pd.to_numeric(fact[col], errors='coerce').fillna(0)
    
    logger.info("집계 테이블 생성 중...")
    
    # 1. Endpoint 시간/비용 집계
    endpoint_mask = fact['is_endpoint']
    if endpoint_mask.any():
        agg_endpoint_hours = fact.loc[endpoint_mask].groupby(
            ['lineitem_resourceid', 'product_instancetype'], dropna=False
        ).agg({
            'usage_hours': 'sum',
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_endpoint_hours.columns = ['resource_id', 'instance_type', 'hours', 'cost']
    else:
        agg_endpoint_hours = pd.DataFrame(columns=['resource_id', 'instance_type', 'hours', 'cost'])
    
    # 2. Training 비용 집계
    training_mask = fact['is_training']
    if training_mask.any():
        agg_training_cost = fact.loc[training_mask].groupby(
            ['lineitem_usageaccountid', 'product_instancetype'], dropna=False
        ).agg({
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_training_cost.columns = ['account_id', 'instance_type', 'cost']
    else:
        agg_training_cost = pd.DataFrame(columns=['account_id', 'instance_type', 'cost'])
    
    # 3. Notebook 시간/비용 집계
    notebook_mask = fact['is_notebook']
    if notebook_mask.any():
        agg_notebook_hours = fact.loc[notebook_mask].groupby(
            ['product_instancetype'], dropna=False
        ).agg({
            'usage_hours': 'sum',
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_notebook_hours.columns = ['instance_type', 'hours', 'cost']
    else:
        agg_notebook_hours = pd.DataFrame(columns=['instance_type', 'hours', 'cost'])
    
    # 4. Studio 시간/비용 집계
    studio_mask = fact['is_studio']
    if studio_mask.any():
        agg_studio_hours = fact.loc[studio_mask].groupby(
            ['product_instancetype'], dropna=False
        ).agg({
            'usage_hours': 'sum',
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_studio_hours.columns = ['instance_type', 'hours', 'cost']
    else:
        agg_studio_hours = pd.DataFrame(columns=['instance_type', 'hours', 'cost'])
    
    # 5. FeatureStore 비용 집계
    featurestore_mask = fact['is_featurestore']
    if featurestore_mask.any():
        agg_featurestore_cost = fact.loc[featurestore_mask].groupby(
            ['lineitem_usagetype'], dropna=False
        ).agg({
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_featurestore_cost.columns = ['usage_type', 'cost']
    else:
        agg_featurestore_cost = pd.DataFrame(columns=['usage_type', 'cost'])
    
    # 6. Processing 비용 집계
    processing_mask = fact['is_processing']
    if processing_mask.any():
        agg_processing_cost = fact.loc[processing_mask].groupby(
            ['product_instancetype'], dropna=False
        ).agg({
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_processing_cost.columns = ['instance_type', 'cost']
    else:
        agg_processing_cost = pd.DataFrame(columns=['instance_type', 'cost'])
    
    # 7. Data Transfer 비용 집계
    datatransfer_mask = fact['is_data_transfer']
    if datatransfer_mask.any():
        agg_datatransfer_cost = fact.loc[datatransfer_mask].groupby(
            ['lineitem_usagetype'], dropna=False
        ).agg({
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_datatransfer_cost.columns = ['usage_type', 'cost']
    else:
        agg_datatransfer_cost = pd.DataFrame(columns=['usage_type', 'cost'])
    
    # 8. Storage 비용 집계
    storage_mask = fact['is_storage']
    if storage_mask.any():
        agg_storage_cost = fact.loc[storage_mask].groupby(
            ['lineitem_usagetype'], dropna=False
        ).agg({
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_storage_cost.columns = ['usage_type', 'cost']
    else:
        agg_storage_cost = pd.DataFrame(columns=['usage_type', 'cost'])
    
    # 9. Spot/OnDemand 비용 비율
    if len(fact) > 0:
        fact_with_pricing = fact.assign(
            pricing_type=np.where(fact['is_spot'], 'Spot', 'OnDemand')
        )
        agg_spot_ratio = fact_with_pricing.groupby('pricing_type').agg({
            'lineitem_unblendedcost': 'sum'
        }).reset_index()
        agg_spot_ratio.columns = ['pricing_type', 'cost']
    else:
        agg_spot_ratio = pd.DataFrame(columns=['pricing_type', 'cost'])
    
    # 10. 월별 총 비용 요약
    if 'billing_ym' in fact.columns:
        monthly_summary = fact.groupby('billing_ym').agg({
            'lineitem_unblendedcost': 'sum',
            'lineitem_blendedcost': 'sum'
        }).reset_index()
        monthly_summary.columns = ['billing_ym', 'unblended_cost', 'blended_cost']
    else:
        monthly_summary = pd.DataFrame(columns=['billing_ym', 'unblended_cost', 'blended_cost'])
    
    logger.info("변환 완료")
    
    return {
        'fact_sagemaker_costs': fact,
        'agg_endpoint_hours': agg_endpoint_hours,
        'agg_training_cost': agg_training_cost,
        'agg_notebook_hours': agg_notebook_hours,
        'agg_studio_hours': agg_studio_hours,
        'agg_featurestore_cost': agg_featurestore_cost,
        'agg_processing_cost': agg_processing_cost,
        'agg_datatransfer_cost': agg_datatransfer_cost,
        'agg_storage_cost': agg_storage_cost,
        'agg_spot_ratio': agg_spot_ratio,
        'monthly_summary': monthly_summary
    }

def get_transform_stats(dfs: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    """변환 결과 통계 반환"""
    stats = {}
    for name, df in dfs.items():
        stats[name] = len(df)
    return stats
