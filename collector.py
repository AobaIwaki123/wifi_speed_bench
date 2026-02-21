"""collector.py - Wi-Fi環境ベンチマーク 計測・記録エンジン（スタブ）"""


def parse_args(argv=None):
    pass


def get_current_ssid(interface="en0"):
    pass


def get_physical_metrics():
    pass


def run_speedtest():
    pass


def build_record(ssid, physical_metrics, speed_metrics):
    pass


def append_log(record, log_path):
    pass


def switch_ssid(ssid, interface="en0", wait_sec=0):
    pass
