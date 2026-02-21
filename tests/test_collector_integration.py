"""tests/test_collector_integration.py - 実コマンドを使う統合テスト

実行方法:
    # 統合テストのみ実行
    pytest -m integration -v

    # ユニットテストのみ実行（統合テストを除外）
    pytest -m "not integration" -v

注意:
    - Wi-Fi に接続した状態で実行すること
    - TestRunSpeedtestIntegration は実際に外部通信を行うため時間がかかる（~30秒）
"""
import pytest

import collector


# ---------------------------------------------------------------------------
# get_physical_metrics（実コマンド）
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestGetPhysicalMetricsIntegration:
    def test_get_physical_metrics_returns_dict(self):
        """実行結果が辞書型であることを確認する"""
        result = collector.get_physical_metrics()
        assert isinstance(result, dict)

    def test_get_physical_metrics_has_required_keys(self):
        """必須キーが全て存在することを確認する"""
        result = collector.get_physical_metrics()
        assert {"rssi", "noise", "mcs_index", "channel", "band"} <= result.keys()

    def test_get_physical_metrics_rssi_is_negative(self):
        """RSSIは通常負の値（dBm）であることを確認する"""
        result = collector.get_physical_metrics()
        if result["rssi"] is not None:
            assert result["rssi"] < 0, f"RSSI should be negative, got {result['rssi']}"

    def test_get_physical_metrics_noise_is_negative(self):
        """Noiseは通常負の値（dBm）であることを確認する"""
        result = collector.get_physical_metrics()
        if result["noise"] is not None:
            assert result["noise"] < 0, f"Noise should be negative, got {result['noise']}"

    def test_get_physical_metrics_mcs_index_is_non_negative(self):
        """MCS Indexは0以上の整数であることを確認する"""
        result = collector.get_physical_metrics()
        if result["mcs_index"] is not None:
            assert result["mcs_index"] >= 0, f"MCS Index should be >= 0, got {result['mcs_index']}"

    def test_get_physical_metrics_channel_is_positive(self):
        """チャンネル番号が正の整数であることを確認する"""
        result = collector.get_physical_metrics()
        if result["channel"] is not None:
            assert result["channel"] > 0, f"Channel should be > 0, got {result['channel']}"

    def test_get_physical_metrics_band_is_valid(self):
        """帯域が既知の値（2.4GHz/5GHz/6GHz）であることを確認する"""
        result = collector.get_physical_metrics()
        if result["band"] is not None:
            assert result["band"] in {"2.4GHz", "5GHz", "6GHz"}, f"Unknown band: {result['band']}"


# ---------------------------------------------------------------------------
# run_speedtest（実際の外部通信: 時間がかかるため明示的に実行する場合のみ使用）
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.slow
class TestRunSpeedtestIntegration:
    def test_run_speedtest_returns_positive_values(self):
        """実際のspeedtestが正の値を返すことを確認する（~30秒かかる）"""
        result = collector.run_speedtest()
        assert result["download_mbps"] > 0
        assert result["upload_mbps"] > 0
        assert result["ping_ms"] > 0

    def test_run_speedtest_returns_expected_keys(self):
        """実際のspeedtestが必須キーを返すことを確認する"""
        result = collector.run_speedtest()
        assert {"download_mbps", "upload_mbps", "ping_ms"} <= result.keys()

