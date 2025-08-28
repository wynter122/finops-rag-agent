import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# .env 파일 로드
load_dotenv()


def generate_sql(question: str, schema_json: str, model: str = "gpt-4o-mini") -> str:
    """자연어 질문을 SQL로 변환합니다.
    
    Args:
        question: 사용자 질문
        schema_json: 스키마 정보 JSON 문자열
        model: 사용할 LLM 모델명
        
    Returns:
        LLM이 생성한 SQL JSON 응답
        
    Raises:
        Exception: LLM 호출 실패 시
    """
    # 동적 프롬프트 생성
    system_prompt = f"""당신은 AWS SageMaker 비용 분석 챗봇이다.
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
    
    llm = ChatOpenAI(model=model, temperature=0)
    
    # 직접 메시지 생성 (템플릿 사용하지 않음)
    from langchain_core.messages import SystemMessage, HumanMessage
    
    system_msg = SystemMessage(content=system_prompt)
    human_msg = HumanMessage(content=question)
    
    resp = llm.invoke([system_msg, human_msg])
    return resp.content


def parse_sql_response(response: str) -> str:
    """LLM 응답에서 SQL을 추출합니다.
    
    Args:
        response: LLM 응답 문자열
        
    Returns:
        추출된 SQL 문자열
        
    Raises:
        ValueError: SQL 파싱에 실패한 경우
    """
    try:
        # JSON 형식으로 파싱 시도
        parsed = json.loads(response)
        if "sql" in parsed:
            return parsed["sql"]
    except json.JSONDecodeError:
        pass
    
    # JSON 파싱 실패 시 직접 SQL 추출 시도
    if "SELECT" in response.upper():
        # SELECT로 시작하는 부분을 찾아서 추출
        lines = response.split('\n')
        sql_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('```'):
                sql_lines.append(line)
        
        if sql_lines:
            return ' '.join(sql_lines)
    
    raise ValueError(f"LLM SQL 파싱 실패: {response}")
