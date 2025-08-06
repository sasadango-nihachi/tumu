"""株探出来高ランキング取得の最小限テスト"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import Mock, patch, call
import pandas as pd
from tumu.webscraper.kabutan import (
    scrape_kabutan_volume_ranking,
    stock_volume_get
)


def test_scrape_kabutan_volume_ranking_basic():
    """基本的なスクレイピングテスト"""
    with patch('requests.get') as mock_get:
        # モックHTMLレスポンス
        mock_html = """
        <html>
            <table class="stock_table">
                <tbody>
                    <tr>
                        <td><a href="#">7203</a></td>
                        <th>トヨタ自動車</th>
                        <td>東証プライム</td>
                        <td></td>
                        <td></td>
                        <td>2,500</td>
                        <td class="up">+50</td>
                        <td class="up">+2.04%</td>
                        <td>15,234,500</td>
                        <td>12.5</td>
                        <td>1.2</td>
                        <td>2.5</td>
                    </tr>
                    <tr>
                        <td><a href="#">6758</a></td>
                        <th>ソニーグループ</th>
                        <td>東証プライム</td>
                        <td></td>
                        <td></td>
                        <td>13,000</td>
                        <td class="down">-100</td>
                        <td class="down">-0.76%</td>
                        <td>8,500,000</td>
                        <td>15.3</td>
                        <td>2.1</td>
                        <td>－</td>
                    </tr>
                </tbody>
            </table>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        # 実行
        data = scrape_kabutan_volume_ranking("https://example.com")
        
        # 検証
        assert len(data) == 2
        assert data[0][0] == "7203"  # コード
        assert data[0][1] == "トヨタ自動車"  # 銘柄名
        assert data[0][2] == "東証プライム"  # 市場
        assert data[0][3] == "2,500"  # 株価
        assert data[0][6] == "15234500"  # 出来高（カンマ除去）
        
        assert data[1][0] == "6758"
        assert data[1][1] == "ソニーグループ"


def test_scrape_kabutan_no_table():
    """テーブルが見つからない場合のテスト"""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.text = "<html><body>No table here</body></html>"
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        result = scrape_kabutan_volume_ranking("https://example.com")
        
        assert result is None


@patch('time.sleep')
@patch('random.uniform')
@patch('tumu.webscraper.kabutan.scrape_kabutan_volume_ranking')
def test_stock_volume_get(mock_scrape, mock_random, mock_sleep):
    """複数ページ取得のテスト"""
    mock_random.return_value = 0.5
    
    mock_data = [
        ["7203", "トヨタ自動車", "東証プライム", "2,500", "+50", "+2.04%", "15234500", "12.5", "1.2", "2.5"],
        ["6758", "ソニーグループ", "東証プライム", "13,000", "-100", "-0.76%", "8500000", "15.3", "2.1", "－"]
    ]
    mock_scrape.return_value = mock_data
    
    # 3ページ分取得
    df = stock_volume_get(page=3)
    
    # 検証
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 6  # 2銘柄 × 3ページ
    assert list(df.columns) == ['コード', '銘柄名', '市場', '株価', '前日比(値)', '前日比(%)', '出来高', 'PER', 'PBR', '利回り']
    
    # scrape関数が3回呼ばれたことを確認
    assert mock_scrape.call_count == 3
    
    # sleepも3回呼ばれる（各ページ取得後）
    assert mock_sleep.call_count == 3  # ← 2から3に修正


def test_error_handling():
    """エラーハンドリングのテスト"""
    with patch('requests.get') as mock_get:
        # 不正なHTMLでエラーを発生させる
        mock_response = Mock()
        mock_response.text = """
        <html>
            <table class="stock_table">
                <tbody>
                    <tr>
                        <!-- 不完全な行 -->
                        <td>エラー行</td>
                    </tr>
                    <tr>
                        <td><a href="#">7203</a></td>
                        <th>正常な行</th>
                        <td>東証プライム</td>
                        <td></td>
                        <td></td>
                        <td>2,500</td>
                    </tr>
                </tbody>
            </table>
        </html>
        """
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        # エラーが発生してもクラッシュしないことを確認
        data = scrape_kabutan_volume_ranking("https://example.com")
        
        # 正常な行のみが処理されることを確認
        assert len(data) >= 1  # 少なくとも1行は処理される


def test_data_extraction():
    """データ抽出ロジックのテスト"""
    with patch('requests.get') as mock_get:
        # 様々なパターンのデータを含むHTML
        mock_html = """
        <html>
            <table class="stock_table">
                <tbody>
                    <tr>
                        <td><a href="#">9999</a></td>
                        <th>テスト銘柄</th>
                        <td>東証グロース</td>
                        <td></td>
                        <td></td>
                        <td>1,234</td>
                        <td>0</td>
                        <td>0%</td>
                        <td>999,999</td>
                        <td>－</td>
                        <td>－</td>
                        <td>3.14</td>
                    </tr>
                </tbody>
            </table>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        data = scrape_kabutan_volume_ranking("https://example.com")
        
        assert len(data) == 1
        assert data[0][0] == "9999"  # コード
        assert data[0][4] == "0"  # 前日比（値）が0の場合
        assert data[0][6] == "999999"  # 出来高（カンマ除去）
        assert data[0][7] == "－"  # PERが－の場合
        assert data[0][8] == "－"  # PBRが－の場合