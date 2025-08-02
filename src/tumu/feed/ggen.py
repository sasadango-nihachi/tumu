"""G-GEN（ジージェン）ブログ用フィードパーサー"""
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


class GGenParser:
    """G-GENブログフィードパーサー"""
    
    SOURCE_NAME = "ggen"
    BASE_URL = "https://blog.g-gen.co.jp"
    FEED_URL = "https://blog.g-gen.co.jp/feed"
    
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
        feed_title = f.feed.get('title', 'G-GEN Tech Blog')
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            summary = entry.get('summary', '')
            
            # 著者情報（authorフィールドから取得）
            author = entry.get('author', '')
            
            # 日付のパース
            pub_time = datetime.now()
            if 'published_parsed' in entry and entry['published_parsed']:
                try:
                    pub_time = datetime(*entry['published_parsed'][:6])
                except:
                    pass
            formatted_date = pub_time.strftime('%Y年%m月%d日')
            
            # タグ/カテゴリの取得
            tags = []
            
            # カテゴリから取得
            for category in entry.get('tags', []):
                if isinstance(category, dict) and 'term' in category:
                    tags.append(category['term'])
            
            # 画像URLの取得
            image_url = None
            
            # contentから画像を抽出
            if 'content' in entry:
                content = entry.get('content', [])
                if content and isinstance(content, list):
                    import re
                    content_text = content[0].get('value', '')
                    # 最初の画像を取得
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', content_text)
                    if img_match:
                        image_url = img_match.group(1)
            
            # summaryからも画像を探す（contentがない場合）
            if not image_url and summary:
                import re
                img_match = re.search(r'<img[^>]+src="([^"]+)"', summary)
                if img_match:
                    image_url = img_match.group(1)
            
            article = Article(
                title=title,
                url=article_url,
                published_date=formatted_date,
                source=GGenParser.SOURCE_NAME,
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
    G-GENブログのフィードを取得
    
    Returns:
        FeedResult: フィード取得結果
        
    Example:
        >>> result = get_feed()
        >>> print(f"記事数: {result.total_count}")
    """
    return GGenParser.parse_feed(GGenParser.FEED_URL)


def get_feed_by_url(url: str) -> FeedResult:
    """
    カスタムURLからフィードを取得（将来の拡張用）
    
    Args:
        url: フィードのURL
        
    Returns:
        FeedResult: フィード取得結果
    """
    return GGenParser.parse_feed(url)


# よく見られるカテゴリ（参考）
class Categories:
    """G-GENブログでよく使われるカテゴリ"""
    GOOGLE_CLOUD = "Google Cloud"
    BIGQUERY = "BigQuery"
    GCP = "GCP"
    CLOUD_RUN = "Cloud Run"
    TERRAFORM = "Terraform"
    KUBERNETES = "Kubernetes"
    MACHINE_LEARNING = "Machine Learning"
    DATA_ENGINEERING = "Data Engineering"


if __name__ == "__main__":
    # 使用例
    print("=== G-GEN Tech Blog フィード ===")
    result = get_feed()
    print(f"フィードタイトル: {result.feed_title}")
    print(f"記事数: {result.total_count}")
    print(f"取得日時: {result.fetched_at}")
    
    if result.articles:
        print(f"\n最新記事:")
        for i, article in enumerate(result.articles[:5], 1):
            print(f"\n{i}. {article.title}")
            print(f"   著者: {article.author}")
            print(f"   URL: {article.url}")
            print(f"   日付: {article.published_date}")
            if article.tags:
                print(f"   タグ: {', '.join(article.tags[:3])}")
            print(f"   要約: {article.short_summary}")
    
    # 辞書形式での出力テスト
    print("\n=== 辞書形式での出力 ===")
    result_dict = result.to_dict()
    print(f"フィード情報:")
    print(f"- タイトル: {result_dict['feedTitle']}")
    print(f"- URL: {result_dict['feedUrl']}")
    print(f"- 記事数: {result_dict['totalCount']}")
    
    # 統一されたインターフェースの確認
    print("\n=== 他のパーサーとの互換性確認 ===")
    articles = result.articles
    if articles:
        # すべて同じArticleクラス
        article = articles[0]
        print(f"ソース識別: {article.source}")  # "ggen"
        print(f"共通フィールド: title={article.title}, url={article.url}")