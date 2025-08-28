"""
의도 분류기: 사용자 질문을 분석하여 적절한 Agent로 라우팅
"""

from typing import Literal

IntentType = Literal["sql", "docs", "general"]


def classify_intent(question: str) -> IntentType:
    """
    사용자 질문의 의도를 분류하여 적절한 Agent 타입을 반환
    
    Args:
        question: 사용자 질문
        
    Returns:
        "sql": CUR 데이터 기반 비용 분석 질문
        "docs": SageMaker/Cloud Radar 문서 관련 질문  
        "general": 일반적인 대화/안내 질문
    """
    question_lower = question.lower()
    
    # SQL Agent 키워드 (비용, 데이터, 분석 관련)
    sql_keywords = [
        "비용", "cost", "금액", "요금", "지출", "사용량", "사용률",
        "분석", "통계", "집계", "합계", "평균", "최대", "최소",
        "데이터", "테이블", "파일", "csv", "parquet",
        "sagemaker", "notebook", "studio", "training", "inference",
        "storage", "processing", "datatransfer", "featurestore"
    ]
    
    # Docs Agent 키워드 (문서, 가이드, 설정 관련)
    docs_keywords = [
        "문서", "documentation", "가이드", "guide", "설정", "configuration",
        "설치", "install", "사용법", "usage", "예제", "example",
        "tutorial", "튜토리얼", "best practice", "모범 사례",
        "api", "reference", "참조", "방법", "어떻게"
    ]
    
    # Docs 의도 확인 (SQL보다 우선)
    if any(keyword in question_lower for keyword in docs_keywords):
        return "docs"
    
    # SQL 의도 확인
    if any(keyword in question_lower for keyword in sql_keywords):
        return "sql"
    
    # General Agent 키워드 (일반 대화, 안내 관련)
    general_keywords = [
        "안녕", "hello", "hi", "도움말", "help", "도움", "assist",
        "감사", "thank", "고마워", "thanks", "천만에요", "welcome"
    ]
    
    # General 의도 확인
    if any(keyword in question_lower for keyword in general_keywords):
        return "general"
    
    # 기본값은 general
    return "general"
