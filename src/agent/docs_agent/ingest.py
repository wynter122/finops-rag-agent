"""
문서 수집/파싱/임베딩 모듈
SageMaker 공식 문서의 HTML 분할본을 수집하고 벡터스토어에 저장
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import chromadb
from langchain_community.document_loaders import DirectoryLoader, BSHTMLLoader
from langchain.text_splitter import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import tqdm
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def load_html_files(src_pattern: str) -> List[Document]:
    """
    HTML 파일들을 로드하고 원문 추출
    
    Args:
        src_pattern: HTML 파일 패턴 (예: "docs/sagemaker/*.html")
        
    Returns:
        Document 리스트 (각각 .page_content, .metadata['source'])
    """
    print(f"HTML 파일 로딩 중: {src_pattern}")
    
    # DirectoryLoader로 HTML 파일들 로드
    loader = DirectoryLoader(
        path=os.path.dirname(src_pattern),
        glob=os.path.basename(src_pattern),
        loader_cls=BSHTMLLoader,
        show_progress=True
    )
    
    documents = loader.load()
    print(f"로드된 문서 수: {len(documents)}")
    
    return documents

 
def parse_sections(documents: List[Document]) -> List[Dict[str, Any]]:
    """
    헤더(H1/H2/H3) 단위로 텍스트 나누기
    
    Args:
        documents: 로드된 Document 리스트
        
    Returns:
        섹션별로 분리된 문서 리스트
    """
    print("섹션 파싱 중...")
    
    # HTML 헤더 기반 텍스트 분할기
    header_splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=[
            ("h1", "H1"),
            ("h2", "H2"), 
            ("h3", "H3")
        ]
    )
    
    sections = []
    
    for doc in tqdm.tqdm(documents, desc="섹션 파싱"):
        try:
            # 헤더 기반으로 섹션 분할
            doc_sections = header_splitter.split_text(doc.page_content)
            
            for i, section in enumerate(doc_sections):
                section_data = {
                    "content": section.page_content,
                    "metadata": {
                        **doc.metadata,
                        "section_order": i,
                        "section_headers": section.metadata.get("headers", {})
                    }
                }
                sections.append(section_data)
                
        except Exception as e:
            print(f"섹션 파싱 실패 (파일: {doc.metadata.get('source', 'unknown')}): {e}")
            continue
    
    print(f"생성된 섹션 수: {len(sections)}")
    return sections


def chunk_text(sections: List[Dict[str, Any]], chunk_size: int = 2000, chunk_overlap: int = 200) -> List[Dict[str, Any]]:
    """
    길이 기준으로 청크 생성 (500-800 토큰 목표)
    
    Args:
        sections: 섹션별 문서 리스트
        chunk_size: 청크 크기 (문자 단위)
        chunk_overlap: 청크 오버랩 (문자 단위)
        
    Returns:
        청크별로 분리된 문서 리스트
    """
    print("청크 생성 중...")
    
    # 재귀적 문자 분할기
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = []
    
    for section in tqdm.tqdm(sections, desc="청크 생성"):
        try:
            # 섹션 텍스트를 청크로 분할
            section_chunks = text_splitter.split_text(section["content"])
            
            for i, chunk_text in enumerate(section_chunks):
                # 청크 ID 생성: "{doc_id}#{section_anchor}#{order:04d}"
                doc_id = Path(section["metadata"]["source"]).stem
                section_anchor = f"s{section['metadata']['section_order']:02d}"
                chunk_id = f"{doc_id}#{section_anchor}#{i:04d}"
                
                chunk_data = {
                    "id": chunk_id,
                    "content": chunk_text,
                    "metadata": {
                        **section["metadata"],
                        "chunk_order": i,
                        "chunk_id": chunk_id
                    }
                }
                chunks.append(chunk_data)
                
        except Exception as e:
            print(f"청크 생성 실패: {e}")
            continue
    
    print(f"생성된 청크 수: {len(chunks)}")
    return chunks


def attach_metadata(chunks: List[Dict[str, Any]], version_date: str, doc_type: str = "developer-guide") -> List[Dict[str, Any]]:
    """
    메타데이터 부착
    
    Args:
        chunks: 청크 리스트
        version_date: 문서 버전 날짜
        doc_type: 문서 타입
        
    Returns:
        메타데이터가 부착된 청크 리스트
    """
    print("메타데이터 부착 중...")
    
    # URL 매핑 (파일명 → URL)
    url_mapping = {
        "sagemaker-overview": "https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html",
        "sagemaker-getting-started": "https://docs.aws.amazon.com/sagemaker/latest/dg/gs.html",
        # 추가 URL 매핑은 필요에 따라 확장
    }
    
    for chunk in chunks:
        # 기본 메타데이터
        chunk["metadata"].update({
            "version_date": version_date,
            "doc_type": doc_type,
            "order": chunk["metadata"].get("chunk_order", 0)
        })
        
        # 제목 추출 (H1 → title, H2/H3 → section)
        headers = chunk["metadata"].get("section_headers", {})
        chunk["metadata"]["title"] = headers.get("H1", "Unknown Title")
        chunk["metadata"]["section"] = headers.get("H2", headers.get("H3", "Unknown Section"))
        
        # URL 설정
        doc_id = Path(chunk["metadata"]["source"]).stem
        chunk["metadata"]["url"] = url_mapping.get(doc_id, f"https://docs.aws.amazon.com/sagemaker/latest/dg/{doc_id}.html")
    
    return chunks


def embed_and_store(chunks: List[Dict[str, Any]], index_dir: str) -> None:
    """
    임베딩 생성 후 Chroma에 저장
    
    Args:
        chunks: 메타데이터가 부착된 청크 리스트
        index_dir: Chroma 인덱스 저장 경로
    """
    print("임베딩 생성 및 저장 중...")
    
    # OpenAI 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        dimensions=1536
    )
    
    # Chroma 클라이언트 초기화
    chroma_client = chromadb.PersistentClient(path=index_dir)
    
    # 컬렉션 생성 또는 가져오기
    collection_name = "sagemaker_docs"
    try:
        collection = chroma_client.get_collection(name=collection_name)
        print(f"기존 컬렉션 사용: {collection_name}")
    except:
        collection = chroma_client.create_collection(
            name=collection_name,
            metadata={"description": "SageMaker documentation chunks"}
        )
        print(f"새 컬렉션 생성: {collection_name}")
    
    # 중복 방지를 위한 텍스트 해시 저장
    existing_hashes = set()
    if collection.count() > 0:
        # 기존 문서들의 해시 수집
        results = collection.get(include=["metadatas"])
        for metadata in results["metadatas"]:
            if metadata and "text_hash" in metadata:
                existing_hashes.add(metadata["text_hash"])
    
    # 청크별로 임베딩 생성 및 저장
    texts_to_add = []
    metadatas_to_add = []
    ids_to_add = []
    
    for chunk in tqdm.tqdm(chunks, desc="임베딩 처리"):
        # 텍스트 해시 생성
        text_hash = hashlib.md5(chunk["content"].encode()).hexdigest()
        
        # 중복 체크
        if text_hash in existing_hashes:
            continue
        
        # 임베딩 생성
        try:
            embedding = embeddings.embed_query(chunk["content"])
            
            # 메타데이터 정리 (Chroma는 기본 타입만 허용)
            clean_metadata = {}
            for key, value in chunk["metadata"].items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    clean_metadata[key] = value
                elif isinstance(value, dict):
                    # 딕셔너리는 JSON 문자열로 변환
                    clean_metadata[key] = json.dumps(value)
                else:
                    # 기타 타입은 문자열로 변환
                    clean_metadata[key] = str(value)
            
            clean_metadata["text_hash"] = text_hash
            
            texts_to_add.append(chunk["content"])
            metadatas_to_add.append(clean_metadata)
            ids_to_add.append(chunk["id"])
            
            existing_hashes.add(text_hash)
            
        except Exception as e:
            print(f"임베딩 생성 실패 (청크: {chunk['id']}): {e}")
            continue
    
    # 배치로 Chroma에 추가
    if texts_to_add:
        collection.add(
            documents=texts_to_add,
            metadatas=metadatas_to_add,
            ids=ids_to_add
        )
        print(f"저장된 새 청크 수: {len(texts_to_add)}")
    else:
        print("저장할 새 청크가 없습니다.")


def write_manifest(chunks: List[Dict[str, Any]], index_dir: str, version_date: str, doc_type: str = "developer-guide") -> None:
    """
    매니페스트 파일 작성
    
    Args:
        chunks: 청크 리스트
        index_dir: 인덱스 디렉토리
        version_date: 버전 날짜
        doc_type: 문서 타입
    """
    print("매니페스트 작성 중...")
    
    # 고유 문서 수 계산
    unique_docs = len(set(chunk["metadata"]["source"] for chunk in chunks))
    
    manifest = {
        "doc_type": doc_type,
        "version_date": version_date,
        "num_docs": unique_docs,
        "num_chunks": len(chunks),
        "index_dir": index_dir
    }
    
    # 매니페스트 저장 경로
    manifest_dir = Path("data/processed/docs")
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "manifest.json"
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"매니페스트 저장 완료: {manifest_path}")
    print(f"문서 수: {unique_docs}, 청크 수: {len(chunks)}")


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description="SageMaker 문서 수집 및 벡터스토어 저장")
    parser.add_argument(
        "--src", 
        default="docs/sagemaker/*.html",
        help="HTML 파일 패턴 (기본값: docs/sagemaker/*.html)"
    )
    parser.add_argument(
        "--index",
        default=".chroma/sagemaker",
        help="Chroma 인덱스 저장 경로 (기본값: .chroma/sagemaker)"
    )
    parser.add_argument(
        "--version-date",
        required=True,
        help="문서 버전 날짜 (예: 2025-08-01)"
    )
    parser.add_argument(
        "--doc-type",
        default="developer-guide",
        help="문서 타입 (기본값: developer-guide)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=2000,
        help="청크 크기 (기본값: 2000)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="청크 오버랩 (기본값: 200)"
    )
    
    args = parser.parse_args()
    
    try:
        # 1. HTML 파일 로딩
        documents = load_html_files(args.src)
        
        if not documents:
            print("로드할 HTML 파일이 없습니다.")
            return
        
        # 2. 섹션 파싱
        sections = parse_sections(documents)
        
        # 3. 청크 생성
        chunks = chunk_text(sections, args.chunk_size, args.chunk_overlap)
        
        # 4. 메타데이터 부착
        chunks = attach_metadata(chunks, args.version_date, args.doc_type)
        
        # 5. 임베딩 및 저장
        embed_and_store(chunks, args.index)
        
        # 6. 매니페스트 작성
        write_manifest(chunks, args.index, args.version_date, args.doc_type)
        
        print("문서 수집 및 벡터스토어 저장 완료!")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
