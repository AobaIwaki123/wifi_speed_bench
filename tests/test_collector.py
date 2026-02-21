"""tests/test_collector.py - collector.py のユニットテスト"""

import inspect
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import collector

# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    def test_parse_args_with_valid_ssids(self):
        args = collector.parse_args(["--ssids", "A", "B"])
        assert args.ssids == ["A", "B"]

    def test_parse_args_default_count(self):
        args = collector.parse_args(["--ssids", "A"])
        assert args.count == 3

    def test_parse_args_default_interval(self):
        args = collector.parse_args(["--ssids", "A"])
        assert args.interval == 10

    def test_parse_args_custom_count(self):
        args = collector.parse_args(["--ssids", "A", "--count", "5"])
        assert args.count == 5

    def test_parse_args_custom_interval(self):
        args = collector.parse_args(["--ssids", "A", "--interval", "30"])
        assert args.interval == 30

    def test_parse_args_missing_ssids_raises_error(self):
        with pytest.raises(SystemExit):
            collector.parse_args([])


# ---------------------------------------------------------------------------
# get_physical_metrics
# ---------------------------------------------------------------------------

AIRPORT_OUTPUT = """\
Wi-Fi:

      Interfaces:
        en0:
          Status: Connected
          Current Network Information:
            MyNet_5GHz:
              PHY Mode: 802.11ax
              Channel: 100 (5GHz, 80MHz)
              Signal / Noise: -55 dBm / -95 dBm
              Transmit Rate: 780
              MCS Index: 9
"""

AIRPORT_OUTPUT_NO_MCS = """\
Wi-Fi:

      Interfaces:
        en0:
          Current Network Information:
            MyNet_5GHz:
              Signal / Noise: -55 dBm / -95 dBm
"""


class TestGetPhysicalMetrics:
    def _mock_airport(self, stdout, returncode=0):
        mock_result = MagicMock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        return mock_result

    def test_get_physical_metrics_returns_expected_keys(self):
        with patch("subprocess.run", return_value=self._mock_airport(AIRPORT_OUTPUT)):
            result = collector.get_physical_metrics()
        assert {"rssi", "noise", "mcs_index", "channel", "band"} <= result.keys()

    def test_get_physical_metrics_parses_rssi(self):
        with patch("subprocess.run", return_value=self._mock_airport(AIRPORT_OUTPUT)):
            result = collector.get_physical_metrics()
        assert result["rssi"] == -55

    def test_get_physical_metrics_parses_noise(self):
        with patch("subprocess.run", return_value=self._mock_airport(AIRPORT_OUTPUT)):
            result = collector.get_physical_metrics()
        assert result["noise"] == -95

    def test_get_physical_metrics_parses_mcs_index(self):
        with patch("subprocess.run", return_value=self._mock_airport(AIRPORT_OUTPUT)):
            result = collector.get_physical_metrics()
        assert result["mcs_index"] == 9

    def test_get_physical_metrics_parses_channel(self):
        with patch("subprocess.run", return_value=self._mock_airport(AIRPORT_OUTPUT)):
            result = collector.get_physical_metrics()
        assert result["channel"] == 100

    def test_get_physical_metrics_parses_band(self):
        with patch("subprocess.run", return_value=self._mock_airport(AIRPORT_OUTPUT)):
            result = collector.get_physical_metrics()
        assert result["band"] == "5GHz"

    def test_get_physical_metrics_when_command_fails(self):
        with patch("subprocess.run", return_value=self._mock_airport("", returncode=1)):
            with pytest.raises(RuntimeError):
                collector.get_physical_metrics()

    def test_get_physical_metrics_missing_field(self):
        with patch(
            "subprocess.run", return_value=self._mock_airport(AIRPORT_OUTPUT_NO_MCS)
        ):
            result = collector.get_physical_metrics()
        assert result["mcs_index"] is None
        assert result["channel"] is None
        assert result["band"] is None


# ---------------------------------------------------------------------------
# run_speedtest
# ---------------------------------------------------------------------------

SPEEDTEST_RESULT = {
    "download": 432_399_360.0,
    "upload": 93_478_912.0,
    "ping": 12.4,
    "server": {"name": "Tokyo"},
    "timestamp": "2026-02-22T10:00:00Z",
}


class TestRunSpeedtest:
    def _make_mock_speedtest(self):
        mock_st = MagicMock()
        mock_st.results.dict.return_value = SPEEDTEST_RESULT
        return mock_st

    def test_run_speedtest_returns_expected_keys(self):
        with patch("speedtest.Speedtest", return_value=self._make_mock_speedtest()):
            result = collector.run_speedtest()
        assert {"download_mbps", "upload_mbps", "ping_ms"} <= result.keys()

    def test_run_speedtest_converts_to_mbps(self):
        with patch("speedtest.Speedtest", return_value=self._make_mock_speedtest()):
            result = collector.run_speedtest()
        assert result["download_mbps"] == pytest.approx(432.4, abs=0.1)

    def test_run_speedtest_values_are_positive(self):
        with patch("speedtest.Speedtest", return_value=self._make_mock_speedtest()):
            result = collector.run_speedtest()
        assert result["download_mbps"] > 0
        assert result["upload_mbps"] > 0
        assert result["ping_ms"] > 0

    def test_run_speedtest_on_network_error(self):
        with patch("speedtest.Speedtest", side_effect=Exception("network error")):
            with pytest.raises(RuntimeError):
                collector.run_speedtest()


# ---------------------------------------------------------------------------
# build_record
# ---------------------------------------------------------------------------

PHYSICAL = {"rssi": -55, "noise": -95, "mcs_index": 9, "channel": 100, "band": "5GHz"}
SPEED = {"download_mbps": 412.3, "upload_mbps": 89.1, "ping_ms": 12.4}
REQUIRED_FIELDS = {
    "timestamp",
    "ssid",
    "rssi",
    "noise",
    "mcs_index",
    "channel",
    "band",
    "download_mbps",
    "upload_mbps",
    "ping_ms",
}


class TestBuildRecord:
    def test_build_record_contains_all_required_fields(self):
        record = collector.build_record("MyNet_5GHz", PHYSICAL, SPEED)
        assert REQUIRED_FIELDS <= record.keys()

    def test_build_record_timestamp_format(self):
        record = collector.build_record("MyNet_5GHz", PHYSICAL, SPEED)
        datetime.fromisoformat(record["timestamp"])  # 不正なら ValueError が上がる

    def test_build_record_ssid_matches_input(self):
        record = collector.build_record("MyNet_5GHz", PHYSICAL, SPEED)
        assert record["ssid"] == "MyNet_5GHz"

    def test_build_record_metrics_are_merged(self):
        record = collector.build_record("MyNet_5GHz", PHYSICAL, SPEED)
        assert record["rssi"] == -55
        assert record["noise"] == -95
        assert record["mcs_index"] == 9
        assert record["channel"] == 100
        assert record["band"] == "5GHz"
        assert record["download_mbps"] == 412.3
        assert record["upload_mbps"] == 89.1
        assert record["ping_ms"] == 12.4


# ---------------------------------------------------------------------------
# append_log
# ---------------------------------------------------------------------------

SAMPLE_RECORD = {
    "timestamp": "2026-02-22T10:00:00+09:00",
    "ssid": "MyNet_5GHz",
    "rssi": -55,
    "noise": -95,
    "mcs_index": 9,
    "download_mbps": 412.3,
    "upload_mbps": 89.1,
    "ping_ms": 12.4,
}


class TestAppendLog:
    def test_append_log_creates_file_if_not_exists(self, tmp_path):
        log_path = tmp_path / "benchmark.jsonl"
        assert not log_path.exists()
        collector.append_log(SAMPLE_RECORD, log_path)
        assert log_path.exists()

    def test_append_log_writes_valid_json(self, tmp_path):
        log_path = tmp_path / "benchmark.jsonl"
        collector.append_log(SAMPLE_RECORD, log_path)
        line = log_path.read_text().strip()
        parsed = json.loads(line)
        assert parsed["ssid"] == "MyNet_5GHz"

    def test_append_log_appends_multiple_records(self, tmp_path):
        log_path = tmp_path / "benchmark.jsonl"
        collector.append_log(SAMPLE_RECORD, log_path)
        collector.append_log(SAMPLE_RECORD, log_path)
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_append_log_creates_directory_if_not_exists(self, tmp_path):
        log_path = tmp_path / "new_dir" / "benchmark.jsonl"
        collector.append_log(SAMPLE_RECORD, log_path)
        assert log_path.exists()

    def test_append_log_permission_error(self, tmp_path):
        log_path = tmp_path / "benchmark.jsonl"
        log_path.write_text("")
        log_path.chmod(0o444)
        try:
            with pytest.raises(PermissionError):
                collector.append_log(SAMPLE_RECORD, log_path)
        finally:
            log_path.chmod(0o644)  # クリーンアップのために権限を戻す


# ---------------------------------------------------------------------------
# switch_ssid
# ---------------------------------------------------------------------------


class TestSwitchSsid:
    def test_switch_ssid_calls_correct_command(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with (
            patch("subprocess.run", return_value=mock_result) as mock_run,
            patch("time.sleep"),
        ):
            collector.switch_ssid("MyNet_5GHz", interface="en0", wait_sec=0)
        args = mock_run.call_args[0][0]
        assert "networksetup" in args
        assert "-setairportnetwork" in args
        assert "en0" in args
        assert "MyNet_5GHz" in args

    def test_switch_ssid_waits_after_switch(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        with (
            patch("subprocess.run", return_value=mock_result),
            patch("time.sleep") as mock_sleep,
        ):
            collector.switch_ssid("MyNet_5GHz", wait_sec=5)
        mock_sleep.assert_called_once_with(5)

    def test_switch_ssid_default_wait_is_nonzero(self):
        sig = inspect.signature(collector.switch_ssid)
        default = sig.parameters["wait_sec"].default
        assert default > 0

    def test_switch_ssid_raises_on_unknown_ssid(self):
        mock_result = MagicMock()
        mock_result.returncode = 4
        with patch("subprocess.run", return_value=mock_result), patch("time.sleep"):
            with pytest.raises(RuntimeError):
                collector.switch_ssid("UnknownNet")

    def test_switch_ssid_raises_on_command_not_found(self):
        with (
            patch("subprocess.run", side_effect=FileNotFoundError),
            patch("time.sleep"),
        ):
            with pytest.raises(RuntimeError):
                collector.switch_ssid("MyNet_5GHz")
