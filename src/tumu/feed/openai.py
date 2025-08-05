"""OpenAI用フィードパーサー"""
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


class OpenAIParser:
    """OpenAIフィードパーサー"""
    
    SOURCE_NAME = "openai"
    FEED_URL = "https://openai.com/blog/rss.xml"
    
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
        feed_title = f.feed.get('title', 'OpenAI Blog')
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            
            # summaryまたはdescriptionを使用
            summary = entry.get('summary', '') or entry.get('description', '')
            
            # 著者情報
            author = entry.get('author', 'OpenAI')
            if not author and 'dc:creator' in entry:
                author = entry.get('dc:creator', 'OpenAI')
            
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
            
            # タグ/カテゴリの取得
            tags = []
            
            # tagsフィールド
            for tag in entry.get('tags', []):
                if isinstance(tag, dict) and 'term' in tag:
                    tags.append(tag['term'])
            
            # categoriesフィールド
            for category in entry.get('categories', []):
                if isinstance(category, str):
                    tags.append(category)
                elif isinstance(category, dict) and 'term' in category:
                    tags.append(category['term'])
            
            # 画像URLの取得
            image_url = None
            
            # media:thumbnailから取得
            if 'media_thumbnail' in entry:
                thumbnails = entry.get('media_thumbnail', [])
                if thumbnails and isinstance(thumbnails, list):
                    image_url = thumbnails[0].get('url')
            
            # enclosureから画像を探す
            if not image_url:
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
                source=OpenAIParser.SOURCE_NAME,
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
    OpenAIブログのフィードを取得
    
    Returns:
        FeedResult: フィード取得結果
        
    Example:
        >>> result = get_feed()
        >>> print(f"記事数: {result.total_count}")
    """
    return OpenAIParser.parse_feed(OpenAIParser.FEED_URL)


def get_feed_by_url(url: str) -> FeedResult:
    """
    カスタムURLからフィードを取得（将来の拡張用）
    
    Args:
        url: フィードのURL
        
    Returns:
        FeedResult: フィード取得結果
    """
    return OpenAIParser.parse_feed(url)


# OpenAIの主要プロダクト/トピック（参考）
class Topics:
    """OpenAIの主要トピック"""
    GPT = "GPT"
    CHATGPT = "ChatGPT"
    DALL_E = "DALL-E"
    CODEX = "Codex"
    API = "API"
    SAFETY = "Safety"
    RESEARCH = "Research"
    PRODUCT = "Product"
    COMPANY = "Company"


if __name__ == "__main__":
    # 使用例
    print("=== OpenAI Blog ===")
    result = get_feed()
    print(f"フィードタイトル: {result.feed_title}")
    print(f"記事数: {result.total_count}")
    print(f"取得日時: {result.fetched_at}")
    
    if result.articles:
        print(f"\n最新記事:")
        for i, article in enumerate(result.articles[:5], 1):
            print(f"\n{i}. {article.title}")
            print(f"   URL: {article.url}")
            print(f"   日付: {article.published_date}")
            print(f"   著者: {article.author}")
            if article.tags:
                print(f"   タグ: {', '.join(article.tags[:3])}")
            print(f"   要約: {article.short_summary}")
    
    # GPT関連記事の検索（例）
    print("\n\n=== GPT関連記事 ===")
    gpt_articles = [a for a in result.articles if 'GPT' in a.title or 'gpt' in a.title.lower()]
    print(f"GPT関連記事: {len(gpt_articles)}件")
    
    for article in gpt_articles[:3]:
        print(f"- {article.title}")