import os, json, re
from typing import Dict, Any

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema.runnable import RunnableLambda

# ─────────────────────────────────────────────────────────────
# 전역 체인 관리
# ─────────────────────────────────────────────────────────────
_NL2SQL_CHAIN = None  # singleton

SYSTEM_PROMPT_TEMPLATE = """당신은 AWS SageMaker 비용 분석 챗봇이다.
사용 가능한 데이터셋은 DuckDB로 읽을 수 있는 Parquet 파일들이다.

아래는 파일과 컬럼 목록이다:
{schema_json}

규칙:
- DuckDB SQL만 작성한다.
- SELECT만 허용된다. INSERT/DELETE/UPDATE 금지.
- 결과는 JSON으로 {{"sql": "..."}} 형식으로만 반환한다.
- 파일을 읽을 때는 read_parquet() 함수를 사용한다
- 파일 경로는 상대 경로를 사용한다 (예: read_parquet('data/processed/latest/파일명.parquet'))
- 비용 관련 질문의 경우 unblended_cost, blended_cost 컬럼을 사용한다.
- 시간 관련 질문의 경우 bill_billingperiodstartdate, bill_billingperiodenddate 컬럼을 사용한다.
- 서비스별 분석의 경우 product_productname, lineitem_lineitemtype 컬럼을 사용한다.
- 날짜 필터는 하드코딩하지 말고 실제 데이터에 맞게 조정한다.
"""

def _make_llm():
    model = os.getenv("LLM_NL2SQL_MODEL", "gpt-4o-mini")
    try:
        temperature = float(os.getenv("LLM_NL2SQL_TEMPERATURE", "0.0"))
    except ValueError:
        temperature = 0.0
    try:
        timeout = float(os.getenv("LLM_NL2SQL_TIMEOUT", "25"))
    except ValueError:
        timeout = 25.0
    return ChatOpenAI(model=model, temperature=temperature, timeout=timeout)

def _post_validate_sql(sql: str) -> str:
    """SELECT-only, 금지 키워드 검증."""
    s = sql.strip().rstrip(";")
    if not re.match(r"(?is)^\s*select\b", s):
        raise ValueError("NL2SQL: SELECT 문이 아닙니다.")
    forbidden = r"(?is)\b(insert|update|delete|create|alter|drop|truncate|attach|copy|pragma)\b"
    if re.search(forbidden, s):
        raise ValueError("NL2SQL: 금지된 키워드가 포함되어 있습니다.")
    return s + ";"

def _sanitize_paths(sql: str, base_dir: str) -> str:
    """
    LLM이 예시대로 'data/processed/latest/...' 경로를 썼다면
    실제 base_dir(예: data/processed/202508)로 치환.
    """
    base_dir = base_dir.rstrip("/").replace("\\", "/")
    return sql.replace("data/processed/latest", base_dir)

def build_nl2sql_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_TEMPLATE),
        ("user", "{question}")
    ])
    llm = _make_llm()
    parser = StrOutputParser()

    def parse_and_validate(text: str) -> str:
        # 1) JSON 파싱
        try:
            obj = json.loads(text)
            sql = obj.get("sql") or ""
        except Exception as e:
            # 혹시 모델이 JSON 외 형식으로 응답하면 예외
            raise ValueError(f"NL2SQL: JSON 파싱 실패: {e}. 원문: {text[:200]}")
        return _post_validate_sql(sql)

    return prompt | llm | parser | RunnableLambda(parse_and_validate)

def get_nl2sql_chain():
    global _NL2SQL_CHAIN
    if _NL2SQL_CHAIN is None:
        _NL2SQL_CHAIN = build_nl2sql_chain()
    return _NL2SQL_CHAIN

# ─────────────────────────────────────────────────────────────
# 외부에서 쓰는 함수(래퍼) — ask.py가 이걸 호출
# ─────────────────────────────────────────────────────────────
def generate_sql(question: str, schema_json: str, base_dir: str, model: str = "gpt-4o-mini") -> str:
    """
    질문+스키마를 기반으로 SQL을 생성한다(체인 기반).
    - base_dir는 경로 보정에 사용된다.
    - 반환값은 최종 실행 가능한 DuckDB SQL 문자열.
    """
    chain = get_nl2sql_chain()
    raw_sql = chain.invoke({"question": question, "schema_json": schema_json})
    fixed_sql = _sanitize_paths(raw_sql, base_dir)
    return fixed_sql
