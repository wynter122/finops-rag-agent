import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict
import pandas as pd

from ..core.config import Config
from ..utils.logging import get_logger

logger = get_logger(__name__)

def write_processed(dfs: Dict[str, pd.DataFrame], billing_ym: str, output_paths: dict):
    """처리된 데이터를 Parquet과 CSV로 저장"""
    processed_dir = output_paths['processed_dir']
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"처리된 데이터 저장 시작: {processed_dir}")
    
    saved_files = []
    
    for name, df in dfs.items():
        if len(df) == 0:
            logger.warning(f"{name}: 빈 DataFrame이므로 저장을 건너뜁니다.")
            continue
        
        # Parquet 저장
        parquet_path = processed_dir / f"{name}.parquet"
        df.to_parquet(parquet_path, index=False)
        saved_files.append(str(parquet_path))
        
        # CSV 저장 (검증용)
        csv_path = processed_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False, quoting=1)  # quoting=1: 모든 필드를 따옴표로 감싸기
        saved_files.append(str(csv_path))
        
        logger.info(f"{name}: {len(df)}행 저장 완료")
    
    logger.info(f"총 {len(saved_files)}개 파일 저장 완료")
    return saved_files

def write_manifest(billing_ym: str, row_counts: Dict[str, int], output_paths: dict, schema_version: str = "1.0"):
    """매니페스트 파일 생성"""
    manifest_path = output_paths['manifest']
    
    manifest = {
        "billing_ym": billing_ym,
        "created_at": datetime.now().isoformat(),
        "schema_version": schema_version,
        "row_counts": row_counts,
        "files": []
    }
    
    # 처리된 파일 목록 수집
    processed_dir = output_paths['processed_dir']
    if processed_dir.exists():
        for file_path in processed_dir.glob("*"):
            if file_path.is_file():
                manifest["files"].append({
                    "name": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
    
    # 매니페스트 저장
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    logger.info(f"매니페스트 저장 완료: {manifest_path}")
    return manifest

def make_latest_symlink(billing_ym: str, output_paths: dict):
    """최신 데이터에 대한 심볼릭 링크 생성"""
    processed_dir = output_paths['processed_dir']
    latest_link = Config.OUTPUT_DIR / 'processed' / 'latest'
    
    try:
        # 기존 링크 제거
        if latest_link.exists():
            if latest_link.is_symlink():
                latest_link.unlink()
            else:
                shutil.rmtree(latest_link)
        
            # 새 심볼릭 링크 생성
        if os.name == 'nt':  # Windows
            # Windows에서는 심볼릭 링크 대신 디렉토리 복사
            if processed_dir.exists():
                shutil.copytree(processed_dir, latest_link, dirs_exist_ok=True)
                logger.info(f"Windows: latest 디렉토리 복사 완료: {latest_link}")
        else:  # Unix/Linux
            # 심볼릭 링크 생성 (상대 경로 사용)
            relative_path = os.path.relpath(processed_dir, latest_link.parent)
            latest_link.symlink_to(relative_path, target_is_directory=True)
            logger.info(f"심볼릭 링크 생성 완료: {latest_link} -> {relative_path}")
            
    except Exception as e:
        logger.warning(f"latest 링크 생성 실패: {e}")

def get_processed_summary(billing_ym: str, output_paths: dict) -> Dict:
    """처리된 데이터 요약 정보 반환"""
    processed_dir = output_paths['processed_dir']
    
    summary = {
        "billing_ym": billing_ym,
        "processed_dir": str(processed_dir),
        "files": [],
        "total_size_mb": 0
    }
    
    if processed_dir.exists():
        for file_path in processed_dir.glob("*.parquet"):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                summary["files"].append({
                    "name": file_path.name,
                    "size_mb": round(size_mb, 2)
                })
                summary["total_size_mb"] += size_mb
        
        summary["total_size_mb"] = round(summary["total_size_mb"], 2)
    
    return summary
