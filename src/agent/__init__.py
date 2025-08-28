"""
멀티에이전트 시스템

Router Agent가 사용자 질문의 의도를 파악하여 적절한 Agent로 라우팅:
- SQL Agent: CUR 기반 비용 질의 응답
- Docs Agent: SageMaker/Cloud Radar 공식 문서 기반 RAG Q&A  
- General Agent: 일반적인 대화/안내 응답
"""

from .router.graph import ask as router_ask

__all__ = ["router_ask"]
