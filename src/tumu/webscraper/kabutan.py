import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random 
from datetime import datetime


def scrape_kabutan_volume_ranking(url):
    """
    株探の出来高ランキングページからデータを取得し、CSVファイルに保存する関数
    
    Args:
        url (str): 株探の出来高ランキングページのURL
    
    Returns:
        pandas.DataFrame: 取得したデータのデータフレーム
    """
    # ヘッダーを設定（ブラウザとして認識させるため）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    }
    
    # ページを取得
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    
    # BeautifulSoupでHTMLを解析
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # テーブルを特定 - class="stock_table st_market"を持つテーブル
    table = soup.find('table', {'class': 'stock_table'})
    
    if not table:
        print("指定されたクラス名のテーブルが見つかりませんでした。")
        return None
    
    # データを格納するリスト
    data = []
    
    # データ行を取得
    rows = table.find('tbody').find_all('tr')
    
    for row in rows:
        try:
            # すべてのセルを取得
            cells = row.find_all(['td', 'th'])
            
            # 各行のデータを格納するリスト
            row_data = []
            
            # コード（最初のtd内のa要素のテキスト）
            code = cells[0].find('a').text.strip() if cells[0].find('a') else "N/A"
            row_data.append(code)
            
            # 銘柄名（最初のth要素のテキスト）
            name = cells[1].text.strip() if len(cells) > 1 else "N/A"
            row_data.append(name)
            
            # 市場（3番目のセル）
            market = cells[2].text.strip() if len(cells) > 2 else "N/A"
            row_data.append(market)
            
            # 株価（6番目のセル、インデックスは5）
            price = "N/A"
            for i, cell in enumerate(cells):
                if i >= 5 and cell.name == 'td' and not cell.find('a'):
                    price = cell.text.strip()
                    break
            row_data.append(price)
            
            # 残りのデータのインデックスを特定
            # 前日比と出来高のインデックスを特定するためのヘルパー関数
            def find_cell_index_by_content(cells, start_index, contains_text=None, class_name=None):
                for i in range(start_index, len(cells)):
                    if contains_text and contains_text in cells[i].text:
                        return i
                    if class_name and cells[i].get('class') and class_name in cells[i].get('class'):
                        return i
                return None
            
            # 前日比（値）- スパン要素を含むセルを探す
            change_value = "N/A"
            change_percent = "N/A"
            volume = "N/A"
            per = "N/A"
            pbr = "N/A"
            yield_value = "N/A"
            
            # 各セルを順番に調べて、データを抽出
            for i in range(5, len(cells)):
                cell_text = cells[i].text.strip()
                
                # 前日比（値）- up/downクラスを持つスパン要素を含むか、数値とプラス/マイナス記号のみ
                if 'up' in str(cells[i]) or 'down' in str(cells[i]) or cell_text.startswith('+') or cell_text.startswith('-') or cell_text == '0':
                    if change_value == "N/A":
                        change_value = cell_text
                    elif change_percent == "N/A" and '%' in cell_text:
                        change_percent = cell_text
                
                # 出来高 - カンマを含む大きな数値
                elif cell_text.replace(',', '').isdigit() and ',' in cell_text:
                    volume = cell_text.replace(',', '')
                
                # PER - 数値か「－」（ハイフン）のみ
                elif (cell_text.replace('.', '').isdigit() or cell_text == '－') and per == "N/A":
                    per = cell_text
                
                # PBR - 数値か「－」（ハイフン）のみ
                elif (cell_text.replace('.', '').isdigit() or cell_text == '－') and pbr == "N/A":
                    pbr = cell_text
                
                # 利回り - 数値か「－」（ハイフン）のみでPBRの後
                elif (cell_text.replace('.', '').isdigit() or cell_text == '－') and pbr != "N/A" and yield_value == "N/A":
                    yield_value = cell_text
            
            row_data.extend([change_value, change_percent, volume, per, pbr, yield_value])
            
            # 行データをリストに追加
            data.append(row_data)
        
        except Exception as e:
            print(f"行の処理中にエラーが発生しました: {e}")
            continue

    
    return data

def stock_volume_get():
    today = datetime.now().strftime('%Y%m%d')
    csv_filename = f'kabutan_volume_ranking_{today}.csv'

    stock_volumes = []
    for i in range(1,80):
        url = f"https://kabutan.jp/warning/volume_ranking?market=0&capitalization=-1&dispmode=normal&stc=&stm=0&page={i}"
        print(url)
        tmp_data = scrape_kabutan_volume_ranking(url)
        stock_volumes += tmp_data
        # 負荷をかけないように0.5から2.0秒のrandomでキックする
        time.sleep(float(f"{random.uniform(0.5, 2.0):.1f}"))
    column_names = ['コード', '銘柄名', '市場', '株価', '前日比(値)', '前日比(%)', '出来高', 'PER', 'PBR', '利回り']
    return pd.DataFrame(stock_volumes, columns=column_names)


if __name__ == "__main__":
    stock_volume_get()
