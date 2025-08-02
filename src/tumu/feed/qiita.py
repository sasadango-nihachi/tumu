"""Qiita用フィードパーサー"""
import feedparser
from datetime import datetime
from typing import List, Optional

# 共通モデルをインポート
try:
    from ..core.models import Article, FeedResult
except ImportError:
    # 直接実行時用
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import Article, FeedResult


class QiitaParser:
    """Qiitaフィードパーサー"""
    
    SOURCE_NAME = "qiita"
    BASE_URL = "https://qiita.com"
    
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
        feed_title = f.feed.get('title', 'Qiita')
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            
            # Atomフィードの場合、summaryがない場合はcontentから取得
            summary = entry.get('summary', '')
            if not summary and 'content' in entry:
                content = entry.get('content', [])
                if content and isinstance(content, list):
                    summary = content[0].get('value', '')
            
            # 著者情報
            author = ''
            if 'author' in entry:
                author = entry.get('author', '')
            elif 'author_detail' in entry:
                author = entry.author_detail.get('name', '')
            elif 'authors' in entry and entry['authors']:
                author = entry['authors'][0].get('name', '')
            
            # 日付のパース（Atomフィードはupdatedを使用）
            pub_time = datetime.now()
            date_field = None
            
            # published_parsed -> updated_parsed の順で試す
            if 'published_parsed' in entry and entry['published_parsed']:
                date_field = entry['published_parsed']
            elif 'updated_parsed' in entry and entry['updated_parsed']:
                date_field = entry['updated_parsed']
            
            if date_field:
                try:
                    pub_time = datetime(*date_field[:6])
                except:
                    pass
            
            formatted_date = pub_time.strftime('%Y年%m月%d日')
            
            # タグの取得
            tags = []
            for tag in entry.get('tags', []):
                if isinstance(tag, dict) and 'term' in tag:
                    tags.append(tag['term'])
            
            # カテゴリからもタグを取得（Qiitaの場合）
            for category in entry.get('categories', []):
                if isinstance(category, str):
                    tags.append(category)
                elif isinstance(category, dict) and 'term' in category:
                    tags.append(category['term'])
            
            # 画像URLの取得
            image_url = None
            
            # リンクから画像を探す
            for link in entry.get('links', []):
                if link.get('type', '').startswith('image/'):
                    image_url = link.get('href')
                    break
            
            # contentまたはsummaryから最初の画像を抽出
            if not image_url:
                import re
                content_text = summary
                if content_text:
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', content_text)
                    if img_match:
                        image_url = img_match.group(1)
            
            article = Article(
                title=title,
                url=article_url,
                published_date=formatted_date,
                source=QiitaParser.SOURCE_NAME,
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
    Qiitaのフィードを取得
    
    Args:
        tag: タグ名（Noneの場合は人気の投稿）
             例: "python", "rails", "docker", "aws"
        
    Returns:
        FeedResult: フィード取得結果
        
    Examples:
        >>> result = get_feed()  # 人気の投稿
        >>> result = get_feed("python")  # Pythonタグ
        >>> result = get_feed("機械学習")  # 日本語タグもOK
    """
    if tag is None:
        # 人気の投稿（Atomフィード）
        url = f"{QiitaParser.BASE_URL}/popular-items/feed.atom"
    else:
        # 特定タグのフィード
        url = f"{QiitaParser.BASE_URL}/tags/{tag}/feed"
    
    return QiitaParser.parse_feed(url)


def get_user_feed(username: str) -> FeedResult:
    """
    特定ユーザーのフィードを取得
    
    Args:
        username: Qiitaのユーザー名
        
    Returns:
        FeedResult: フィード取得結果
        
    Example:
        >>> result = get_user_feed("username")
    """
    url = f"{QiitaParser.BASE_URL}/users/{username}/feed.atom"
    return QiitaParser.parse_feed(url)


def get_organization_feed(org_id: str) -> FeedResult:
    """
    特定組織のフィードを取得
    
    Args:
        org_id: 組織ID
        
    Returns:
        FeedResult: フィード取得結果
        
    Example:
        >>> result = get_organization_feed("qiita-inc")
    """
    url = f"{QiitaParser.BASE_URL}/organizations/{org_id}/activities.atom"
    return QiitaParser.parse_feed(url)


def get_advent_calendar_feed(year: int, calendar_id: str) -> FeedResult:
    """
    アドベントカレンダーのフィードを取得
    
    Args:
        year: 年（例: 2023）
        calendar_id: カレンダーID
        
    Returns:
        FeedResult: フィード取得結果
        
    Example:
        >>> result = get_advent_calendar_feed(2023, "python")
    """
    url = f"{QiitaParser.BASE_URL}/advent-calendar/{year}/feeds/{calendar_id}.atom"
    return QiitaParser.parse_feed(url)


# よく使われるタグ
class PopularTags:
    """Qiitaでよく使われるタグ"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    RUBY = "ruby"
    GO = "go"
    TYPESCRIPT = "typescript"
    RAILS = "rails"
    REACT = "react"
    VUE = "vue"
    AWS = "aws"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    GIT = "git"
    LINUX = "linux"
    MACHINE_LEARNING = "機械学習"
    DEEP_LEARNING = "deeplearning"
    NEXTJS = "nextjs"


if __name__ == "__main__":
    # 使用例1: 人気の投稿
    print("=== Qiita 人気の投稿 ===")
    result = get_feed()
    print(f"フィードタイトル: {result.feed_title}")
    print(f"記事数: {result.total_count}")
    
    if result.articles:
        print(f"\n人気記事:")
        for i, article in enumerate(result.articles[:5], 1):
            print(f"\n{i}. {article.title}")
            print(f"   著者: {article.author}")
            print(f"   URL: {article.url}")
            print(f"   日付: {article.published_date}")
            if article.tags:
                print(f"   タグ: {', '.join(article.tags[:5])}")
    
    # 使用例2: 特定タグ
    print("\n\n=== Python タグの投稿 ===")
    python_result = get_feed("python")
    print(f"Python記事数: {python_result.total_count}")
    
    # 使用例3: 様々なタグでの記事数比較
    print("\n=== タグ別記事数 ===")
    tags = ["python", "javascript", "rails", "docker", "aws"]
    for tag in tags:
        result = get_feed(tag)
        print(f"{tag}: {result.total_count}件")
    
    # 使用例4: 統一されたインターフェースの確認
    print("\n=== 他のサービスとの互換性 ===")
    # Qiitaの記事
    qiita_articles = get_feed("python").articles
    if qiita_articles:
        article = qiita_articles[0]
        print(f"Qiita記事:")
        print(f"- ソース: {article.source}")  # "qiita"
        print(f"- タイトル: {article.title}")
        print(f"- 著者: {article.author}")
        print(f"- タグ: {', '.join(article.tags[:3]) if article.tags else 'なし'}")