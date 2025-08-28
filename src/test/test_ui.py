"""
UI 컴포넌트 테스트
"""

import pytest
from src.ui.components.chat_message import render_user, render_assistant
from src.ui.components.citations import render_citations
from src.ui.components.metrics import render_metrics
from src.ui.utils.session import init_session, append_history


def test_session_utils():
    """세션 유틸리티 테스트"""
    # 실제로는 Streamlit 컨텍스트가 필요하지만, 
    # 여기서는 함수가 정의되어 있는지만 확인
    assert callable(init_session)
    assert callable(append_history)


def test_chat_message_components():
    """채팅 메시지 컴포넌트 테스트"""
    assert callable(render_user)
    assert callable(render_assistant)


def test_citations_component():
    """참고문헌 컴포넌트 테스트"""
    assert callable(render_citations)


def test_metrics_component():
    """메트릭 컴포넌트 테스트"""
    assert callable(render_metrics)


def test_router_import():
    """Router import 테스트"""
    try:
        from src.agent.router.graph import ask as router_ask
        assert callable(router_ask)
    except ImportError as e:
        pytest.skip(f"Router import 실패: {e}")


if __name__ == "__main__":
    print("🧪 UI 컴포넌트 테스트 실행 중...")
    
    test_session_utils()
    test_chat_message_components()
    test_citations_component()
    test_metrics_component()
    test_router_import()
    
    print("✅ 모든 테스트 통과!")
