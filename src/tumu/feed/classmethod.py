"""ClassMethod Developers IO用フィードパーサー"""
import feedparser
from datetime import datetime
from typing import List, Optional

# 共通モデルをインポート（相対インポート）
try:
    from ..core.models import Article, FeedResult
except ImportError:
    # 直接実行時用
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import Article, FeedResult


class ClassMethodParser:
    """ClassMethod Developers IOフィードパーサー"""
    
    SOURCE_NAME = "classmethod"
    BASE_URL = "https://dev.classmethod.jp"
    
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
        feed_title = f.feed.get('title', 'ClassMethod Developers IO')
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            summary = entry.get('summary', '')
            
            # 著者情報
            author = entry.get('author', '')
            if not author and 'authors' in entry:
                # authorsフィールドから取得
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
            formatted_date = pub_time.strftime('%Y年%m月%d日')
            
            # タグの取得
            tags = []
            for tag in entry.get('tags', []):
                if isinstance(tag, dict) and 'term' in tag:
                    tags.append(tag['term'])
            
            # 画像URLの取得（OGP画像など）
            image_url = None
            
            # linksから画像を探す
            for link in entry.get('links', []):
                if link.get('type', '').startswith('image/'):
                    image_url = link.get('href')
                    break
            
            # contentから画像を抽出する場合もある
            if not image_url and 'content' in entry:
                content = entry.get('content', [])
                if content and isinstance(content, list):
                    # 簡易的な画像URL抽出（より詳細な実装が必要な場合は拡張）
                    import re
                    content_text = content[0].get('value', '')
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', content_text)
                    if img_match:
                        image_url = img_match.group(1)
            
            article = Article(
                title=title,
                url=article_url,
                published_date=formatted_date,
                source=ClassMethodParser.SOURCE_NAME,
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

def get_feed(tag: Optional[str] = None) -> FeedResult:
    """
    ClassMethod Developers IOのフィードを取得
    
    Args:
        tag: タグ名（Noneの場合は全体フィード）
             例: "aws", "python", "serverless", "machine-learning"
        
    Returns:
        FeedResult: フィード取得結果
        
    Examples:
        >>> result = get_feed()  # 全体フィード
        >>> result = get_feed("aws")  # AWSタグのフィード
        >>> result = get_feed("python")  # Pythonタグのフィード
    """
    if tag is None:
        url = f"{ClassMethodParser.BASE_URL}/feed/"
    else:
        url = f"{ClassMethodParser.BASE_URL}/tags/{tag}/feed/"
    
    return ClassMethodParser.parse_feed(url)


def get_feed_by_url(url: str) -> FeedResult:
    """
    カスタムURLからフィードを取得
    
    Args:
        url: フィードのURL
        
    Returns:
        FeedResult: フィード取得結果
    """
    return ClassMethodParser.parse_feed(url)


def get_author_feed(author_id: str) -> FeedResult:
    """
    特定著者のフィードを取得
    
    Args:
        author_id: 著者ID
        
    Returns:
        FeedResult: フィード取得結果
        
    Example:
        >>> result = get_author_feed("suzuki-shohei")
    """
    url = f"{ClassMethodParser.BASE_URL}/author/{author_id}/feed/"
    return ClassMethodParser.parse_feed(url)


# 人気のタグのプリセット
class PopularTags:
    """ClassMethodでよく使われるタグ"""
    AWS = "aws"
    PYTHON = "python"
    SERVERLESS = "serverless"
    MACHINE_LEARNING = "machine-learning"
    CONTAINER = "container"
    DEVOPS = "devops"
    SECURITY = "security"
    DATABASE = "database"
    ANALYTICS = "analytics"
    IOT = "iot"


if __name__ == "__main__":
    # 使用例1: 全体フィード
    print("=== ClassMethod 全体フィード ===")
    result = get_feed()
    print(f"フィードタイトル: {result.feed_title}")
    print(f"記事数: {result.total_count}")
    
    if result.articles:
        print(f"\n最新記事:")
        for article in result.articles[:3]:
            print(f"- {article.title}")
            print(f"  著者: {article.author}")
            print(f"  URL: {article.url}")
            print(f"  タグ: {', '.join(article.tags[:3]) if article.tags else 'なし'}")
    
    # 使用例2: AWSタグ
    print("\n=== AWS タグのフィード ===")
    aws_result = get_feed("aws")
    print(f"AWS記事数: {aws_result.total_count}")
    
    # 使用例3: 人気タグを使った取得
    print("\n=== 人気タグでの取得 ===")
    for tag_name in ["aws", "python", "serverless"]:
        result = get_feed(tag_name)
        print(f"{tag_name}: {result.total_count}件")
    
    # 使用例4: 辞書形式での出力
    print("\n=== 辞書形式での出力 ===")
    result_dict = result.to_dict()
    print(f"記事数: {result_dict['totalCount']}")
    if result_dict['articles']:
        print(f"最初の記事: {result_dict['articles'][0]['title']}")
