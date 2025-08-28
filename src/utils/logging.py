import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = 'finops_etl', level: str = 'INFO') -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    
    if logger.handlers:  # 이미 설정된 경우 중복 방지
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # 파일 핸들러 (data 디렉토리에 로그 저장)
    log_dir = Path('data/logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'etl_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = 'finops_etl') -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)
