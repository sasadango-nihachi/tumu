import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_anthropic_news_urls():
    """
    AnthropicのニュースページからURL一覧を取得
    返り値: URLのリスト
    """
    base_url = "https://www.anthropic.com"
    news_url = "https://www.anthropic.com/news"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(news_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ニュースリンクを全て取得
        urls = []
        news_links = soup.find_all('a', href=lambda x: x and '/news/' in x)
        
        for link in news_links:
            href = link.get('href')
            full_url = urljoin(base_url, href)
            
            # /newsで終わるURLは除外（一覧ページ自体）
            if not full_url.endswith('/news'):
                urls.append(full_url)
        
        # 重複を削除
        unique_urls = list(set(urls))
        
        return unique_urls
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []


def get_anthropic_news_urls_selenium():
    """
    Seleniumで動的コンテンツを含む全URLを取得
    返り値: URLのリスト
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
    except ImportError:
        print("Seleniumがインストールされていません。")
        print("pip install selenium")
        return []
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.anthropic.com/news")
        
        # 初期読み込み待機
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/news/']"))
        )
        
        # スクロールして全コンテンツを読み込む
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # 下までスクロール
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # 新しい高さを取得
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # JavaScriptでURL一覧を取得
        urls = driver.execute_script("""
            const urls = new Set();
            const links = document.querySelectorAll('a[href*="/news/"]');
            
            links.forEach(link => {
                const href = link.href;
                if (!href.endsWith('/news')) {
                    urls.add(href);
                }
            });
            
            return Array.from(urls);
        """)
        
        return urls
        
    except Exception as e:
        print(f"Seleniumでエラーが発生しました: {e}")
        return []
        
    finally:
        driver.quit()


def get_article_details(url):
    """
    個別の記事ページからタイトルと日付を取得
    返り値: {'url': str, 'title': str, 'date': str}
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # タイトルを取得（h1 class="h2"）
        title_elem = soup.find('h1', class_='h2')
        title = title_elem.get_text(strip=True) if title_elem else "タイトル不明"
        
        # 日付を取得（div class="PostDetail_post-timestamp__TBJ0Z text-label"）
        date_elem = soup.find('div', class_=lambda x: x and 'post-timestamp' in x)
        if date_elem:
            # 日付部分だけを抽出（●の前まで）
            date_text = date_elem.get_text(strip=True)
            date = date_text.split('●')[0].strip() if '●' in date_text else date_text.split('•')[0].strip()
        else:
            date = "日付不明"
        
        return {
            'url': url,
            'title': title,
            'date': date
        }
        
    except Exception as e:
        print(f"エラー ({url}): {e}")
        return {
            'url': url,
            'title': "取得エラー",
            'date': "取得エラー"
        }


def get_all_article_details(urls, max_articles=None):
    """
    URL一覧から全記事の詳細を取得
    
    Args:
        urls: URLのリスト
        max_articles: 取得する最大記事数（Noneで全て）
    
    返り値: [{'url': str, 'title': str, 'date': str}, ...]
    """
    import time
    
    articles = []
    urls_to_process = urls[:max_articles] if max_articles else urls
    
    print(f"\n{len(urls_to_process)}件の記事詳細を取得中...")
    
    for i, url in enumerate(urls_to_process, 1):
        print(f"{i}/{len(urls_to_process)}: {url}")
        article = get_article_details(url)
        articles.append(article)
        
        # サーバーに負荷をかけないよう待機
        if i < len(urls_to_process):
            time.sleep(0.2)
    
    return articles

def get_urls():
    """
    URL一覧から全記事の詳細を取得
    
    返り値: [{'url': str, 'title': str, 'date': str}, ...]
    """
    urls = get_anthropic_news_urls()
    return get_all_article_details(urls)

# メイン実行部分
if __name__ == "__main__":
    print("=== AnthropicニュースURL取得 ===\n")
    
    # Basic版
    print("1. URL一覧を取得中...")
    urls = get_anthropic_news_urls()
    
    if urls:
        print(f"\n取得したURL数: {len(urls)}")
        
        # 各記事の詳細を取得
        print("\n2. 各記事の詳細を取得中...")
        # 最初の5件だけ取得（全て取得する場合はmax_articlesを削除）
        articles = get_all_article_details(urls)
        
        print("\n=== 取得した記事一覧 ===")
        for i, article in enumerate(articles, 1):
            print(f"\n記事{i}:")
            print(f"  タイトル: {article['title']}")
            print(f"  日付: {article['date']}")
            print(f"  URL: {article['url']}")
        
        # 全記事を取得したい場合
        print(f"\n\n※ 現在は最初の5件のみ取得しています。")
        print(f"全{len(urls)}件を取得する場合は、以下を実行してください：")
        print("articles = get_all_article_details(urls)")
        
    else:
        print("URLを取得できませんでした。")