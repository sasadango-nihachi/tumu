"""Hugging Face用フィードパーサー"""
import feedparser
from datetime import datetime
from typing import List

# 共通モデルをインポート
try:
    from ..core.models import Article, FeedResult
except ImportError:
    # 直接実行時用
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import Article, FeedResult


class HuggingFaceParser:
    """Hugging Faceフィードパーサー"""
    
    SOURCE_NAME = "huggingface"
    FEED_URL = "https://huggingface.co/blog/feed.xml"
    
    @staticmethod
    def parse_feed(url: str) -> FeedResult:
        """
        フィードをパースしてFeedResultを返す
        
        Args:
            url: フィードのURL
            
        Returns:
            FeedResult: パースされた結果
        """
        f = feedparser.parse(url)
        articles = []
        
        # フィード情報
        feed_title = f.feed.get('title', 'Hugging Face Blog')
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            
            # summaryまたはdescriptionを使用
            summary = entry.get('summary', '') or entry.get('description', '')
            
            # 著者情報
            author = entry.get('author', '')
            if not author and 'authors' in entry:
                authors = entry.get('authors', [])
                if authors and isinstance(authors, list):
                    author = authors[0].get('name', '')
            
            # 日付のパース
            pub_time = datetime.now()
            if 'published_parsed' in entry and entry['published_parsed']:
                try:
                    pub_time = datetime(*entry['published_parsed'][:6])
                except:
                    pass
            elif 'updated_parsed' in entry and entry['updated_parsed']:
                try:
                    pub_time = datetime(*entry['updated_parsed'][:6])
                except:
                    pass
            
            formatted_date = pub_time.strftime('%Y年%m月%d日')
            
            # タグの取得
            tags = []
            for tag in entry.get('tags', []):
                if isinstance(tag, dict) and 'term' in tag:
                    tags.append(tag['term'])
            
            # カテゴリからもタグを取得
            for category in entry.get('categories', []):
                if isinstance(category, str):
                    tags.append(category)
                elif isinstance(category, dict) and 'term' in category:
                    tags.append(category['term'])
            
            # 画像URLの取得
            image_url = None
            
            # enclosureから画像を探す
            for enclosure in entry.get('enclosures', []):
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href')
                    break
            
            # contentから画像を抽出
            if not image_url and summary:
                import re
                img_match = re.search(r'<img[^>]+src="([^"]+)"', summary)
                if img_match:
                    image_url = img_match.group(1)
            
            article = Article(
                title=title,
                url=article_url,
                published_date=formatted_date,
                source=HuggingFaceParser.SOURCE_NAME,
                summary=summary,
                author=author,
                tags=tags,
                image_url=image_url
            )
            
            articles.append(article)
        
        return FeedResult(
            articles=articles,
            feed_title=feed_title,
            feed_url=url,
            fetched_at=datetime.now()
        )


# 便利な関数（高レベルAPI）

def get_feed() -> FeedResult:
    """
    Hugging Face公式ブログのフィードを取得
    
    Returns:
        FeedResult: フィード取得結果
        
    Example:
        >>> result = get_feed()
        >>> print(f"記事数: {result.total_count}")
    """
    return HuggingFaceParser.parse_feed(HuggingFaceParser.FEED_URL)


def get_feed_by_url(url: str) -> FeedResult:
    """
    カスタムURLからフィードを取得（将来の拡張用）
    
    Args:
        url: フィードのURL
        
    Returns:
        FeedResult: フィード取得結果
    """
    return HuggingFaceParser.parse_feed(url)


# Hugging Faceの主要トピック（参考）
class Topics:
    """Hugging Faceブログの主要トピック"""
    TRANSFORMERS = "Transformers"
    DATASETS = "Datasets"
    TOKENIZERS = "Tokenizers"
    DIFFUSERS = "Diffusers"
    GRADIO = "Gradio"
    SPACES = "Spaces"
    MODELS = "Models"
    RESEARCH = "Research"
    COMMUNITY = "Community"
    TUTORIAL = "Tutorial"


if __name__ == "__main__":
    # 使用例
    print("=== Hugging Face Blog ===")
    result = get_feed()
    print(f"フィードタイトル: {result.feed_title}")
    print(f"記事数: {result.total_count}")
    print(f"取得日時: {result.fetched_at}")
    
    if result.articles:
        print("\n最新のブログ記事:")
        for i, article in enumerate(result.articles[:5], 1):
            print(f"\n{i}. {article.title}")
            print(f"   著者: {article.author}")
            print(f"   URL: {article.url}")
            print(f"   日付: {article.published_date}")
            if article.tags:
                print(f"   タグ: {', '.join(article.tags[:3])}")
            print(f"   要約: {article.short_summary}")