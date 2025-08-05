"""フィードパーサーの単体テスト"""
import sys
from pathlib import Path

# srcをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from tumu.feed import zenn, classmethod, ggen, qiita, googlecloud, aws, huggingface, deepmind 


def test_zenn_feed():
    """Zennフィードの基本テスト"""
    result = zenn.get_feed()
    assert result.total_count > 0
    assert len(result.articles) > 0
    
    # トピック指定
    python_result = zenn.get_feed("python")
    assert "python" in python_result.feed_url


def test_classmethod_feed():
    """ClassMethodフィードの基本テスト"""
    result = classmethod.get_feed()
    assert result.total_count > 0
    
    # タグ指定
    aws_result = classmethod.get_feed("aws")
    assert "aws" in aws_result.feed_url


def test_ggen_feed():
    """G-GENフィードの基本テスト"""
    result = ggen.get_feed()
    assert result.total_count > 0
    assert all(a.source == "ggen" for a in result.articles)


def test_qiita_feed():
    """Qiitaフィードの基本テスト"""
    result = qiita.get_feed()
    assert result.total_count > 0
    
    # タグ指定
    python_result = qiita.get_feed("python")
    assert len(python_result.articles) > 0


def test_googlecloud_feed():
    """Google Cloudフィードの基本テスト"""
    # 日本語（デフォルト）
    ja_result = googlecloud.get_feed()
    assert ja_result.total_count > 0
    assert all(a.source == "googlecloud_ja" for a in ja_result.articles)
    
    # 英語
    en_result = googlecloud.get_feed("en")
    assert all(a.source == "googlecloud_en" for a in en_result.articles)


def test_aws_feed():
    """AWSフィードの基本テスト"""
    # 日本語（デフォルト）
    ja_result = aws.get_feed()
    assert ja_result.total_count > 0
    assert all(a.source == "aws_ja" for a in ja_result.articles)


def test_huggingface_feed():
    """huggingfaceフィードの基本テスト"""
    result = huggingface.get_feed()
    assert result.total_count > 0


def test_deepmind_feed():
    """deepmindフィードの基本テスト"""
    result = deepmind.get_feed()
    assert result.total_count > 0


def test_article_structure():
    """記事の構造が正しいかテスト"""
    result = zenn.get_feed()
    if result.articles:
        article = result.articles[0]
        
        # 必須フィールド
        assert article.title
        assert article.url
        assert article.published_date
        assert article.source
        
        # 辞書変換
        article_dict = article.to_dict()
        assert isinstance(article_dict, dict)
        assert "title" in article_dict
        assert "url" in article_dict


def test_all_feeds_work():
    """全フィードが動作することを確認"""
    feeds = [
        ("Zenn", lambda: zenn.get_feed()),
        ("ClassMethod", lambda: classmethod.get_feed()),
        ("G-GEN", lambda: ggen.get_feed()),
        ("Qiita", lambda: qiita.get_feed()),
        ("Google Cloud", lambda: googlecloud.get_feed()),
        ("AWS", lambda: aws.get_feed()),
        ("huggingface", lambda: huggingface.get_feed()),
        ("deepmind", lambda: deepmind.get_feed()),
    ]
    
    for name, get_feed in feeds:
        result = get_feed()
        assert result is not None, f"{name}のフィード取得に失敗"
        assert hasattr(result, 'articles'), f"{name}にarticles属性がない"
        assert hasattr(result, 'total_count'), f"{name}にtotal_count属性がない"