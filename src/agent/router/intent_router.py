"""
의도 분류기: 사용자 질문을 분석하여 적절한 Agent로 라우팅
LLM + 규칙 하이브리드 방식으로 정확도와 유연성을 향상
"""

from typing import Literal, TypedDict
from functools import lru_cache
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableConfig

# .env 파일 로드
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # 암호화된 .env 파일이 있을 수 있음
    load_dotenv()

logger = logging.getLogger(__name__)

IntentType = Literal["sql", "docs", "general"]


class IntentResult(TypedDict):
    intent: IntentType          # "sql" | "docs" | "general"
    confidence: float           # 0.0 ~ 1.0
    reason: str                 # 분류 근거(한글 요약)


# --- LLM 분류기 설정 ---
_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=20)

_prompt = ChatPromptTemplate.from_template(
    """너는 질문 의도 분류기다. 사용자 질문을 분석하여 적절한 의도를 분류해라.

가능한 의도는 "sql", "docs", "general" 뿐이다.

의도 정의 및 예시:
- sql: CUR/비용/사용량/집계/테이블/쿼리/월별 비용 등 수치 기반 분석 요청
  예시: "이번달 SageMaker 비용", "Notebook 시간 합계", "소비 추이 그래프", "월별 사용량 통계"
- docs: SageMaker 기능/설정/개념/가이드/튜토리얼/레퍼런스 질문
  예시: "Studio 설정 방법", "Serverless Inference 작동 방식", "Feature Store 개념 설명", "API 레퍼런스"
- general: 인사/도움말/안내/잡담 등, 숫자질의·문서설명 둘 다 아닌 경우
  예시: "안녕", "도움말", "감사합니다", "고마워"

반드시 JSON만 출력:
{{"intent": "sql|docs|general", "confidence": 0.0~1.0, "reason": "짧은 근거"}}

주의사항:
- 문서 설명/설정/개념 질문은 docs
- 비용/합계/사용량/집계 등 수치 질의는 sql
- 그 외는 general
- 모호하면 가장 가능성 높은 하나만 고르되 reason에 근거 서술
- SQL 키워드가 포함돼도 "문서 설명을 해달라"면 docs
- 비용 분석이 아니라 "설정 방법/동작 방식"은 docs

질문: {question}"""
)

_parser = JsonOutputParser()


@lru_cache(maxsize=512)
def classify_intent(question: str) -> IntentResult:
    """
    사용자 질문의 의도를 분류하여 적절한 Agent 타입을 반환
    LLM 기반 분류로 정확도와 유연성을 향상
    
    Args:
        question: 사용자 질문
        
    Returns:
        IntentResult: intent, confidence, reason을 포함한 분류 결과
    """
    q = (question or "").strip()
    if not q:
        return {"intent": "general", "confidence": 0.5, "reason": "빈 질문"}
    
    try:
        # LangSmith 트레이싱 설정
        config: RunnableConfig = {
            "tags": ["router", "intent", "llm"],
            "metadata": {"question": q[:200]}
        }
        
        # LLM 체인 실행
        chain = _prompt | _llm | _parser
        out = chain.invoke({"question": q}, config=config)
        
        # 결과 검증
        intent = out.get("intent", "general")
        conf = float(out.get("confidence", 0.0))
        reason = str(out.get("reason", ""))
        
        # 유효한 의도인지 확인
        if intent not in ("sql", "docs", "general"):
            raise ValueError(f"Invalid intent: {intent}")
        
        logger.info(f"LLM classification successful: {intent} (conf: {conf}) for: {q}")
        return {"intent": intent, "confidence": conf, "reason": reason}
        
    except Exception as e:
        # LLM 실패 시 기본값 반환
        logger.warning(f"LLM classification failed for: {q}, error: {str(e)}")
        return {"intent": "general", "confidence": 0.3, "reason": f"LLM 실패로 기본값 사용: {str(e)}"}


# --- 하위 호환성을 위한 기존 함수 ---
def classify_intent_legacy(question: str) -> IntentType:
    """
    기존 API와의 호환성을 위한 함수
    새로운 코드에서는 classify_intent() 사용 권장
    """
    result = classify_intent(question)
    return result["intent"]
