"""
Chroma 인덱스 디버그 스크립트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# .env 파일 로드
load_dotenv()

def debug_chroma_index():
    """Chroma 인덱스 상태 확인"""
    print("🔍 Chroma 인덱스 디버그 시작...")
    
    index_dir = ".chroma/sagemaker_web"
    embed_model = "text-embedding-3-small"
    
    try:
        # 임베딩 모델 초기화
        print(f"📝 임베딩 모델: {embed_model}")
        embeddings = OpenAIEmbeddings(model=embed_model, dimensions=384)
        
        # Chroma 벡터스토어 로드
        print(f"📁 인덱스 디렉토리: {index_dir}")
        vs = Chroma(
            collection_name="sagemaker_docs",
            persist_directory=index_dir,
            embedding_function=embeddings,
        )
        
        # 컬렉션 정보 확인
        print(f"📊 컬렉션 이름: {vs._collection.name}")
        print(f"📊 컬렉션 개수: {vs._collection.count()}")
        
        if vs._collection.count() == 0:
            print("❌ 컬렉션에 문서가 없습니다!")
            return
        
        # 샘플 문서 확인
        print("\n📄 샘플 문서 확인...")
        sample_docs = vs._collection.get(limit=3)
        
        if 'documents' in sample_docs and sample_docs['documents']:
            for i, doc in enumerate(sample_docs['documents'][:2]):
                print(f"문서 {i+1}:")
                print(f"  내용: {doc[:200]}...")
                if 'metadatas' in sample_docs and sample_docs['metadatas']:
                    print(f"  메타데이터: {sample_docs['metadatas'][i]}")
                print()
        
        # 간단한 검색 테스트
        print("🔍 간단한 검색 테스트...")
        test_query = "serverless"
        results = vs.similarity_search_with_relevance_scores(test_query, k=3)
        
        print(f"검색어: '{test_query}'")
        print(f"결과 수: {len(results)}")
        
        for i, (doc, score) in enumerate(results):
            print(f"결과 {i+1}:")
            print(f"  점수: {score}")
            print(f"  내용: {doc.page_content[:100]}...")
            print(f"  메타데이터: {doc.metadata}")
            print()
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_chroma_index()
