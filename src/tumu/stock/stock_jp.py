import pandas_datareader as  web
import pandas as pd 
from  datetime  import datetime,date,timedelta
import yfinance as yf
import requests
from io import BytesIO

def jpx_stock_list_get():
    """
    JPXから日本株一覧データを取得する関数
    
    JPXのWebサイトからdata_j.xlsファイルをダウンロードし、
    プライム・スタンダード・グロース市場の日本株データを抽出・整形して返す
    
    Returns:
        pd.DataFrame: 日本株一覧データ
            - date: 日付
            - stock_code: 銘柄コード
            - stock_name: 銘柄名
            - industry_code_33: 33業種コード
            - industry_type_33: 33業種区分
            - industry_code_17: 17業種コード
            - industry_type_17: 17業種区分
            - market_type: 市場・商品区分
            
    Raises:
        requests.exceptions.RequestException: ダウンロードに失敗した場合
        pd.errors.ExcelFileError: エクセルファイルの読み込みに失敗した場合
    """
    # JPXのエクセルファイルのURL
    url = 'https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls'
    
    # エクセルファイルをHTTP GETリクエストでダウンロード
    response = requests.get(url)
    response.raise_for_status()  # HTTPエラーチェック（4xx, 5xxエラーで例外発生）
    
    # ダウンロードしたバイナリデータをBytesIOオブジェクトに変換
    # （pandasがファイルパスではなくストリームから読み込めるようにする）
    data = BytesIO(response.content)
    
    # エクセルファイルをpandasのDataFrameに読み込み
    df = pd.read_excel(data)
    
    # 必要なカラムのみを抽出
    columns = ['日付','コード', '銘柄名','33業種コード' ,'33業種区分','17業種コード', '17業種区分', '市場・商品区分']
    df_filtered = df[columns]
    
    # カラム名を英語に変更（データベースやAPIでの取り扱いを容易にするため）
    df_filtered = df_filtered.rename(columns={
        '日付': 'date',
        'コード': 'stock_code',
        '銘柄名': 'stock_name',
        '33業種コード': 'industry_code_33',
        '33業種区分': 'industry_type_33',
        '17業種コード': 'industry_code_17',
        '17業種区分': 'industry_type_17',
        '市場・商品区分': 'market_type'
    })
    
    # 東証の主要3市場（プライム・スタンダード・グロース）の内国株式のみをフィルタリング
    return df_filtered[df_filtered['market_type'].isin(['プライム（内国株式）','スタンダード（内国株式）','グロース（内国株式）'])]


def stooq_jp_data_get(stock_code, date_s, date_e):
    """
    Stooq APIを使用して日本株の株価データを取得する関数
    
    Args:
        stock_code (str): 銘柄コード（例：'7203'）
        date_s (datetime): 取得開始日
        date_e (datetime): 取得終了日
        
    Returns:
        pd.DataFrame: 株価データ（日付昇順でソート済み）
            - Date: 日付
            - Open: 始値
            - High: 高値
            - Low: 安値
            - Close: 終値
            - Volume: 出来高
            
    Note:
        - Stooqでは日本株のシンボルは'{stock_code}.JP'形式
        - データが存在しない場合は、列を持つ空のDataFrameを返す
    """
    # デフォルトのカラム定義
    default_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    try:
        # Stooq APIから株価データを取得
        stooq_reader = web.stooq.StooqDailyReader(f'{stock_code}.JP', start=date_s, end=date_e)
        stooq = stooq_reader.read()
        
        # データが空かチェック
        if stooq.empty:
            # 空のDataFrameを作成（列定義付き）
            return pd.DataFrame(columns=default_columns)
        
        # インデックスをリセット（DateがインデックスになっているはずなのでDateカラムに変換）
        stooq = stooq.reset_index()
        
        # カラム名の正規化（大文字小文字の違いを吸収）
        column_mapping = {}
        for col in stooq.columns:
            col_lower = col.lower()
            if col_lower == 'date':
                column_mapping[col] = 'Date'
            elif col_lower == 'open':
                column_mapping[col] = 'Open'
            elif col_lower == 'high':
                column_mapping[col] = 'High'
            elif col_lower == 'low':
                column_mapping[col] = 'Low'
            elif col_lower == 'close':
                column_mapping[col] = 'Close'
            elif col_lower == 'volume':
                column_mapping[col] = 'Volume'
        
        # カラム名を変更
        stooq = stooq.rename(columns=column_mapping)
        
        # 必要なカラムのみ選択（存在するものだけ）
        available_columns = [col for col in default_columns if col in stooq.columns]
        
        if not available_columns:
            # 期待されるカラムが一つもない場合
            return pd.DataFrame(columns=default_columns)
        
        # 必要なカラムを選択
        stooq = stooq[available_columns].copy()
        
        # 不足しているカラムをNaNで追加
        for col in default_columns:
            if col not in stooq.columns:
                stooq[col] = pd.NA
        
        # カラムの順序を整える
        stooq = stooq[default_columns]
        
        # 価格カラムをfloat型に変換
        price_columns = ['Open', 'High', 'Low', 'Close']
        for col in price_columns:
            if col in stooq.columns:
                stooq[col] = pd.to_numeric(stooq[col], errors='coerce')
        
        # Volumeを整数型に変換
        if 'Volume' in stooq.columns:
            stooq['Volume'] = pd.to_numeric(stooq['Volume'], errors='coerce').fillna(0).astype('int64')
        
        # 日付順（昇順）でソート
        if 'Date' in stooq.columns and not stooq.empty:
            stooq = stooq.sort_values(by='Date').reset_index(drop=True)
        
        return stooq
        
    except Exception as e:
        # エラーが発生した場合も空のDataFrameを返す
        print(f"データ取得エラー: {e}")
        print(f"銘柄コード: {stock_code}.JP, 期間: {date_s} - {date_e}")
        return pd.DataFrame(columns=default_columns)


def stooq_jp_data_get_safe(stock_code, date_s, date_e):
    """
    より安全なバージョン（エラーハンドリング強化版）
    """
    # デフォルトのDataFrame構造
    empty_df = pd.DataFrame({
        'Date': pd.DatetimeIndex([]),
        'Open': pd.Series(dtype='float64'),
        'High': pd.Series(dtype='float64'),
        'Low': pd.Series(dtype='float64'),
        'Close': pd.Series(dtype='float64'),
        'Volume': pd.Series(dtype='int64')
    })
    
    try:
        df = stooq_jp_data_get(stock_code, date_s, date_e)
        
        # データが取得できているかチェック
        if df.empty:
            print(f"警告: {stock_code}.JP のデータが見つかりません（期間: {date_s} - {date_e}）")
            return empty_df
            
        return df
        
    except Exception as e:
        print(f"エラー: {stock_code}.JP のデータ取得に失敗しました: {e}")
        return empty_df


def yfinance_jp_data_get(stock_code, date_s, date_e):
    """
    Yahoo Finance APIを使用して日本株の株価データを取得する関数
    
    Args:
        stock_code (str): 銘柄コード（例：'7203'）
        date_s (str): 取得開始日（'YYYY-MM-DD' 形式）
        date_e (str): 取得終了日（'YYYY-MM-DD' 形式）
        
    Returns:
        pd.DataFrame: 株価データ（日付昇順でソート済み）
            - Date: 日付
            - Open: 始値
            - High: 高値
            - Low: 安値
            - Close: 終値
            - Volume: 出来高
            
    Note:
        - Yahoo Financeでは日本株のシンボルは'{stock_code}.T'形式
        - データが存在しない場合は、列を持つ空のDataFrameを返す
        - 日付は'YYYY-MM-DD'形式の文字列で指定
    """
    # デフォルトのカラム定義
    default_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    
    # 空のDataFrameのテンプレート
    empty_df = pd.DataFrame({
        'Date': pd.Series(dtype='datetime64[ns]'),
        'Open': pd.Series(dtype='float64'),
        'High': pd.Series(dtype='float64'),
        'Low': pd.Series(dtype='float64'),
        'Close': pd.Series(dtype='float64'),
        'Volume': pd.Series(dtype='int64')
    })
    
    try:
        # 文字列の日付をdatetimeに変換（バリデーション）
        start_date = datetime.strptime(date_s, '%Y-%m-%d')
        end_date = datetime.strptime(date_e, '%Y-%m-%d')
        
        # 終了日に+1日（Yahoo Financeの仕様）
        end_date_plus = end_date + timedelta(days=1)
        
        # Yahoo Financeのティッカーオブジェクトを作成
        ticker = yf.Ticker(f"{str(stock_code)}.T")
        
        # 株価履歴を取得
        stock_value_df = ticker.history(
            start=date_s,  # 文字列のまま渡せる
            end=end_date_plus.strftime('%Y-%m-%d')
        )
        
        # データが空の場合
        if stock_value_df.empty:
            print(f"データなし: {stock_code}.T（期間: {date_s} ～ {date_e}）")
            return empty_df.copy()
        
        # インデックスをリセット
        stock_value_df = stock_value_df.reset_index()
        
        # 日付カラムの処理（時刻情報を除去）
        stock_value_df['Date'] = pd.to_datetime(
            stock_value_df['Date'].dt.strftime('%Y-%m-%d')
        )
        
        # カラムの存在確認と選択
        existing_columns = []
        for col in default_columns:
            if col in stock_value_df.columns:
                existing_columns.append(col)
        
        # 必要なカラムが揃っているか確認
        if len(existing_columns) < len(default_columns):
            # 足りないカラムを補完
            result_df = pd.DataFrame()
            
            for col in default_columns:
                if col in stock_value_df.columns:
                    result_df[col] = stock_value_df[col]
                else:
                    # カラムが存在しない場合
                    if col == 'Date':
                        result_df[col] = pd.Series(dtype='datetime64[ns]')
                    elif col == 'Volume':
                        result_df[col] = pd.Series(dtype='int64').fillna(0)
                    else:
                        result_df[col] = pd.Series(dtype='float64')
            
            stock_value_df = result_df
        else:
            # 必要なカラムのみを選択
            stock_value_df = stock_value_df[default_columns].copy()
        
        # データ型の確認と変換
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in stock_value_df.columns:
                stock_value_df[col] = pd.to_numeric(
                    stock_value_df[col], 
                    errors='coerce'
                ).astype('float64')
        
        if 'Volume' in stock_value_df.columns:
            stock_value_df['Volume'] = pd.to_numeric(
                stock_value_df['Volume'], 
                errors='coerce'
            ).fillna(0).astype('int64')
        
        # 日付順（昇順）でソート
        stock_value_df = stock_value_df.sort_values(by='Date').reset_index(drop=True)
        
        return stock_value_df
        
    except ValueError as e:
        print(f"日付形式エラー: {e}")
        print("日付は 'YYYY-MM-DD' 形式で指定してください")
        return empty_df.copy()
        
    except Exception as e:
        print(f"データ取得エラー: {e}")
        print(f"銘柄: {stock_code}.T, 期間: {date_s} ～ {date_e}")
        return empty_df.copy()

