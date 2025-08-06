from dotenv import load_dotenv
from pathlib import Path
import requests
import pandas as pd
import zipfile
import os
import time
import glob

# .envファイルを読み込み
load_dotenv()

# TODO どのくらいの返却が必要か悩ましい、どの程度扱える状態がいいか精査が必要

def search_by_security_code(api_key: str, security_code: str, date: str) -> pd.DataFrame:
    """
    証券コードと日付で有価証券報告書を検索
    
    Args:
        api_key (str): EDINET APIキー
        security_code (str): 証券コード（4桁）
        date (str): 検索日付 (YYYY-MM-DD形式)
        
    Returns:
        pd.DataFrame: 検索結果
    """
    url = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
    params = {
        'date': date,
        'type': 2,
        'Subscription-Key': api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['results'])

        if df.empty:
            print(f"{date}の書類は見つかりませんでした")
            return pd.DataFrame()
        
        # 証券コードで絞り込み
        filtered_df = df[df['secCode'] == f"{security_code}0"]
        # 有価証券報告書のみにする場合、docDescriptionに入ってる
  
        
        return filtered_df[['docID','secCode','filerName','submitDateTime','docDescription']]
        
    except requests.RequestException as e:
        print(f"検索エラー: {e}")
        return pd.DataFrame()
    

def download_csv_report(api_key: str, doc_id: str,  save_dir: str = "./edinet_data") -> str:
    """
    書類管理番号でCSV形式の財務諸表をダウンロード
    
    Args:
        api_key (str): EDINET APIキー
        doc_id (str): 書類管理番号
        save_dir (str): 保存先ディレクトリ
        
    Returns:
        str: 解凍先ディレクトリパス（成功時）、None（失敗時）
    """
    url = f"https://api.edinet-fsa.go.jp/api/v2/documents/{doc_id}"
    params = {
        'type': 5,  # CSV形式
        'Subscription-Key': api_key
    }
    
    os.makedirs(save_dir, exist_ok=True)
    zip_path = os.path.join(save_dir, f"{doc_id}.zip")
    
    try:
        print(f"ダウンロード中: {doc_id}")
        response = requests.get(url, params=params, stream=True)
        response.raise_for_status()
        
        # ZIPファイル保存
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 解凍
        extract_dir = os.path.join(save_dir, doc_id)
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"ダウンロード完了: {extract_dir}")
        return extract_dir
        
    except requests.RequestException as e:
        print(f"ダウンロードエラー: {e}")
        return None


def download_pdf_report(api_key: str, doc_id: str, save_dir: str = None) -> str:
    """
    書類管理番号でPDF形式の財務諸表をダウンロード
    
    Args:
        api_key (str): EDINET APIキー
        doc_id (str): 書類管理番号
        save_dir (str): 保存先ディレクトリ
        
    Returns:
        str: PDFファイルパス（成功時）、None（失敗時）
    """
    if save_dir is None:
        home_dir = os.environ.get('HOME')
        if home_dir:
            save_dir = os.path.join(home_dir, 'Downloads')
        else:
            save_dir = os.path.join(os.getcwd(), 'Downloads') # HOMEが見つからなかった場合のフォールバック、現在のディレクトリ配下にして

    url = f"https://api.edinet-fsa.go.jp/api/v2/documents/{doc_id}"
    params = {
        'type': 2,  # PDF形式
        'Subscription-Key': api_key
    }
    
    os.makedirs(save_dir, exist_ok=True)
    pdf_path = os.path.join(save_dir, f"{doc_id}.pdf")
    
    try:
        print(f"PDFダウンロード中: {doc_id}")
        response = requests.get(url, params=params, stream=True)
        response.raise_for_status()
        
        # PDFファイル保存
        with open(pdf_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"PDFダウンロード完了: {pdf_path}")
        return pdf_path
        
    except requests.RequestException as e:
        print(f"PDFダウンロードエラー: {e}")
        return None
    
if __name__ == "__main__":
    API_KEY = os.getenv('EDINET_API')
    result = search_by_security_code(API_KEY,'4499','2024-12-23')
    print(result)
    # download_pdf_report(API_KEY, 'S100UZY2')