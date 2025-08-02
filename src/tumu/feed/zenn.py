"""Zenn用フィードパーサー"""
import feedparser
import warnings
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ZennArticle:
    """Zenn記事のデータクラス"""
    title: str
    summary: str
    url: str
    published_date: str
    image_url: Optional[str] = None
    ogp_image_url: Optional[str] = None
    
    @property
    def short_summary(self) -> str:
        """150文字に省略されたサマリー"""
        return self.summary[:150] + "..." if len(self.summary) > 150 else self.summary
    
    def to_dict(self) -> Dict[str, str]:
        """辞書形式に変換（後方互換性のため）"""
        return {
            "title": self.title,
            "summary": self.short_summary,
            "imageUrl": str(self.image_url) if self.image_url else "",
            "url": self.url,
            "publishedDate": self.published_date
        }


class ZennFeedParser:
    """Zennフィードパーサー"""
    
    @staticmethod
    def parse_feed(url: str) -> List[ZennArticle]:
        """
        フィードをパースしてZennArticleのリストを返す
        
        Args:
            url: フィードのURL
            
        Returns:
            List[ZennArticle]: パースされた記事のリスト
        """
        f = feedparser.parse(url)
        articles = []
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            summary = entry.get('summary', '')
            article_url = entry.get('link', '')
            
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
            ogp_image_url = None
            
            for link in entry.get('links', []):
                link_type = link.get('type', '')
                link_rel = link.get('rel', '')
                
                # 通常の画像URL
                if link_type.startswith('image/') and not image_url:
                    image_url = link.get('href')
                
                # OGP画像URL
                if link_rel == 'enclosure' and link_type.startswith('image/'):
                    ogp_image_url = link.get('href')
            
            article = ZennArticle(
                title=title,
                summary=summary,
                url=article_url,
                published_date=formatted_date,
                image_url=image_url,
                ogp_image_url=ogp_image_url
            )
            
            articles.append(article)
        
        return articles
    
    @staticmethod
    def parse_feed_as_dict(url: str) -> List[Dict[str, str]]:
        """
        フィードをパースして辞書のリストを返す（後方互換性）
        
        Args:
            url: フィードのURL
            
        Returns:
            List[Dict[str, str]]: パースされた記事の辞書リスト
        """
        articles = ZennFeedParser.parse_feed(url)
        return [article.to_dict() for article in articles]


# 便利な関数（高レベルAPI）

def get_feed(topic: Optional[str] = None, all_pages: bool = False) -> List[ZennArticle]:
    """
    Zennのフィードを取得
    
    Args:
        topic: トピック名（Noneの場合は全体フィード）
               例: "python", "機械学習", "llm", "データエンジニア"
        all_pages: Trueの場合、全ページを取得（?all=1を付与）
               ※全体フィードでは利用できません
        
    Returns:
        List[ZennArticle]: 記事のリスト
        
    Examples:
        >>> articles = get_feed()  # 全体フィード
        >>> articles = get_feed("python")  # Pythonトピック（最新のみ）
        >>> articles = get_feed("python", all_pages=True)  # Pythonトピック（全件）
    """
    if topic is None:
        url = "https://zenn.dev/feed"
        if all_pages:
            warnings.warn(
                "all_pages=True は全体フィードでは利用できません。"
                "トピックを指定してください。", 
                UserWarning
            )
    else:
        url = f"https://zenn.dev/topics/{topic}/feed"
        if all_pages:
            url += "?all=1"
    
    return ZennFeedParser.parse_feed(url)


def get_feed_by_url(url: str) -> List[ZennArticle]:
    """
    カスタムURLからフィードを取得
    
    Args:
        url: フィードのURL
        
    Returns:
        List[ZennArticle]: 記事のリスト
    """
    return ZennFeedParser.parse_feed(url)


def get_user_feed(username: str, all_pages: bool = False) -> List[ZennArticle]:
    """
    特定ユーザーのフィードを取得
    
    Args:
        username: Zennのユーザー名
        all_pages: Trueの場合、全ページを取得（?all=1を付与）
        
    Returns:
        List[ZennArticle]: 記事のリスト
        
    Examples:
        >>> articles = get_user_feed("churadata")  # 最新のみ
        >>> articles = get_user_feed("churadata", all_pages=True)  # 全件
    """
    url = f"https://zenn.dev/p/{username}/feed"
    
    if all_pages:
        url += "?all=1"
    
    return ZennFeedParser.parse_feed(url)


# 後方互換性のための関数
def zen_feed_data_get(url: str) -> List[Dict[str, str]]:
    """
    元の関数と同じインターフェース（後方互換性）
    
    Args:
        url: フィードのURL
        
    Returns:
        List[Dict[str, str]]: 記事の辞書リスト
    """
    return ZennFeedParser.parse_feed_as_dict(url)




if __name__ == "__main__":
    # 使用例1: 元のコードと同じ使い方
    print("=== 後方互換性の確認 ===")
    ZENN_DATAENGINEER_URL = "https://zenn.dev/topics/データエンジニア/feed"
    result = zen_feed_data_get(ZENN_DATAENGINEER_URL)
    print(f"データエンジニア記事数: {len(result)}")
    if result:
        print(f"最初の記事: {result[0]['title']}")
    
    # 使用例2: トピックを引数で指定
    print("\n=== トピックを引数で指定 ===")
    articles = get_feed("python")
    print(f"Python記事数: {len(articles)}")
    if articles:
        print(f"最初の記事: {articles[0].title}")
    
    # 使用例3: 日本語トピック
    print("\n=== 日本語トピック ===")
    ml_articles = get_feed("機械学習")
    print(f"機械学習記事数: {len(ml_articles)}")
    
    # 使用例4: 全体フィード（引数なし）
    print("\n=== 全体フィード ===")
    all_feed_articles = get_feed()
    print(f"全体記事数（最新）: {len(all_feed_articles)}")
    all_feed_articles_all = get_feed(all_pages=True)
    print(f"全体記事数（全件）: {len(all_feed_articles_all)}")
    
    # 使用例5: 特定ユーザー
    print("\n=== 特定ユーザーのフィード ===")
    user_articles = get_user_feed("churadata")
    print(f"churadataさんの記事数（最新）: {len(user_articles)}")
    user_articles_all = get_user_feed("churadata", all_pages=True)
    print(f"churadataさんの記事数（全件）: {len(user_articles_all)}")
    