"""Google AI Blog用フィードパーサー"""
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


class GoogleAIParser:
    """Google AI Blogフィードパーサー"""
    
    SOURCE_NAME = "googleai"
    FEED_URL = "https://feeds.feedburner.com/blogspot/gJZg"
    
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
        feed_title = f.feed.get('title', 'Google AI Blog')
        
        for entry in f.entries:
            # 基本情報の取得
            title = entry.get('title', '')
            article_url = entry.get('link', '')
            
            # Feedburnerの場合、元のURLを取得
            if 'feedburner_origlink' in entry:
                article_url = entry.get('feedburner_origlink', article_url)
            
            # summaryまたはdescriptionを使用
            summary = entry.get('summary', '') or entry.get('description', '')
            
            # contentから詳細な内容を取得（利用可能な場合）
            if 'content' in entry and entry['content']:
                content_value = entry['content'][0].get('value', '')
                if content_value and len(content_value) > len(summary):
                    summary = content_value
            
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
            
            # タグ/カテゴリの取得
            tags = []
            
            # tagsフィールド
            for tag in entry.get('tags', []):
                if isinstance(tag, dict) and 'term' in tag:
                    tags.append(tag['term'])
            
            # categoriesフィールド（Google AI Blogは研究分野をカテゴリとして使用）
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
                    # 最大サイズの画像を選択
                    thumbnail = max(thumbnails, key=lambda x: int(x.get('width', 0)) * int(x.get('height', 0)))
                    image_url = thumbnail.get('url')
            
            # enclosureから画像を探す
            if not image_url:
                for enclosure in entry.get('enclosures', []):
                    if enclosure.get('type', '').startswith('image/'):
                        image_url = enclosure.get('href')
                        break
            
            # contentから画像を抽出
            if not image_url and summary:
                import re
                # Bloggerの画像URLパターンにマッチ
                img_patterns = [
                    r'<img[^>]+src="([^"]+)"',
                    r'src="(https://[^"]+\.(?:jpg|jpeg|png|gif|webp))"'
                ]
                for pattern in img_patterns:
                    img_match = re.search(pattern, summary, re.IGNORECASE)
                    if img_match:
                        image_url = img_match.group(1)
                        break
            
            article = Article(
                title=title,
                url=article_url,
                published_date=formatted_date,
                source=GoogleAIParser.SOURCE_NAME,
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
    Google AI Blogのフィードを取得
    
    Returns:
        FeedResult: フィード取得結果
        
    Example:
        >>> result = get_feed()
        >>> print(f"記事数: {result.total_count}")
    """
    return GoogleAIParser.parse_feed(GoogleAIParser.FEED_URL)


def get_feed_by_url(url: str) -> FeedResult:
    """
    カスタムURLからフィードを取得（将来の拡張用）
    
    Args:
        url: フィードのURL
        
    Returns:
        FeedResult: フィード取得結果
    """
    return GoogleAIParser.parse_feed(url)


# Google AIの研究分野（参考）
class ResearchAreas:
    """Google AIの主な研究分野"""
    MACHINE_LEARNING = "Machine Learning"
    NATURAL_LANGUAGE = "Natural Language Processing"
    COMPUTER_VISION = "Computer Vision"
    ROBOTICS = "Robotics"
    QUANTUM_AI = "Quantum AI"
    HEALTHCARE = "Healthcare"
    CLIMATE = "Climate and Sustainability"
    RESPONSIBLE_AI = "Responsible AI"
    TENSORFLOW = "TensorFlow"
    BERT = "BERT"
    GEMINI = "Gemini"
    PALM = "PaLM"
    LAMDA = "LaMDA"
    BARD = "Bard"


if __name__ == "__main__":
    # 使用例
    print("=== Google AI Blog ===")
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
            if article.author:
                print(f"   著者: {article.author}")
            if article.tags:
                print(f"   カテゴリ: {', '.join(article.tags[:3])}")
            print(f"   要約: {article.short_summary}")
    
    # 研究分野別の記事数（例）
    print("\n\n=== 研究分野別の分析 ===")
    ml_articles = [a for a in result.articles if any('machine learning' in tag.lower() for tag in a.tags)]
    nlp_articles = [a for a in result.articles if any('language' in tag.lower() for tag in a.tags)]
    cv_articles = [a for a in result.articles if any('vision' in tag.lower() for tag in a.tags)]
    
    print(f"機械学習関連: {len(ml_articles)}件")
    print(f"自然言語処理関連: {len(nlp_articles)}件")
    print(f"コンピュータビジョン関連: {len(cv_articles)}件")