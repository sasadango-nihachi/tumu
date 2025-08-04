"""株価データ取得の最小限テスト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tumu.stock import stock_jp  # 変更
from datetime import datetime


def test_jpx_stock_list():
    """JPX株式一覧の取得"""
    df = stock_jp.jpx_stock_list_get()  # 変更
    assert not df.empty
    assert 'stock_code' in df.columns
    assert len(df) > 1000


def test_yfinance_data():
    """Yahoo Financeデータ取得"""
    # 正常ケース
    df = stock_jp.yfinance_jp_data_get('7203', '2024-01-01', '2024-01-31')  # 変更
    assert 'Date' in df.columns
    assert 'Close' in df.columns
    
    # 異常ケース（空のDF）
    df_empty = stock_jp.yfinance_jp_data_get('99999', '2024-01-01', '2024-01-31')  # 変更
    assert df_empty.empty
    assert list(df_empty.columns) == ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']


def test_stooq_data():
    """Stooqデータ取得"""
    df = stock_jp.stooq_jp_data_get('7203', datetime(2024, 1, 1), datetime(2024, 1, 31))  # 変更
    assert 'Date' in df.columns
    assert 'Close' in df.columns