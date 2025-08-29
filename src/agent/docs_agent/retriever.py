"""
벡터스토어 검색기
문서 질의에 대한 관련 문서 검색 (LangChain + Chroma)
"""

from typing import List, Dict, Any, Tuple
import os
import time
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langsmith import traceable
from langchain.callbacks import LangChainTracer

# .env 파일 로드
load_dotenv()


def _get_embeddings(model_name: str):
    """임베딩 모델 초기화"""
    return OpenAIEmbeddings(model=model_name, dimensions=1536)


def load_vectorstore(index_dir: str, embed_model: str) -> Chroma:
    """
    Chroma 벡터스토어 로드
    
    Args:
        index_dir: Chroma 인덱스 디렉토리 경로
        embed_model: 임베딩 모델명
        
    Returns:
        Chroma 벡터스토어 인스턴스
    """
    return Chroma(
        collection_name="sagemaker_docs",
        persist_directory=index_dir,
        embedding_function=_get_embeddings(embed_model),
    )


def _avg_score(scores: List[float]) -> float:
    """평균 점수 계산"""
    return sum(scores) / max(1, len(scores))


def _normalize_score(score: float) -> float:
    """유사도 점수를 0~1 범위로 정규화"""
    # Chroma의 기본 유사도 점수는 보통 -1~1 범위
    # 이를 0~1 범위로 변환
    return max(0.0, min(1.0, (score + 1) / 2))


def _dedup_by_text(contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """중복 텍스트 제거 (선택적 기능)"""
    seen_texts = set()
    deduped = []
    
    for ctx in contexts:
        # 텍스트의 첫 100자로 중복 판단
        text_key = ctx["text"][:100].strip()
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            deduped.append(ctx)
    
    return deduped


def format_contexts(docs_with_scores: List[Tuple[Any, float]], top_n: int) -> List[Dict[str, Any]]:
    """
    검색 결과를 표준화된 컨텍스트 형식으로 변환
    
    Args:
        docs_with_scores: (Document, score) 튜플 리스트
        top_n: 반환할 컨텍스트 수
        
    Returns:
        표준화된 컨텍스트 리스트
    """
    contexts = []
    for i, (doc, score) in enumerate(docs_with_scores[:top_n]):
        md = doc.metadata or {}
        contexts.append({
            "id": md.get("id") or md.get("chunk_id") or f"doc-{i}",
            "text": doc.page_content,
            "score": _normalize_score(float(score)),  # 0~1 범위로 정규화
            "metadata": {
                "title": md.get("title", ""),
                "section": md.get("section", ""),
                "url": md.get("url", ""),
                "version_date": md.get("version_date", ""),
                "source": md.get("source", "aws-doc"),
                "doc_type": md.get("doc_type", "developer-guide"),
            },
        })
    return contexts


@traceable(name="docs_retriever")
def retrieve(
    question: str,
    top_k: int = 20,
    top_n: int = 8,
    threshold: float = 0.35,
    index_dir: str = ".chroma/sagemaker_web",
    embed_model: str = "text-embedding-3-small"
) -> Dict[str, Any]:
    """
    질의에 대한 관련 문서 검색 (LangGraph의 docs_agent.graph에서 직접 호출)
    
    Args:
        question: 검색 질의
        top_k: 검색할 문서 수 (벡터 검색)
        top_n: 반환할 컨텍스트 수 (후처리)
        threshold: 신뢰 임계값 (평균 점수가 이 값보다 낮으면 빈 컨텍스트 반환)
        index_dir: Chroma 인덱스 디렉토리 경로
        embed_model: 임베딩 모델명
        
    Returns:
        검색 결과 딕셔너리
    """
    start_time = time.time()
    
    try:
        # 벡터스토어 로드
        vs = load_vectorstore(index_dir, embed_model)
        
        # relevance score: 0~1 (LangChain이 보장)
        docs_with_scores = vs.similarity_search_with_relevance_scores(question, k=top_k)
        
        # 점수 추출 및 평균 계산 (정규화된 점수 사용)
        scores = [_normalize_score(float(s)) for (_, s) in docs_with_scores]
        avg_score = _avg_score(scores)
        
        # 컨텍스트 포맷팅
        contexts = format_contexts(docs_with_scores, top_n=top_n)
        
        # 중복 제거 (선택적)
        # contexts = _dedup_by_text(contexts)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # threshold 판정: avg가 낮으면 안전 응답을 위한 빈 컨텍스트 반환
        if avg_score < threshold:
            return {
                "contexts": [],
                "avg_score": avg_score,
                "top_k": top_k,
                "top_n": top_n,
                "latency_ms": latency_ms,
                "context_ids": []
            }
        
        context_ids = [ctx["id"] for ctx in contexts[:3]]  # 로깅용 상위 3개 ID
        
        return {
            "contexts": contexts,
            "avg_score": avg_score,
            "top_k": top_k,
            "top_n": top_n,
            "latency_ms": latency_ms,
            "context_ids": context_ids
        }
        
    except Exception as e:
        # 에러 발생 시 빈 결과 반환
        return {
            "contexts": [],
            "avg_score": 0.0,
            "top_k": top_k,
            "top_n": top_n,
            "latency_ms": int((time.time() - start_time) * 1000),
            "context_ids": [],
            "error": str(e)
        }


class DocumentRetriever:
    """문서 검색기 (기존 인터페이스 호환성)"""
    
    def __init__(self, store_path: str = ".chroma/sagemaker_web"):
        """
        검색기 초기화
        
        Args:
            store_path: Chroma 인덱스 경로
        """
        self.store_path = store_path
        self.embed_model = "text-embedding-3-small"
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        질의에 대한 관련 문서 검색 (기존 인터페이스)
        
        Args:
            query: 검색 질의
            top_k: 반환할 문서 수
            
        Returns:
            관련 문서 목록
        """
        result = retrieve(
            question=query,
            top_k=top_k * 2,  # 더 많은 후보에서 선택
            top_n=top_k,
            threshold=0.0,  # 임계값 비활성화
            index_dir=self.store_path,
            embed_model=self.embed_model
        )
        return result.get("contexts", [])
    
    def get_relevant_context(self, query: str, top_k: int = 3) -> str:
        """
        질의에 대한 관련 컨텍스트 반환 (기존 인터페이스)
        
        Args:
            query: 검색 질의
            top_k: 반환할 문서 수
            
        Returns:
            관련 컨텍스트 문자열
        """
        result = retrieve(
            question=query,
            top_k=top_k * 2,
            top_n=top_k,
            threshold=0.35,
            index_dir=self.store_path,
            embed_model=self.embed_model
        )
        
        contexts = result.get("contexts", [])
        if not contexts:
            return ""
        
        # 문서들을 하나의 컨텍스트로 결합
        context_parts = []
        for ctx in contexts:
            metadata = ctx.get("metadata", {})
            context_parts.append(f"제목: {metadata.get('title', 'Unknown')}")
            context_parts.append(f"섹션: {metadata.get('section', '')}")
            context_parts.append(f"내용: {ctx.get('text', '')}")
            context_parts.append("---")
        
        return "\n".join(context_parts)


def get_retriever(store_path: str = ".chroma/sagemaker_web") -> DocumentRetriever:
    """
    문서 검색기 인스턴스 반환 (기존 인터페이스)
    
    Args:
        store_path: Chroma 인덱스 경로
        
    Returns:
        DocumentRetriever 인스턴스
    """
    return DocumentRetriever(store_path)
