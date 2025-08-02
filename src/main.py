import feedparser
from datetime import datetime

def zen_feed_data_get(url):
    
    f = feedparser.parse(url)
    # データフレーム用のリストを作成
    articles_data = []

    for article in f['entries']:
        # 基本情報の取得
        title = article['title']
        summary = article['summary']
        url = article['link']
        # 時間をより扱いやすい形式で取得
        pub_time = datetime(*article['published_parsed'][:6])
        formatted_date = pub_time.strftime('%Y年%m月%d日')
        # リンクから特定のタイプのURLを取得（例：画像）
        image_url = None
        for link in article['links']:
            if link.get('type', '').startswith('image/'):
                image_url = link['href']
                break
        # リンクからOGP画像のURLだけを取得
        ogp_image_url = None
        for link in article['links']:
            if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
                ogp_image_url = link['href']
                break

            # 各記事の情報を辞書として追加
            article_dict = {
            "title": title,
            "summary" : summary[:150] + "..." if len(summary) > 150 else summary,
            "imageUrl" : str(image_url),
            "url" :  str(url),
            "publishedDate" : formatted_date
            }

        articles_data.append(article_dict)

    return articles_data

if __name__ == "__main__":
    ZENN_ALL_URL = "https://zenn.dev/feed"
    ZENN_DATAENGINEER_URL = "https://zenn.dev/topics/データエンジニア/feed"
    ZENN_GENAI_URL = "https://zenn.dev/topics/生成ai/feed"
    ZENN_MACHINELEARNING_URL = "https://zenn.dev/topics/機械学習/feed"
    ZENN_LLM_URL = "https://zenn.dev/topics/llm/feed"
    ZENN_AI_URL = "https://zenn.dev/topics/ai/feed"
    ZENN_DEEPLEARNING_URL = "https://zenn.dev/topics/deeplearning/feed"
    ZENN_NLP_URL = "https://zenn.dev/topics/nlp/feed"
    ZENN_PYTHON_URL = "https://zenn.dev/topics/python/feed"
    ZENN_GOOGLECLOUD_URL = "https://zenn.dev/topics/googlecloud/feed"
    ZENN_BIGQUERY_URL = "https://zenn.dev/topics/bigquery/feed"
    ZENN_CHURADATA_URL = "https://zenn.dev/p/churadata/feed"
    print(zen_feed_data_get(ZENN_DATAENGINEER_URL))