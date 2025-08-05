"""フィードパーサーモジュール"""
from tumu.feed import zenn, classmethod, ggen, qiita, googlecloud, aws, huggingface,deepmind, openai

__all__ = ["zenn", "classmethod", "ggen", "qiita", "googlecloud","aws","huggingface","deepmind","openai"]
# これらが公開APIであるという宣言

# ここがあると下記のように簡潔になる、忘れがちなのでメモしておく
# 長いインポートが必要
# from tumu.feed.zenn import get_feed as get_zenn_feed
# from tumu.feed.qiita import get_feed as get_qiita_feed
# from tumu.feed.googlecloud import get_feed as get_gc_fee
# 
# シンプルにモジュールをインポートできる
# from tumu.feed import zenn, qiita, googlecloud

# # 使用
# zenn.get_feed("python")
# qiita.get_feed("python")
# googlecloud.get_feed()