#!/usr/bin/env python3
"""
AWS SageMaker 문서 웹 스크래핑 모듈
실제 AWS 공식 문서를 웹에서 파싱하여 로컬에 저장
"""

import os
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
import tqdm
from dotenv import load_dotenv
from doc_urls import get_combined_urls, get_urls_by_category

# .env 파일 로드
load_dotenv()


class SageMakerDocScraper:
    """AWS SageMaker 문서 스크래퍼"""
    
    def __init__(self, base_url: str = "https://docs.aws.amazon.com/sagemaker/latest/dg/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_page_content(self, url: str) -> Optional[str]:
        """웹 페이지 내용 가져오기"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"페이지 가져오기 실패 ({url}): {e}")
            return None
    
    def clean_html_content(self, html_content: str) -> str:
        """HTML 내용 정리"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 불필요한 요소 제거
        for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
            element.decompose()
        
        # AWS 문서 특화 정리
        # 사이드바, 네비게이션 등 제거
        for element in soup.find_all(['div'], class_=re.compile(r'sidebar|nav|toc|breadcrumb')):
            element.decompose()
        
        return str(soup)
    
    def extract_title_and_headers(self, html_content: str) -> Dict[str, Any]:
        """제목과 헤더 추출"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 제목 추출
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
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
        
        return {
            'title': title,
            'headers': headers
        }
    
    def scrape_sagemaker_docs(self, doc_urls: List[str]) -> List[Dict[str, Any]]:
        """SageMaker 문서 스크래핑 - 결과를 리턴만 하고 저장하지 않음"""
        print(f"웹 문서 스크래핑 시작...")
        print(f"대상 URL 수: {len(doc_urls)}")
        
        scraped_docs = []
        
        for url in tqdm.tqdm(doc_urls, desc="문서 스크래핑"):
            try:
                # 페이지 내용 가져오기
                html_content = self.get_page_content(url)
                if not html_content:
                    continue
                
                # HTML 정리
                cleaned_html = self.clean_html_content(html_content)
                
                # 제목과 헤더 추출
                title_headers = self.extract_title_and_headers(html_content)
                
                # 파일명 생성
                parsed_url = urlparse(url)
                filename = Path(parsed_url.path).stem
                if not filename:
                    filename = "index"
                
                # 문서 정보만 저장 (파일 저장하지 않음)
                doc_info = {
                    'url': url,
                    'filename': f"{filename}.html",
                    'html_content': cleaned_html,  # HTML 내용도 포함
                    'title': title_headers['title'],
                    'headers': title_headers['headers'],
                    'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                scraped_docs.append(doc_info)
                
                # 요청 간격 조절 (AWS 서버 부하 방지)
                time.sleep(1)
                
            except Exception as e:
                print(f"스크래핑 실패 ({url}): {e}")
                continue
        
        print(f"스크래핑 완료: {len(scraped_docs)}개 문서")
        
        return scraped_docs


# get_sagemaker_doc_urls 함수는 doc_urls.py에서 import하여 사용


def main():
    """메인 실행 함수"""
    print("🚀 AWS SageMaker 문서 웹 스크래핑 시작")
    
    # 스크래퍼 초기화
    scraper = SageMakerDocScraper()
    
    # 문서 URL 목록 가져오기 (분석 데이터에서만 추출)
    doc_urls = get_combined_urls()
    
    print(f"📋 스크래핑할 SageMaker 문서 URL: {len(doc_urls)}개")
    print("🔹 URL 소스:")
    print("  - 분석 데이터에서 동적으로 추출된 URL")
    print("  - 중복 제거 및 정규화 완료")
    
    # URL 목록 출력 (처음 10개만)
    for i, url in enumerate(doc_urls[:10], 1):
        print(f"  {i:2d}. {url}")
    if len(doc_urls) > 10:
        print(f"  ... 및 {len(doc_urls) - 10}개 더")
    
    # 스크래핑 실행
    scraped_docs = scraper.scrape_sagemaker_docs(doc_urls)
    
    print(f"\n✅ 스크래핑 완료!")
    print(f"📄 문서 수: {len(scraped_docs)}")
    
    # 결과 요약
    print(f"\n📋 스크래핑된 문서들:")
    for doc in scraped_docs:
        print(f"  - {doc['title']} ({doc['filename']})")
    
    return scraped_docs


if __name__ == "__main__":
    main()
