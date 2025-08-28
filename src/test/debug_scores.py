"""
점수 정규화 디버그 스크립트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent.docs_agent.retriever import _normalize_score, retrieve

def debug_score_normalization():
    """점수 정규화 디버그"""
    print("🔍 점수 정규화 디버그 시작...")
    
    # 테스트 점수들
    test_scores = [-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4]
    
    print("📊 원본 점수 -> 정규화된 점수:")
    for score in test_scores:
        normalized = _normalize_score(score)
        print(f"  {score:6.2f} -> {normalized:6.3f}")
    
    # 실제 검색 결과로 테스트
    print("\n🔍 실제 검색 결과 점수 정규화:")
    result = retrieve(
        question="Training Compiler",
        top_k=5,
        top_n=3,
        threshold=0.0  # 임계값 비활성화
    )
    
    print(f"평균 점수 (정규화 전): {result['avg_score']:.3f}")
    
    if result['contexts']:
        print("상위 3개 컨텍스트의 정규화된 점수:")
        for i, ctx in enumerate(result['contexts'][:3]):
            print(f"  {i+1}. {ctx['score']:.3f}")
    else:
        print("컨텍스트가 없습니다.")

if __name__ == "__main__":
    debug_score_normalization()
