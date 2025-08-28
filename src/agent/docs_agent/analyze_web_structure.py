#!/usr/bin/env python3
"""
웹 문서 구조 분석 스크립트
지정된 URL의 웹 문서 구조를 분석
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import List, Dict, Any
import json
import argparse
import sys
import os

# 결과 저장 디렉토리 (루트의 data/web_structure/)
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "web_structure"

def analyze_web_structure(url: str = None):
    """웹 문서 구조 분석"""
    
    # 기본 URL 설정
    if url is None:
        url = "https://docs.aws.amazon.com/sagemaker/latest/dg/machine-learning-environments.html"
    
    print(f"🔍 웹 문서 구조 분석 시작")
    print(f"📄 분석 대상: {url}")
    print("=" * 80)
    
    # 페이지 가져오기
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"❌ 페이지 가져오기 실패: {e}")
        return
    
    # BeautifulSoup으로 파싱
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. 제목과 헤더 구조 분석
    print("📋 1. 문서 제목 및 헤더 구조")
    print("-" * 50)
    
    title = soup.find('title')
    if title:
        print(f"제목: {title.get_text().strip()}")
    
    # H1, H2, H3 헤더 추출
    headers = {
        'H1': [],
        'H2': [],
        'H3': []
    }
    
    for h1 in soup.find_all('h1'):
        headers['H1'].append(h1.get_text().strip())
    
    for h2 in soup.find_all('h2'):
        headers['H2'].append(h2.get_text().strip())
    
    for h3 in soup.find_all('h3'):
        headers['H3'].append(h3.get_text().strip())
    
    print(f"H1 헤더 ({len(headers['H1'])}개):")
    for h1 in headers['H1']:
        print(f"  - {h1}")
    
    print(f"\nH2 헤더 ({len(headers['H2'])}개):")
    for h2 in headers['H2']:
        print(f"  - {h2}")
    
    print(f"\nH3 헤더 ({len(headers['H3'])}개):")
    for h3 in headers['H3']:
        print(f"  - {h3}")
    
    # 2. 링크 구조 분석
    print(f"\n🔗 2. 문서 내 링크 구조 분석")
    print("-" * 50)
    
    base_url = "https://docs.aws.amazon.com/sagemaker/latest/dg/"
    sagemaker_links = []
    
    # 모든 링크 찾기
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        link_text = link.get_text().strip()
        
        # SageMaker 관련 링크만 필터링
        if href and ('sagemaker' in href.lower() or 'sagemaker' in link_text.lower()):
            # 상대 URL을 절대 URL로 변환
            if href.startswith('/'):
                full_url = urljoin(base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(base_url, href)
            
            sagemaker_links.append({
                'text': link_text,
                'url': full_url,
                'href': href
            })
    
    print(f"발견된 SageMaker 관련 링크 ({len(sagemaker_links)}개):")
    for link in sagemaker_links:
        print(f"  - {link['text']} -> {link['url']}")
    
    # 3. 주요 섹션 및 서비스 분석
    print(f"\n📚 3. 주요 SageMaker 서비스 및 환경 분석")
    print("-" * 50)
    
    # 문서 내용에서 주요 서비스 추출
    content_text = soup.get_text()
    
    # 주요 SageMaker 서비스 키워드
    services = [
        'Amazon SageMaker Studio',
        'Amazon SageMaker Studio Classic', 
        'Amazon SageMaker Notebook Instances',
        'Amazon SageMaker Studio Lab',
        'Amazon SageMaker Canvas',
        'Amazon SageMaker geospatial',
        'RStudio on Amazon SageMaker',
        'SageMaker HyperPod',
        'Amazon SageMaker AutoPilot',
        'Amazon SageMaker Feature Store',
        'Amazon SageMaker Model Monitor',
        'Amazon SageMaker Pipelines',
        'Amazon SageMaker JumpStart',
        'Amazon SageMaker Ground Truth',
        'Amazon SageMaker Data Wrangler',
        'Amazon SageMaker Model Registry',
        'Amazon SageMaker Projects',
        'Amazon SageMaker ML Lineage',
        'Amazon SageMaker Model Building Pipeline',
        'Amazon SageMaker Training Compiler',
        'Amazon SageMaker Inference Recommender',
        'Amazon SageMaker Edge Manager',
        'Amazon SageMaker Neo',
        'Amazon SageMaker Clarify',
        'Amazon SageMaker Debugger'
    ]
    
    found_services = []
    for service in services:
        if service.lower() in content_text.lower():
            found_services.append(service)
    
    print(f"문서에서 발견된 SageMaker 서비스 ({len(found_services)}개):")
    for service in found_services:
        print(f"  - {service}")
    
    # 4. Topics 섹션 분석
    print(f"\n📖 4. Topics 섹션 분석")
    print("-" * 50)
    
    # Topics 섹션 찾기
    topics_section = soup.find('div', class_='topics')
    if topics_section:
        topic_links = topics_section.find_all('a')
        print(f"Topics 섹션에서 발견된 링크 ({len(topic_links)}개):")
        for link in topic_links:
            href = link.get('href', '')
            text = link.get_text().strip()
            if href:
                full_url = urljoin(base_url, href)
                print(f"  - {text} -> {full_url}")
    else:
        print("Topics 섹션을 찾을 수 없습니다.")
    
    # 5. 문서 구조 요약
    print(f"\n📊 5. 문서 구조 요약")
    print("-" * 50)
    
    summary = {
        'title': title.get_text().strip() if title else 'Unknown',
        'headers': headers,
        'sagemaker_links_count': len(sagemaker_links),
        'found_services_count': len(found_services),
        'found_services': found_services,
        'sagemaker_links': sagemaker_links
    }
    
    print(f"문서 제목: {summary['title']}")
    print(f"총 헤더 수: H1({len(headers['H1'])}), H2({len(headers['H2'])}), H3({len(headers['H3'])}")
    print(f"SageMaker 관련 링크: {len(sagemaker_links)}개")
    print(f"발견된 서비스: {len(found_services)}개")
    
    # 결과를 JSON으로 저장 (docs_agent/data/ 디렉토리에)
    DATA_DIR.mkdir(exist_ok=True)
    
    parsed_url = urlparse(url)
    filename = Path(parsed_url.path).stem
    if not filename:
        filename = "analysis"
    
    output_filename = DATA_DIR / f"web_structure_analysis_{filename}.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 분석 완료! 결과가 '{output_filename}'에 저장되었습니다.")
    
    return summary


def main():
    """메인 함수 - 명령행 인자 처리"""
    parser = argparse.ArgumentParser(
        description="웹 문서 구조 분석 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python analyze_web_structure.py
  python analyze_web_structure.py --url "https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html"
  python analyze_web_structure.py -u "https://docs.aws.amazon.com/sagemaker/latest/dg/gs.html"
        """
    )
    
    parser.add_argument(
        '--url', '-u',
        type=str,
        help='분석할 웹 문서 URL (기본값: machine-learning-environments.html)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='결과 JSON 파일명 (기본값: web_structure_analysis_{filename}.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세한 분석 정보 출력'
    )
    
    args = parser.parse_args()
    
    try:
        # URL 분석 실행
        result = analyze_web_structure(args.url)
        
        if args.verbose:
            print(f"\n🔍 상세 분석 결과:")
            print(f"분석 URL: {args.url or '기본 URL'}")
            print(f"문서 제목: {result['title']}")
            print(f"총 링크 수: {result['sagemaker_links_count']}")
            print(f"발견된 서비스 수: {result['found_services_count']}")
        
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
