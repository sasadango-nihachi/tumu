"""Anthropicニュース取得の最小限テスト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import Mock, patch
from tumu.webscraper.anthropicnews import (
    get_anthropic_news_urls,
    get_article_details
)


def test_get_anthropic_news_urls_basic():
    """基本的なURL取得テスト"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = """
            <a href="/news/article1">Article 1</a>
            <a href="/news/article2">Article 2</a>
            <a href="/news">News Index</a>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        urls = get_anthropic_news_urls()
        
        assert len(urls) == 2  # /newsで終わるURLは除外
        assert all('/news/' in url for url in urls)


def test_get_article_details_basic():
    """基本的な記事詳細取得テスト"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = """
            <h1 class="h2">Test Title</h1>
            <div class="PostDetail_post-timestamp__TBJ0Z">2024年1月1日 ● 5分</div>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = get_article_details("https://example.com/news/test")
        
        assert result['title'] == "Test Title"
        assert result['date'] == "2024年1月1日"


def test_error_handling():
    """エラーハンドリングのテスト"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Network error")
        
        # URL取得でエラー
        urls = get_anthropic_news_urls()
        assert urls == []
        
        # 記事詳細取得でエラー
        result = get_article_details("https://example.com")
        assert result['title'] == "取得エラー"