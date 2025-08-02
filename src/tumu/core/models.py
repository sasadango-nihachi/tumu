"""共通データモデル"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Article:
    """記事の共通データクラス"""
    title: str
    url: str
    published_date: str
    source: str  # "zenn", "classmethod", etc.
    summary: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    
    @property
    def short_summary(self) -> str:
        """150文字に省略されたサマリー"""
        if not self.summary:
            return ""
        return self.summary[:150] + "..." if len(self.summary) > 150 else self.summary
    
    def to_dict(self) -> Dict[str, any]:
        """辞書形式に変換"""
        return {
            "title": self.title,
            "url": self.url,
            "publishedDate": self.published_date,
            "source": self.source,
            "summary": self.short_summary,
            "author": self.author or "",
            "tags": self.tags or [],
            "imageUrl": self.image_url or ""
        }


@dataclass
class FeedResult:
    """フィード取得結果"""
    articles: List[Article]
    feed_title: str
    feed_url: str
    fetched_at: datetime
    total_count: int = 0
    
    def __post_init__(self):
        """記事数を自動計算"""
        self.total_count = len(self.articles)
    
    def to_dict(self) -> Dict[str, any]:
        """辞書形式に変換"""
        return {
            "feedTitle": self.feed_title,
            "feedUrl": self.feed_url,
            "fetchedAt": self.fetched_at.isoformat(),
            "totalCount": self.total_count,
            "articles": [article.to_dict() for article in self.articles]
        }