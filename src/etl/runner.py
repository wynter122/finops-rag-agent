#!/usr/bin/env python3
"""
FinOps RAG Agent ETL Pipeline
Redshift CUR 추출 → 변환 → LLM 정규화(옵션) → 저장
"""

import argparse
import sys
from pathlib import Path

from ..core.config import Config, parse_billing_ym, parse_account_ids, get_output_paths
from ..utils.logging import setup_logger, get_logger
from ..utils.lock import etl_lock
from .extract import extract_cur_from_redshift, load_raw_from_csv, save_raw
from .transform import transform_all, get_transform_stats
from .clean import clean_data
from .store import write_processed, write_manifest, make_latest_symlink, get_processed_summary
from ..core.contracts import ContractManager

def main():
    """메인 ETL 실행 함수"""
    parser = argparse.ArgumentParser(description='FinOps RAG Agent ETL Pipeline')
    parser.add_argument('--billing-ym', required=False, 
                       help='청구 연월 (YYYYMM 또는 YYYY-MM 형식)')
    parser.add_argument('--contract', type=str, default=None,
                       help='계약 ID (contracts.json에서 정의)')
    parser.add_argument('--accounts', type=str, default=None,
                       help='AWS 계정 ID 목록 (쉼표로 구분, --contract와 상호 배타적)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Redshift 쿼리 제한 (디버그용)')
    parser.add_argument('--input-csv', type=str, default=None,
                       help='입력 CSV 파일 경로 (Redshift 대신 사용)')
    parser.add_argument('--list-contracts', action='store_true',
                       help='사용 가능한 계약 목록 출력')
    
    args = parser.parse_args()
    
    # 로거 설정
    logger = setup_logger()
    logger.info("FinOps RAG Agent ETL Pipeline 시작")
    
    # 계약 관리자 초기화
    contract_manager = ContractManager()
    
    # 계약 목록 출력
    if args.list_contracts:
        contracts = contract_manager.list_contracts()
        if contracts:
            logger.info("사용 가능한 계약 목록:")
            for contract_id, contract in contracts.items():
                summary = contract_manager.get_contract_summary(contract_id)
                logger.info(f"  {contract_id}: {summary['name']} ({summary['account_count']}개 계정)")
        else:
            logger.info("정의된 계약이 없습니다.")
        return
    
    # billing_ym이 필수 (계약 목록 출력이 아닌 경우)
    if not args.billing_ym:
        logger.error("--billing-ym이 필요합니다.")
        sys.exit(1)
    
    try:
        # 파라미터 파싱
        billing_ym = parse_billing_ym(args.billing_ym)
        input_csv = args.input_csv
        limit = args.limit
        
        # 계정 ID 결정 (계약 또는 직접 입력)
        if args.contract:
            if args.accounts:
                logger.error("--contract와 --accounts는 동시에 사용할 수 없습니다.")
                sys.exit(1)
            
            if not contract_manager.validate_contract(args.contract):
                sys.exit(1)
            
            account_ids = contract_manager.get_contract_accounts(args.contract)
            contract_summary = contract_manager.get_contract_summary(args.contract)
            logger.info(f"계약 사용: {contract_summary['name']} ({len(account_ids)}개 계정)")
        elif args.accounts:
            account_ids = parse_account_ids(args.accounts)
        else:
            # 기본 계약 사용
            default_contract = contract_manager.get_default_contract()
            if default_contract and contract_manager.validate_contract(default_contract):
                account_ids = contract_manager.get_contract_accounts(default_contract)
                contract_summary = contract_manager.get_contract_summary(default_contract)
                logger.info(f"기본 계약 사용: {contract_summary['name']} ({len(account_ids)}개 계정)")
            else:
                logger.error("계정 ID를 지정하거나 유효한 기본 계약을 설정하세요.")
                sys.exit(1)
        
        logger.info(f"파라미터: billing_ym={billing_ym}, accounts={len(account_ids)}개, limit={limit}")
        
        # 출력 경로 설정
        output_paths = get_output_paths(billing_ym)
        
        # ETL 락으로 중복 실행 방지
        with etl_lock(timeout=300):
            # 1. 원시 데이터 적재
            if input_csv:
                logger.info(f"CSV 파일에서 데이터 로드: {input_csv}")
                df_raw = load_raw_from_csv(input_csv)
            else:
                logger.info("Redshift에서 데이터 추출")
                df_raw = extract_cur_from_redshift(billing_ym, account_ids, limit)
            
            # 2. 원시 데이터 저장
            save_raw(df_raw, billing_ym, output_paths)
            
            # 3. 데이터 변환
            logger.info("데이터 변환 시작")
            dfs_transformed = transform_all(df_raw)
            
            # 4. LLM 정규화 (옵션)
            if Config.USE_LLM_NORMALIZATION:
                logger.info("LLM 정규화 시작")
                dfs_transformed['fact_sagemaker_costs'] = clean_data(dfs_transformed['fact_sagemaker_costs'])
            
            # 5. 처리된 데이터 저장
            write_processed(dfs_transformed, billing_ym, output_paths)
            
            # 6. 매니페스트 생성
            row_counts = get_transform_stats(dfs_transformed)
            write_manifest(billing_ym, row_counts, output_paths)
            
            # 7. 최신 링크 생성
            make_latest_symlink(billing_ym, output_paths)
            
            # 8. 결과 요약 출력
            summary = get_processed_summary(billing_ym, output_paths)
            
            logger.info("=" * 50)
            logger.info("ETL 파이프라인 완료!")
            logger.info(f"청구 연월: {billing_ym}")
            logger.info(f"원시 데이터: {len(df_raw)}행")
            logger.info(f"처리된 파일: {len(summary['files'])}개")
            logger.info(f"총 크기: {summary['total_size_mb']}MB")
            logger.info(f"출력 디렉토리: {summary['processed_dir']}")
            logger.info("=" * 50)
            
            # 행 수 상세 정보
            for name, count in row_counts.items():
                logger.info(f"  {name}: {count}행")
            
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"ETL 파이프라인 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
