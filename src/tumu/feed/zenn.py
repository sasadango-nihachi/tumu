"""Zenn用フィードパーサー（共通モデル版）"""
import feedparser
from datetime import datetime
from typing import List, Optional
try:
    from ..core.models import Article, FeedResult
except ImportError:
    # 直接実行時用
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from core.models import Article, FeedResult



class ZennParser:
    """Zennフィードパーサー"""
    
    SOURCE_NAME = "zenn"
    BASE_URL = "https://zenn.dev"
    
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
        feed_title = f.feed.get('title', 'Zenn')
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            summary = entry.get('summary', '')
            
            # 日付のパース
            pub_time = datetime.now()
            if 'published_parsed' in entry and entry['published_parsed']:
                try:
                    pub_time = datetime(*entry['published_parsed'][:6])
                except:
                    pass
            formatted_date = pub_time.strftime('%Y年%m月%d日')
            
            # 画像URLの取得
            image_url = None
            for link in entry.get('links', []):
                link_type = link.get('type', '')
                if link_type.startswith('image/'):
                    image_url = link.get('href')
                    break
            
            # Zennの場合、著者やタグ情報は基本的にフィードに含まれない
            article = Article(
                title=title,
                url=article_url,
                published_date=formatted_date,
                source=ZennParser.SOURCE_NAME,
                summary=summary,
                author=None,  # Zennのフィードには著者情報がない
                tags=None,    # Zennのフィードにはタグ情報がない
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

def get_feed(topic: Optional[str] = None, all_pages: bool = False) -> FeedResult:
    """
    Zennのフィードを取得
    
    Args:
        topic: トピック名（Noneの場合は全体フィード）
               例: "python", "機械学習", "llm", "データエンジニア"
        all_pages: Trueの場合、全ページを取得（?all=1を付与）
               ※全体フィードでは利用できません
        
    Returns:
        FeedResult: フィード取得結果
        
    Examples:
        >>> result = get_feed()  # 全体フィード
        >>> result = get_feed("python")  # Pythonトピック
        >>> result = get_feed("python", all_pages=True)  # Pythonトピック全件
    """
    if topic is None:
        url = f"{ZennParser.BASE_URL}/feed"
        # 全体フィードではall_pagesは無効
    else:
        url = f"{ZennParser.BASE_URL}/topics/{topic}/feed"
        if all_pages:
            url += "?all=1"
    
    return ZennParser.parse_feed(url)


def get_user_feed(username: str, all_pages: bool = False) -> FeedResult:
    """
    特定ユーザーのフィードを取得
    
    Args:
        username: Zennのユーザー名
        all_pages: Trueの場合、全ページを取得（?all=1を付与）
        
    Returns:
        FeedResult: フィード取得結果
        
    Examples:
        >>> result = get_user_feed("churadata")  # 最新のみ
        >>> result = get_user_feed("churadata", all_pages=True)  # 全件
    """
    url = f"{ZennParser.BASE_URL}/p/{username}/feed"
    
    if all_pages:
        url += "?all=1"
    
    return ZennParser.parse_feed(url)


# 後方互換性のための関数とクラス

def zen_feed_data_get(url: str) -> List[dict]:
    """
    元の関数と同じインターフェース（後方互換性）
    
    Args:
        url: フィードのURL
        
    Returns:
        List[dict]: 記事の辞書リスト
    """
    result = ZennParser.parse_feed(url)
    return [article.to_dict() for article in result.articles]


# よく使うトピック
class PopularTopics:
    """Zennでよく使われるトピック"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    AWS = "aws"
    GCP = "googlecloud"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    REACT = "react"
    VUE = "vue"
    NEXTJS = "nextjs"
    AI = "ai"
    MACHINE_LEARNING = "機械学習"
    DATA_ENGINEER = "データエンジニア"


if __name__ == "__main__":
    # 使用例1: 統一されたインターフェース
    print("=== 統一されたインターフェースでの使用 ===")
    
    # Zennの場合
    zenn_result = get_feed("python")
    print(f"Zenn Python記事数: {zenn_result.total_count}")
    
    # 記事の詳細（共通フォーマット）
    if zenn_result.articles:
        article = zenn_result.articles[0]
        print(f"\n記事情報:")
        print(f"- タイトル: {article.title}")
        print(f"- URL: {article.url}")
        print(f"- ソース: {article.source}")
        print(f"- 日付: {article.published_date}")
        print(f"- 要約: {article.short_summary}")
    
    # 辞書形式での取得
    result_dict = zenn_result.to_dict()
    print(f"\n辞書形式: {result_dict['feedTitle']}, {result_dict['totalCount']}件")