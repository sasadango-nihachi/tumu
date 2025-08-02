"""Google Cloud Blog用フィードパーサー"""
import feedparser
from datetime import datetime
from typing import List, Optional, Literal

# 共通モデルをインポート
try:
    from ..core.models import Article, FeedResult
except ImportError:
    # 直接実行時用
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import Article, FeedResult


class GoogleCloudParser:
    """Google Cloud Blogフィードパーサー"""
    
    SOURCE_NAME = "googlecloud"
    BASE_URL = "https://cloudblog.withgoogle.com"
    
    # 言語別のフィードURL
    FEED_URLS = {
        "en": "https://cloudblog.withgoogle.com/rss/",
        "ja": "https://cloudblog.withgoogle.com/ja/rss/"
    }
    
    @staticmethod
    def parse_feed(url: str, lang: str = "en") -> FeedResult:
        """
        フィードをパースしてFeedResultを返す
        
        Args:
            url: フィードのURL
            lang: 言語設定（"en" or "ja"）
            
        Returns:
            FeedResult: パースされた結果
        """
        f = feedparser.parse(url)
        articles = []
        
        # フィード情報（言語を含める）
        base_title = f.feed.get('title', 'Google Cloud Blog')
        feed_title = f"{base_title} ({lang.upper()})"
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            
            # descriptionフィールドを使用（Google Cloud Blogの場合）
            summary = entry.get('description', '') or entry.get('summary', '')
            
            # 著者情報
            author = entry.get('author', '')
            if not author and 'dc:creator' in entry:
                author = entry.get('dc:creator', '')
            
            # 日付のパース
            pub_time = datetime.now()
            if 'published_parsed' in entry and entry['published_parsed']:
                try:
                    pub_time = datetime(*entry['published_parsed'][:6])
                except:
                    pass
            formatted_date = pub_time.strftime('%Y年%m月%d日')
            
            # カテゴリ/タグの取得
            tags = []
            
            # categoriesフィールドから取得
            for category in entry.get('categories', []):
                if isinstance(category, str):
                    tags.append(category)
                elif isinstance(category, dict) and 'term' in category:
                    tags.append(category['term'])
            
            # tagsフィールドからも取得
            for tag in entry.get('tags', []):
                if isinstance(tag, dict) and 'term' in tag:
                    tag_term = tag['term']
                    if tag_term not in tags:  # 重複を避ける
                        tags.append(tag_term)
            
            # 画像URLの取得
            image_url = None
            
            # media:thumbnailから取得（Google Cloud Blogでよく使われる）
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
            
            # ソース名に言語を含める
            source_with_lang = f"{GoogleCloudParser.SOURCE_NAME}_{lang}"
            
            article = Article(
                title=title,
                url=article_url,
                published_date=formatted_date,
                source=source_with_lang,
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

def get_feed(lang: Literal["en", "ja"] = "ja") -> FeedResult:
    """
    Google Cloud Blogのフィードを取得
    
    Args:
        lang: 言語設定
              - "ja": 日本語版（デフォルト）
              - "en": 英語版
        
    Returns:
        FeedResult: フィード取得結果
        
    Examples:
        >>> result = get_feed()  # 日本語版（デフォルト）
        >>> result = get_feed("ja")  # 日本語版を明示的に指定
        >>> result = get_feed("en")  # 英語版
    """
    if lang not in GoogleCloudParser.FEED_URLS:
        raise ValueError(f"Unsupported language: {lang}. Use 'en' or 'ja'.")
    
    url = GoogleCloudParser.FEED_URLS[lang]
    return GoogleCloudParser.parse_feed(url, lang)


def get_feed_by_url(url: str) -> FeedResult:
    """
    カスタムURLからフィードを取得
    
    Args:
        url: フィードのURL
        
    Returns:
        FeedResult: フィード取得結果
    """
    # URLから言語を推測
    lang = "ja" if "/ja/" in url else "en"
    return GoogleCloudParser.parse_feed(url, lang)


def get_all_feeds() -> dict[str, FeedResult]:
    """
    全言語のフィードを取得
    
    Returns:
        dict: 言語コードをキーとした結果の辞書
        
    Example:
        >>> all_feeds = get_all_feeds()
        >>> print(f"日本語版: {all_feeds['ja'].total_count}件")
        >>> print(f"英語版: {all_feeds['en'].total_count}件")
    """
    results = {}
    for lang in ["ja", "en"]:  # 日本語を先に
        results[lang] = get_feed(lang)
    return results


# よく見られるトピック/タグ
class PopularTopics:
    """Google Cloud Blogでよく使われるトピック"""
    AI_MACHINE_LEARNING = "AI & Machine Learning"
    COMPUTE = "Compute"
    CONTAINERS_KUBERNETES = "Containers & Kubernetes"
    DATA_ANALYTICS = "Data Analytics"
    DATABASES = "Databases"
    DEVELOPERS_PRACTITIONERS = "Developers & Practitioners"
    INFRASTRUCTURE = "Infrastructure"
    MANAGEMENT_TOOLS = "Management Tools"
    NETWORKING = "Networking"
    SECURITY = "Security"
    SERVERLESS = "Serverless"
    STORAGE_DATA_TRANSFER = "Storage & Data Transfer"


if __name__ == "__main__":
    # 使用例1: 日本語版の取得（デフォルト）
    print("=== Google Cloud Blog (日本語) ===")
    ja_result = get_feed()  # デフォルトで日本語
    print(f"フィードタイトル: {ja_result.feed_title}")
    print(f"記事数: {ja_result.total_count}")
    
    if ja_result.articles:
        print(f"\n最新記事（日本語）:")
        for i, article in enumerate(ja_result.articles[:3], 1):
            print(f"\n{i}. {article.title}")
            print(f"   著者: {article.author}")
            print(f"   URL: {article.url}")
            print(f"   日付: {article.published_date}")
            if article.tags:
                print(f"   タグ: {', '.join(article.tags[:3])}")
    
    # 使用例2: 英語版の取得
    print("\n\n=== Google Cloud Blog (English) ===")
    en_result = get_feed("en")
    print(f"フィードタイトル: {en_result.feed_title}")
    print(f"記事数: {en_result.total_count}")
    
    if en_result.articles:
        print(f"\n最新記事（英語）:")
        for i, article in enumerate(en_result.articles[:3], 1):
            print(f"\n{i}. {article.title}")
            print(f"   URL: {article.url}")
            print(f"   日付: {article.published_date}")
    
    # 使用例3: 両言語の比較
    print("\n\n=== 言語別の記事数比較 ===")
    all_feeds = get_all_feeds()
    for lang, result in all_feeds.items():
        print(f"{lang.upper()}: {result.total_count}件")
    
    # 使用例4: ソースの識別
    print("\n=== ソース識別の確認 ===")
    if en_result.articles:
        print(f"英語記事のソース: {en_result.articles[0].source}")  # "googlecloud_en"
    if ja_result.articles:
        print(f"日本語記事のソース: {ja_result.articles[0].source}")  # "googlecloud_ja"
    
    # 使用例5: 統合した使い方
    print("\n=== 英語と日本語の記事を統合 ===")
    all_articles = []
    all_articles.extend(en_result.articles)
    all_articles.extend(ja_result.articles)
    
    # 言語別に分類
    en_articles = [a for a in all_articles if a.source.endswith("_en")]
    ja_articles = [a for a in all_articles if a.source.endswith("_ja")]
    
    print(f"統合後 - 英語: {len(en_articles)}件, 日本語: {len(ja_articles)}件")
    print(f"合計: {len(all_articles)}件")