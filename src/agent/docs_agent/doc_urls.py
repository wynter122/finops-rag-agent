#!/usr/bin/env python3
"""
SageMaker 문서 URL 목록 정의
분석 데이터에서 URL을 동적으로 추출하여 관리
"""

from typing import List, Dict, Any
import json
from pathlib import Path
import re

# AWS SageMaker 문서 기본 URL
SAGEMAKER_BASE_URL = "https://docs.aws.amazon.com/sagemaker/latest/dg/"


def get_urls_by_category(category: str) -> List[str]:
    """특정 카테고리의 URL 목록 반환"""
    categories = get_urls_from_analysis_data_by_category()
    return categories.get(category, [])


def get_urls_from_analysis_data() -> List[str]:
    """data/web_structure/ 디렉토리의 분석 결과 파일들에서 URL 추출"""
    data_dir = Path(__file__).parent.parent.parent.parent / "data" / "web_structure"
    urls = []
    
    if not data_dir.exists():
        print(f"⚠️  데이터 디렉토리가 존재하지 않습니다: {data_dir}")
        return urls
    
    # JSON 파일들 찾기
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        print(f"⚠️  데이터 디렉토리에 JSON 파일이 없습니다: {data_dir}")
        return urls
    
    print(f"📁 분석 데이터에서 URL 추출 중... ({len(json_files)}개 파일)")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # sagemaker_links에서 URL 추출
            if 'sagemaker_links' in data:
                for link in data['sagemaker_links']:
                    if 'url' in link and link['url']:
                        urls.append(link['url'])
            
            print(f"  ✅ {json_file.name}: {len(data.get('sagemaker_links', []))}개 링크 추출")
            
        except Exception as e:
            print(f"  ❌ {json_file.name} 처리 실패: {e}")
    
    # 중복 제거
    unique_urls = list(set(urls))
    print(f"📊 총 {len(unique_urls)}개 고유 URL 추출 완료")
    
    return unique_urls


def get_urls_from_analysis_data_by_category() -> Dict[str, List[str]]:
    """분석 데이터에서 카테고리별로 URL 분류"""
    urls = get_urls_from_analysis_data()
    
    # URL을 카테고리별로 분류
    categories = {
        "studio": [],
        "notebook": [],
        "training": [],
        "inference": [],
        "autopilot": [],
        "feature_store": [],
        "monitoring": [],
        "pipelines": [],
        "canvas": [],
        "geospatial": [],
        "rstudio": [],
        "hyperpod": [],
        "jupyter": [],
        "security": [],
        "assets": [],
        "algorithms": [],
        "frameworks": [],
        "partner": [],
        "migration": [],
        "other": []
    }
    
    for url in urls:
        url_lower = url.lower()
        
        if 'studio' in url_lower:
            if 'classic' in url_lower:
                categories["studio"].append(url)
            elif 'lab' in url_lower:
                categories["studio"].append(url)
            else:
                categories["studio"].append(url)
        elif 'notebook' in url_lower or 'nbi' in url_lower:
            categories["notebook"].append(url)
        elif 'training' in url_lower:
            categories["training"].append(url)
        elif 'inference' in url_lower:
            categories["inference"].append(url)
        elif 'autopilot' in url_lower:
            categories["autopilot"].append(url)
        elif 'feature-store' in url_lower:
            categories["feature_store"].append(url)
        elif 'monitor' in url_lower:
            categories["monitoring"].append(url)
        elif 'pipeline' in url_lower:
            categories["pipelines"].append(url)
        elif 'canvas' in url_lower:
            categories["canvas"].append(url)
        elif 'geospatial' in url_lower:
            categories["geospatial"].append(url)
        elif 'rstudio' in url_lower:
            categories["rstudio"].append(url)
        elif 'hyperpod' in url_lower:
            categories["hyperpod"].append(url)
        elif 'jupyter' in url_lower:
            categories["jupyter"].append(url)
        elif 'security' in url_lower:
            categories["security"].append(url)
        elif 'assets' in url_lower:
            categories["assets"].append(url)
        elif 'algorithm' in url_lower:
            categories["algorithms"].append(url)
        elif 'framework' in url_lower:
            categories["frameworks"].append(url)
        elif 'partner' in url_lower:
            categories["partner"].append(url)
        elif 'migrate' in url_lower:
            categories["migration"].append(url)
        else:
            categories["other"].append(url)
    
    # 빈 카테고리 제거
    return {k: v for k, v in categories.items() if v}


def get_combined_urls(limit: int = None) -> List[str]:
    """분석 데이터에서 URL 추출"""
    analysis_urls = get_urls_from_analysis_data()
    
    # 중복 제거
    unique_urls = list(set(analysis_urls))
    
    print(f"📊 URL 추출 결과:")
    print(f"  - 분석 데이터 URL: {len(analysis_urls)}개")
    print(f"  - 중복 제거 후: {len(unique_urls)}개")
    
    if limit:
        unique_urls = unique_urls[:limit]
    
    return unique_urls


def print_url_summary():
    """URL 목록 요약 출력"""
    print("📋 SageMaker 문서 URL 목록 요약")
    print("=" * 60)
    
    # 분석 데이터 URL 요약
    print("\n🔹 분석 데이터 URL:")
    analysis_categories = get_urls_from_analysis_data_by_category()
    total_analysis = 0
    
    for category, urls in analysis_categories.items():
        print(f"  - {category.replace('_', ' ').title()} ({len(urls)}개):")
        for url in urls:
            filename = url.split('/')[-1]
            print(f"    * {filename}")
        total_analysis += len(urls)
    
    print(f"  📊 총 분석 데이터 URL: {total_analysis}개")
    
    # 최종 URL 요약
    print("\n🔹 최종 URL 목록:")
    final_urls = get_combined_urls()
    print(f"  📊 총 URL: {len(final_urls)}개")


if __name__ == "__main__":
    print_url_summary()
