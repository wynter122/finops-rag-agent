#!/usr/bin/env python3
"""
Chroma DB 확인 테스트 스크립트
"""

import chromadb
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리 찾기
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)

# .env 파일 로드
load_dotenv()

def test_chroma_db():
    """Chroma DB 상태 및 데이터 확인"""
    
    print("🔍 Chroma DB 확인 시작...")
    
    # Chroma 클라이언트 초기화
    chroma_client = chromadb.PersistentClient(path=".chroma/sagemaker_web")
    
    # 컬렉션 목록 확인
    collections = chroma_client.list_collections()
    print(f"\n📚 컬렉션 목록: {[col.name for col in collections]}")
    
    # sagemaker_docs 컬렉션 가져오기
    collection = chroma_client.get_collection(name="sagemaker_docs")
    print(f"\n📖 컬렉션 이름: {collection.name}")
    print(f"📊 총 문서 수: {collection.count()}")
    
    # 모든 문서 조회
    results = collection.get(include=["documents", "metadatas"])
    
    print(f"\n📄 저장된 문서들 ({len(results['documents'])}개):")
    print("=" * 80)
    
    # 문서 목록을 간단히 요약해서 표시
    print("\n📋 문서 목록 요약:")
    for i, (doc, metadata) in enumerate(zip(results["documents"], results["metadatas"])):
        print(f"   {i+1:2d}. {metadata.get('title', 'N/A')} - {metadata.get('section', 'N/A')}")
    
    # 상세 정보는 처음 5개만 표시
    print(f"\n📝 상세 문서 정보 (처음 5개):")
    print("=" * 80)
    
    for i, (doc, metadata) in enumerate(zip(results["documents"][:5], results["metadatas"][:5])):
        print(f"\n📝 문서 {i+1}:")
        print(f"   ID: {results['ids'][i]}")
        print(f"   제목: {metadata.get('title', 'N/A')}")
        print(f"   섹션: {metadata.get('section', 'N/A')}")
        print(f"   URL: {metadata.get('url', 'N/A')}")
        print(f"   문서 타입: {metadata.get('doc_type', 'N/A')}")
        print(f"   버전: {metadata.get('version_date', 'N/A')}")
        print(f"   내용 (처음 150자): {doc[:150]}...")
        print("-" * 60)
    
    if len(results['documents']) > 5:
        print(f"\n... 나머지 {len(results['documents']) - 5}개 문서는 생략")
    
    # 검색 테스트
    print(f"\n🔍 검색 테스트:")
    print("=" * 80)
    
    # 다양한 검색 쿼리 테스트
    test_queries = [
        "SageMaker Overview",
        "cost optimization", 
        "training models",
        "notebook instances",
        "machine learning service",
        "warm pools"
    ]
    
    for query in test_queries:
        print(f"\n🔍 '{query}' 검색 결과:")
        print("-" * 50)
        
        try:
            query_results = collection.query(
                query_texts=[query],
                n_results=5,  # 결과 수 증가
                include=["documents", "metadatas", "distances"]
            )
            
            if not query_results["documents"][0]:
                print("   검색 결과가 없습니다.")
                continue
            
            for i, (doc, metadata, distance) in enumerate(zip(
                query_results["documents"][0], 
                query_results["metadatas"][0], 
                query_results["distances"][0]
            )):
                # Chroma의 cosine distance는 0~2 범위이므로 0~1로 정규화
                similarity = 1 - (distance / 2.0)
                
                # 유사도에 따른 등급 표시
                if similarity >= 0.8:
                    grade = "🟢 매우 높음"
                elif similarity >= 0.6:
                    grade = "🟡 높음"
                elif similarity >= 0.4:
                    grade = "🟠 보통"
                else:
                    grade = "🔴 낮음"
                
                print(f"   결과 {i+1} (유사도: {similarity:.3f}) {grade}:")
                print(f"   제목: {metadata.get('title', 'N/A')}")
                print(f"   섹션: {metadata.get('section', 'N/A')}")
                print(f"   URL: {metadata.get('url', 'N/A')}")
                print(f"   내용: {doc[:150]}...")
                print()
                
        except Exception as e:
            print(f"   검색 중 오류 발생: {e}")
            continue
    
    # 임베딩 모델 정보 출력
    print(f"\n📊 임베딩 모델 정보:")
    print(f"   모델: text-embedding-3-small")
    print(f"   차원: 1536")
    print(f"   거리 측정: Cosine Distance")
    print(f"   참고: 유사도 = 1 - 거리")

if __name__ == "__main__":
    test_chroma_db()
