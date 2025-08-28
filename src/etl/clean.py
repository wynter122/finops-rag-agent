import pandas as pd
import openai
from typing import Dict, Optional
import json
import time
from ..core.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)

# LLM 정규화를 위한 프롬프트 템플릿
NORMALIZATION_PROMPT = """
다음 AWS SageMaker 사용 타입을 다음 카테고리 중 하나로 분류해주세요:
- Endpoint: 추론/인퍼런스 관련
- Notebook: 개발/실험용 노트북
- Training: 모델 훈련 관련
- Processing: 데이터 처리/전처리
- Other: 기타

사용 타입: {usage_type}
작업: {operation}
제품명: {product_name}

분류 결과만 JSON 형식으로 응답하세요:
{{"category": "분류결과"}}
"""

def normalize_with_llm(df: pd.DataFrame) -> pd.DataFrame:
    """LLM을 사용하여 데이터 정규화"""
    if not Config.USE_LLM_NORMALIZATION:
        logger.info("LLM 정규화가 비활성화되어 있습니다. 규칙 기반 정규화를 사용합니다.")
        return normalize_with_rules(df)
    
    if not Config.OPENAI_API_KEY:
        logger.warning("OpenAI API 키가 설정되지 않았습니다. 규칙 기반 정규화로 폴백합니다.")
        return normalize_with_rules(df)
    
    logger.info("LLM 정규화 시작")
    
    # OpenAI 클라이언트 설정
    openai.api_key = Config.OPENAI_API_KEY
    
    # 정규화할 컬럼들 확인
    required_columns = ['lineitem_usagetype', 'lineitem_operation', 'product_productname']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"필수 컬럼이 누락되었습니다: {missing_columns}. 규칙 기반 정규화로 폴백합니다.")
        return normalize_with_rules(df)
    
    # 결과를 저장할 새로운 컬럼
    df_normalized = df.copy()
    df_normalized['llm_category'] = 'Other'  # 기본값
    
    # 고유한 조합들만 정규화 (성능 최적화)
    unique_combinations = df[required_columns].drop_duplicates()
    logger.info(f"고유한 조합 {len(unique_combinations)}개를 정규화합니다.")
    
    # 정규화 결과 캐시
    normalization_cache = {}
    
    for idx, row in unique_combinations.iterrows():
        usage_type = str(row['lineitem_usagetype']) if pd.notna(row['lineitem_usagetype']) else ''
        operation = str(row['lineitem_operation']) if pd.notna(row['lineitem_operation']) else ''
        product_name = str(row['product_productname']) if pd.notna(row['product_productname']) else ''
        
        # 캐시 키 생성
        cache_key = f"{usage_type}|{operation}|{product_name}"
        
        if cache_key in normalization_cache:
            category = normalization_cache[cache_key]
        else:
            try:
                # LLM 호출
                prompt = NORMALIZATION_PROMPT.format(
                    usage_type=usage_type,
                    operation=operation,
                    product_name=product_name
                )
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "AWS SageMaker 사용 타입을 분류하는 전문가입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=50
                )
                
                # 응답 파싱
                content = response.choices[0].message.content.strip()
                try:
                    result = json.loads(content)
                    category = result.get('category', 'Other')
                except json.JSONDecodeError:
                    logger.warning(f"JSON 파싱 실패: {content}")
                    category = 'Other'
                
                # 캐시에 저장
                normalization_cache[cache_key] = category
                
                # API 호출 제한 방지
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"LLM 정규화 실패: {e}")
                category = 'Other'
                normalization_cache[cache_key] = category
        
        # 해당 조합을 가진 모든 행에 카테고리 적용
        mask = (
            (df['lineitem_usagetype'] == row['lineitem_usagetype']) &
            (df['lineitem_operation'] == row['lineitem_operation']) &
            (df['product_productname'] == row['product_productname'])
        )
        df_normalized.loc[mask, 'llm_category'] = category
    
    logger.info("LLM 정규화 완료")
    return df_normalized

def normalize_with_rules(df: pd.DataFrame) -> pd.DataFrame:
    """규칙 기반 데이터 정규화"""
    logger.info("규칙 기반 정규화 시작")
    
    df_normalized = df.copy()
    df_normalized['rule_category'] = 'Other'  # 기본값
    
    # 규칙 기반 분류
    def classify_usage(row):
        usage_type = str(row.get('lineitem_usagetype', '')).lower()
        operation = str(row.get('lineitem_operation', '')).lower()
        product_name = str(row.get('product_productname', '')).lower()
        
        # Endpoint 관련
        if any(keyword in usage_type or keyword in operation for keyword in ['endpoint', 'inference']):
            return 'Endpoint'
        
        # Notebook 관련
        if any(keyword in usage_type or keyword in operation for keyword in ['notebook', 'jupyter']):
            return 'Notebook'
        
        # Training 관련
        if any(keyword in usage_type or keyword in operation for keyword in ['training', 'train', 'model']):
            return 'Training'
        
        # Processing 관련
        if any(keyword in usage_type or keyword in operation for keyword in ['processing', 'transform', 'batch']):
            return 'Processing'
        
        return 'Other'
    
    # 규칙 적용
    df_normalized['rule_category'] = df_normalized.apply(classify_usage, axis=1)
    
    logger.info("규칙 기반 정규화 완료")
    return df_normalized

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """데이터 정규화 실행"""
    if Config.USE_LLM_NORMALIZATION and Config.OPENAI_API_KEY:
        return normalize_with_llm(df)
    else:
        return normalize_with_rules(df)
