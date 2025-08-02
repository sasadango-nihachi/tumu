"""AWS公式ブログ用フィードパーサー"""
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


class AWSParser:
    """AWS公式ブログフィードパーサー"""
    
    SOURCE_NAME = "aws"
    
    # 言語別のフィードURL
    FEED_URLS = {
        "ja": "https://aws.amazon.com/jp/blogs/news/feed/",  # 日本語版
        "en": "https://aws.amazon.com/jp/blogs/aws/feed/"   # 英語版
    }
    
    @staticmethod
    def parse_feed(url: str, lang: str = "ja") -> FeedResult:
        """
        フィードをパースしてFeedResultを返す
        
        Args:
            url: フィードのURL
            lang: 言語設定（"ja" or "en"）
            
        Returns:
            FeedResult: パースされた結果
        """
        f = feedparser.parse(url)
        articles = []
        
        # フィード情報（言語を含める）
        base_title = f.feed.get('title', 'AWS Blog')
        feed_title = f"{base_title} ({lang.upper()})"
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            
            # summaryまたはdescriptionを使用
            summary = entry.get('summary', '') or entry.get('description', '')
            
            # 著者情報
            author = entry.get('author', '')
            if not author and 'dc:creator' in entry:
                author = entry.get('dc:creator', '')
            elif not author and 'authors' in entry:
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
            
            # media:thumbnailから取得
            if 'media_thumbnail' in entry:
                thumbnails = entry.get('media_thumbnail', [])
                if thumbnails and isinstance(thumbnails, list):
                    image_url = thumbnails[0].get('url')
            
            # media:contentから取得
            if not image_url and 'media_content' in entry:
                media_contents = entry.get('media_content', [])
                for media in media_contents:
                    if media.get('type', '').startswith('image/'):
                        image_url = media.get('url')
                        break
            
            # enclosureから画像を探す
            if not image_url:
                for enclosure in entry.get('enclosures', []):
                    if enclosure.get('type', '').startswith('image/'):
                        image_url = enclosure.get('href')
                        break
            
            # contentから画像を抽出（最終手段）
            if not image_url and summary:
                import re
                img_match = re.search(r'<img[^>]+src="([^"]+)"', summary)
                if img_match:
                    image_url = img_match.group(1)
            
            # ソース名に言語を含める
            source_with_lang = f"{AWSParser.SOURCE_NAME}_{lang}"
            
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

def get_feed(lang: Literal["ja", "en"] = "ja") -> FeedResult:
    """
    AWS公式ブログのフィードを取得
    
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
    if lang not in AWSParser.FEED_URLS:
        raise ValueError(f"Unsupported language: {lang}. Use 'ja' or 'en'.")
    
    url = AWSParser.FEED_URLS[lang]
    return AWSParser.parse_feed(url, lang)


def get_feed_by_url(url: str) -> FeedResult:
    """
    カスタムURLからフィードを取得
    
    Args:
        url: フィードのURL
        
    Returns:
        FeedResult: フィード取得結果
    """
    # URLから言語を推測
    if "/jp/blogs/news/" in url:
        lang = "ja"
    elif "/blogs/aws/" in url:
        lang = "en"
    else:
        lang = "ja"  # デフォルト
    
    return AWSParser.parse_feed(url, lang)


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


# よく見られるカテゴリ/サービス
class PopularCategories:
    """AWS Blogでよく使われるカテゴリ"""
    # コンピューティング
    EC2 = "Amazon EC2"
    LAMBDA = "AWS Lambda"
    ECS = "Amazon ECS"
    EKS = "Amazon EKS"
    
    # ストレージ
    S3 = "Amazon S3"
    EBS = "Amazon EBS"
    EFS = "Amazon EFS"
    
    # データベース
    RDS = "Amazon RDS"
    DYNAMODB = "Amazon DynamoDB"
    AURORA = "Amazon Aurora"
    
    # 分析
    ATHENA = "Amazon Athena"
    REDSHIFT = "Amazon Redshift"
    QUICKSIGHT = "Amazon QuickSight"
    
    # AI/ML
    SAGEMAKER = "Amazon SageMaker"
    REKOGNITION = "Amazon Rekognition"
    BEDROCK = "Amazon Bedrock"
    
    # その他
    CLOUDFORMATION = "AWS CloudFormation"
    CDK = "AWS CDK"
    SECURITY = "Security"
    ARCHITECTURE = "Architecture"


if __name__ == "__main__":
    # 使用例1: 日本語版の取得（デフォルト）
    print("=== AWS Blog (日本語) ===")
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
                print(f"   カテゴリ: {', '.join(article.tags[:3])}")
    
    # 使用例2: 英語版の取得
    print("\n\n=== AWS Blog (English) ===")
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
    