#!/usr/bin/env python3
"""
계약 기반 계정 관리 모듈
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from ..utils.logging import get_logger

logger = get_logger(__name__)

class ContractManager:
    """계약 기반 계정 관리자"""
    
    def __init__(self, contracts_file: str = "contracts.json"):
        self.contracts_file = Path(contracts_file)
        self.contracts_data = self._load_contracts()
    
    def _load_contracts(self) -> Dict:
        """계약 파일 로드"""
        try:
            if self.contracts_file.exists():
                with open(self.contracts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"계약 파일 로드 완료: {self.contracts_file}")
                return data
            else:
                logger.warning(f"계약 파일이 없습니다: {self.contracts_file}")
                return {"contracts": {}, "default_contract": None}
        except Exception as e:
            logger.error(f"계약 파일 로드 실패: {e}")
            return {"contracts": {}, "default_contract": None}
    
    def get_contract(self, contract_id: str) -> Optional[Dict]:
        """계약 정보 조회"""
        contracts = self.contracts_data.get("contracts", {})
        return contracts.get(contract_id)
    
    def get_contract_accounts(self, contract_id: str) -> List[str]:
        """계약의 계정 목록 조회"""
        contract = self.get_contract(contract_id)
        if contract:
            return contract.get("accounts", [])
        return []
    
    def list_contracts(self) -> Dict[str, Dict]:
        """모든 계약 목록 조회"""
        return self.contracts_data.get("contracts", {})
    
    def get_default_contract(self) -> Optional[str]:
        """기본 계약 ID 조회"""
        return self.contracts_data.get("default_contract")
    
    def validate_contract(self, contract_id: str) -> bool:
        """계약 유효성 검증"""
        contract = self.get_contract(contract_id)
        if not contract:
            logger.error(f"계약을 찾을 수 없습니다: {contract_id}")
            return False
        
        accounts = contract.get("accounts", [])
        if not accounts:
            logger.error(f"계약에 계정이 없습니다: {contract_id}")
            return False
        
        logger.info(f"계약 검증 완료: {contract_id} ({len(accounts)}개 계정)")
        return True
    
    def get_contract_summary(self, contract_id: str) -> Dict:
        """계약 요약 정보"""
        contract = self.get_contract(contract_id)
        if not contract:
            return {}
        
        return {
            "contract_id": contract_id,
            "name": contract.get("name", ""),
            "description": contract.get("description", ""),
            "account_count": len(contract.get("accounts", [])),
            "accounts": contract.get("accounts", []),
            "billing_owner": contract.get("billing_owner", ""),
            "tags": contract.get("tags", [])
        }
