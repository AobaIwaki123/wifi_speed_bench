#!/usr/bin/env python3
"""
visualize.py - Wi-Fi ベンチマークログの可視化ツール

使い方:
    python visualize.py [--log logs/benchmark.jsonl] [--out charts]

生成されるチャート:
    01_time_series.png   - 時系列折れ線グラフ（Download / Upload / Ping）
    02_boxplot.png       - SSID別ボックスプロット（速度・Ping 分布比較）
    03_scatter_rssi.png  - RSSI vs Download / Upload 散布図
    04_bar_avg.png       - SSID別平均メトリクス棒グラフ
    05_heatmap.png       - メトリクス相関ヒートマップ
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timezone
from pathlib import Path

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.rcParams["font.family"] = [
    "Hiragino Sans",
    "Hiragino Maru Gothic Pro",
    "AppleGothic",
    "DejaVu Sans",
]
matplotlib.rcParams["axes.unicode_minus"] = False

# ── 定数 ──────────────────────────────────────────────────────────────────────
DEFAULT_LOG = Path("logs/benchmark.jsonl")
DEFAULT_OUT = Path("charts")

SPEED_METRICS = ["download_mbps", "upload_mbps", "ping_ms"]
METRIC_LABELS: dict[str, str] = {
    "download_mbps": "ダウンロード (Mbps)",
    "upload_mbps": "アップロード (Mbps)",
    "ping_ms": "Ping (ms)",
    "rssi": "RSSI (dBm)",
    "noise": "Noise (dBm)",
    "mcs_index": "MCS Index",
}
PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2", "#937860"]


# ── データ読み込み ────────────────────────────────────────────────────────────
def load_log(log_path: Path) -> pd.DataFrame:
    """JSONL ログを読み込み DataFrame を返す。"""
    if not log_path.exists():
        print(f"[ERROR] ログファイルが見つかりません: {log_path}", file=sys.stderr)
        sys.exit(1)

    records: list[dict] = []
    with log_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        print("[ERROR] ログが空です。", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


# ── チャート 1: 時系列折れ線グラフ ────────────────────────────────────────────
def plot_time_series(df: pd.DataFrame, out_dir: Path) -> None:
    """Download / Upload / Ping の時系列推移を SSID 別に描画する。"""
    metrics = [
        ("download_mbps", "ダウンロード速度"),
        ("upload_mbps", "アップロード速度"),
        ("ping_ms", "Ping"),
    ]
    ssids = df["ssid"].unique()
    color_map = {ssid: PALETTE[i % len(PALETTE)] for i, ssid in enumerate(ssids)}

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    fig.suptitle("時系列推移（SSID 別）", fontsize=14, fontweight="bold", y=1.01)

    for ax, (col, title) in zip(axes, metrics):
        for ssid in ssids:
            sub = df[df["ssid"] == ssid]
            ax.plot(
                sub["timestamp"],
                sub[col],
                marker="o",
                markersize=5,
                linewidth=1.6,
                label=ssid,
                color=color_map[ssid],
            )
        ax.set_ylabel(METRIC_LABELS[col], fontsize=9)
        ax.set_title(title, fontsize=10, pad=4)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(fontsize=8, loc="upper right")

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%m/%d\n%H:%M"))
    axes[-1].xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=0, ha="center")

    fig.tight_layout()
    out = out_dir / "01_time_series.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  保存: {out}")


# ── チャート 2: SSID 別ボックスプロット ────────────────────────────────────────
def plot_boxplot(df: pd.DataFrame, out_dir: Path) -> None:
    """Download / Upload / Ping の SSID 別分布をボックスプロットで比較する。"""
    ssids = sorted(df["ssid"].unique())
    metrics = [
        ("download_mbps", "ダウンロード速度 (Mbps)"),
        ("upload_mbps", "アップロード速度 (Mbps)"),
        ("ping_ms", "Ping (ms)"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    fig.suptitle("SSID 別メトリクス分布", fontsize=14, fontweight="bold")

    for ax, (col, ylabel) in zip(axes, metrics):
        data = [df.loc[df["ssid"] == s, col].dropna().values for s in ssids]
        bp = ax.boxplot(
            data,
            tick_labels=ssids,
            patch_artist=True,
            medianprops=dict(color="black", linewidth=2),
        )
        for patch, color in zip(bp["boxes"], PALETTE):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(col.replace("_", " "), fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        ax.tick_params(axis="x", labelsize=8)

    fig.tight_layout()
    out = out_dir / "02_boxplot.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  保存: {out}")


# ── チャート 3: RSSI vs 速度 散布図 ────────────────────────────────────────────
def plot_scatter_rssi(df: pd.DataFrame, out_dir: Path) -> None:
    """RSSI と Download / Upload 速度の相関を散布図で示す。"""
    ssids = sorted(df["ssid"].unique())
    color_map = {ssid: PALETTE[i % len(PALETTE)] for i, ssid in enumerate(ssids)}

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("RSSI と速度の相関", fontsize=14, fontweight="bold")

    for ax, (col, ylabel) in zip(
        axes,
        [
            ("download_mbps", "ダウンロード (Mbps)"),
            ("upload_mbps", "アップロード (Mbps)"),
        ],
    ):
        for ssid in ssids:
            sub = df[df["ssid"] == ssid]
            ax.scatter(
                sub["rssi"],
                sub[col],
                label=ssid,
                color=color_map[ssid],
                alpha=0.8,
                s=70,
                edgecolors="white",
                linewidth=0.5,
            )
        # 全データで回帰直線
        x = df["rssi"].values.astype(float)
        y = df[col].values.astype(float)
        if len(x) > 1:
            coef = np.polyfit(x, y, 1)
            xline = np.linspace(x.min(), x.max(), 100)
            ax.plot(
                xline,
                np.polyval(coef, xline),
                color="gray",
                linewidth=1.5,
                linestyle="--",
                label=f"回帰直線 (slope={coef[0]:.2f})",
            )
        ax.set_xlabel("RSSI (dBm)", fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(col.replace("_", " "), fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, linestyle="--", alpha=0.4)

    fig.tight_layout()
    out = out_dir / "03_scatter_rssi.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  保存: {out}")


# ── チャート 4: SSID 別平均棒グラフ ────────────────────────────────────────────
def plot_bar_avg(df: pd.DataFrame, out_dir: Path) -> None:
    """SSID ごとに Download / Upload / Ping の平均値を棒グラフで表示する。"""
    cols = ["download_mbps", "upload_mbps", "ping_ms"]
    ssids = sorted(df["ssid"].unique())
    means = df.groupby("ssid")[cols].mean().reindex(ssids)
    stds = df.groupby("ssid")[cols].std().reindex(ssids)

    x = np.arange(len(ssids))
    width = 0.25

    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    fig.suptitle("SSID 別平均メトリクス（±1σ）", fontsize=14, fontweight="bold")

    for ax, (col, ylabel) in zip(
        axes,
        [
            ("download_mbps", "平均ダウンロード (Mbps)"),
            ("upload_mbps", "平均アップロード (Mbps)"),
            ("ping_ms", "平均 Ping (ms)"),
        ],
    ):
        bars = ax.bar(
            x,
            means[col],
            yerr=stds[col],
            color=[PALETTE[i % len(PALETTE)] for i in range(len(ssids))],
            alpha=0.8,
            capsize=5,
            edgecolor="white",
            linewidth=0.8,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(ssids, fontsize=8, rotation=15, ha="right")
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(col.replace("_", " "), fontsize=10)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        # 棒の上に数値
        for bar, val in zip(bars, means[col]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{val:.1f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    fig.tight_layout()
    out = out_dir / "04_bar_avg.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  保存: {out}")


# ── チャート 5: 相関ヒートマップ ───────────────────────────────────────────────
def plot_heatmap(df: pd.DataFrame, out_dir: Path) -> None:
    """数値メトリクス間の相関係数をヒートマップで可視化する。"""
    num_cols = ["download_mbps", "upload_mbps", "ping_ms", "rssi", "noise", "mcs_index"]
    corr = df[num_cols].corr()
    labels = [METRIC_LABELS[c] for c in num_cols]

    fig, ax = plt.subplots(figsize=(8, 6))
    fig.suptitle("メトリクス相関ヒートマップ", fontsize=14, fontweight="bold")

    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Pearson r")

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8, rotation=30, ha="right")
    ax.set_yticklabels(labels, fontsize=8)

    for i in range(len(num_cols)):
        for j in range(len(num_cols)):
            val = corr.values[i, j]
            color = "white" if abs(val) > 0.6 else "black"
            ax.text(
                j, i, f"{val:.2f}", ha="center", va="center", fontsize=8, color=color
            )

    fig.tight_layout()
    out = out_dir / "05_heatmap.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  保存: {out}")


# ── JSON エクスポート ────────────────────────────────────────────────────────
def export_stats_json(df: pd.DataFrame, out_dir: Path) -> dict:
    """集計済み統計 + 時系列データを stats.json に書き出し、dict を返す。"""
    num_cols = ["download_mbps", "upload_mbps", "ping_ms", "rssi", "noise", "mcs_index"]
    corr = df[num_cols].corr()

    stats: dict = {}
    for ssid, grp in df.groupby("ssid"):
        entry: dict = {"band": grp["band"].iloc[0], "count": int(len(grp))}
        for col in num_cols:
            v = grp[col].dropna()
            entry[col] = {
                "avg": round(float(v.mean()), 2),
                "min": round(float(v.min()), 2),
                "max": round(float(v.max()), 2),
                "std": round(float(v.std()), 2),
                "values": [round(float(x), 2) for x in v],
            }
        stats[ssid] = entry

    time_series = [
        {
            "timestamp": row["timestamp"].isoformat(),
            "ssid": row["ssid"],
            **{c: round(float(row[c]), 2) for c in num_cols if pd.notna(row[c])},
        }
        for _, row in df.iterrows()
    ]

    data = {
        "generated_at": pd.Timestamp.now(tz=timezone.utc).isoformat(),
        "total_records": int(len(df)),
        "period": {
            "start": df["timestamp"].min().isoformat(),
            "end": df["timestamp"].max().isoformat(),
        },
        "ssids": sorted(df["ssid"].unique().tolist()),
        "stats": stats,
        "time_series": time_series,
        "correlation": {
            "fields": num_cols,
            "matrix": [[round(float(v), 3) for v in row] for row in corr.values],
        },
    }

    out = out_dir / "stats.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  保存: {out}")
    return data


# ── HTML ダッシュボード ────────────────────────────────────────────────────────
_CHART_COLORS = [
    ("99,102,241", "#6366f1"),  # indigo
    ("245,158,11", "#f59e0b"),  # amber
    ("16,185,129", "#10b981"),  # emerald
    ("239,68,68", "#ef4444"),  # red
]


def export_dashboard(data: dict, out_dir: Path) -> None:
    """JSON データを埋め込んだ自己完結 HTML ダッシュボードを生成する。"""
    ssids = data["ssids"]
    stats = data["stats"]
    corr = data["correlation"]

    # ── KPI cards (f-string: Python変数のみ、JS {} なし) ─────────────────────
    kpi_cards_html = ""
    for i, ssid in enumerate(ssids):
        _, hex_color = _CHART_COLORS[i % len(_CHART_COLORS)]
        s = stats[ssid]
        kpi_cards_html += (
            f'<div class="card kpi-card" style="border-top:4px solid {hex_color}">'
            f'<div class="kpi-ssid" style="color:{hex_color}">{ssid}</div>'
            f'<div class="kpi-band">{s["band"]} &middot; {s["count"]} samples</div>'
            '<div class="kpi-grid">'
            f'<div class="kpi-item"><div class="kpi-val">{s["download_mbps"]["avg"]}</div>'
            '<div class="kpi-label">\u2193 Mbps</div></div>'
            f'<div class="kpi-item"><div class="kpi-val">{s["upload_mbps"]["avg"]}</div>'
            '<div class="kpi-label">\u2191 Mbps</div></div>'
            f'<div class="kpi-item"><div class="kpi-val">{s["ping_ms"]["avg"]}</div>'
            '<div class="kpi-label">Ping ms</div></div>'
            f'<div class="kpi-item"><div class="kpi-val">{s["rssi"]["avg"]}</div>'
            '<div class="kpi-label">RSSI dBm</div></div>'
            "</div></div>"
        )

    # ── 相関テーブル ──────────────────────────────────────────────────────────
    corr_fields_short = ["DL", "UL", "Ping", "RSSI", "Noise", "MCS"]
    corr_header = "".join(f"<th>{f}</th>" for f in corr_fields_short)
    corr_rows_html = ""
    for row_vals, label in zip(corr["matrix"], corr_fields_short):
        cells = "".join(
            '<td style="background:'
            + _corr_cell_color(v)
            + ";color:"
            + ("#fff" if abs(v) > 0.6 else "#1e293b")
            + f'">{v:.2f}</td>'
            for v in row_vals
        )
        corr_rows_html += f"<tr><th>{label}</th>{cells}</tr>"

    # ── Python 側で計算した値を JSON として JS に渡す ──────────────────────────
    json_blob = json.dumps(data, ensure_ascii=False)
    colors_json = json.dumps([c[1] for c in _CHART_COLORS])
    colors_a_json = json.dumps([f"rgba({c[0]},0.18)" for c in _CHART_COLORS])

    # ── CSS: 通常文字列 (f-string 不使用) ─────────────────────────────────────
    css = (
        "*,::before,::after{box-sizing:border-box;margin:0;padding:0}"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
        "background:#f1f5f9;color:#1e293b;font-size:14px}"
        "header{background:#fff;border-bottom:1px solid #e2e8f0;padding:16px 28px;"
        "display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:10;"
        "box-shadow:0 1px 4px rgba(0,0,0,.06)}"
        "header h1{font-size:18px;font-weight:700;letter-spacing:-.3px}"
        "header .meta{margin-left:auto;font-size:12px;color:#64748b}"
        ".container{max-width:1280px;margin:0 auto;padding:24px 20px;display:grid;gap:20px}"
        ".kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}"
        ".card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 1px 6px rgba(0,0,0,.07)}"
        ".card-title{font-size:13px;font-weight:600;color:#475569;"
        "text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px}"
        ".kpi-card{padding:20px 22px}"
        ".kpi-ssid{font-size:15px;font-weight:700;word-break:break-all}"
        ".kpi-band{font-size:11px;color:#94a3b8;margin:3px 0 14px}"
        ".kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}"
        ".kpi-item{background:#f8fafc;border-radius:8px;padding:10px 12px}"
        ".kpi-val{font-size:22px;font-weight:700;line-height:1}"
        ".kpi-label{font-size:11px;color:#94a3b8;margin-top:3px}"
        ".two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}"
        "@media(max-width:768px){.two-col{grid-template-columns:1fr}}"
        "canvas{max-height:320px}"
        "table.corr{width:100%;border-collapse:collapse;font-size:12px}"
        "table.corr th{background:#f8fafc;padding:6px 8px;font-weight:600;text-align:center}"
        "table.corr td{padding:6px 8px;text-align:center;border:1px solid #e2e8f0}"
    )

    # ── JS: 通常文字列 (f-string 不使用、プレースホルダ埋め込み後置換) ──────────
    js = r"""
(function() {
  const D = /*@JSON@*/null;
  const ssids = D.ssids;
  const COLORS   = /*@COLORS@*/null;
  const COLORS_A = /*@COLORS_A@*/null;

  document.getElementById('meta').textContent =
    `${D.total_records} records \u00b7 ${D.period.start.slice(0,10)} \u2192 ${D.period.end.slice(0,10)}`;

  // Time series
  const tsDatasets = ssids.flatMap((ssid, i) => {
    const rows = D.time_series.filter(r => r.ssid === ssid);
    const lbs  = rows.map(r => r.timestamp.slice(5,16).replace('T',' '));
    const c = COLORS[i % COLORS.length];
    return [
      { label:`${ssid} \u2193`, data:rows.map((r,j) => ({x:lbs[j], y:r.download_mbps})),
        borderColor:c, backgroundColor:'transparent', tension:.3, pointRadius:4, borderWidth:2 },
      { label:`${ssid} \u2191`, data:rows.map((r,j) => ({x:lbs[j], y:r.upload_mbps})),
        borderColor:c, backgroundColor:'transparent', tension:.3, pointRadius:4,
        borderWidth:2, borderDash:[5,3] },
    ];
  });
  new Chart(document.getElementById('tsChart'), {
    type:'line', data:{datasets:tsDatasets},
    options:{ responsive:true, interaction:{mode:'index',intersect:false},
      scales:{ x:{type:'category',ticks:{maxRotation:45,font:{size:10}}},
               y:{title:{display:true,text:'Mbps'}} },
      plugins:{ legend:{labels:{boxWidth:12,font:{size:11}}} } }
  });

  // Bar avg
  new Chart(document.getElementById('barChart'), {
    type:'bar',
    data:{ labels:['Download','Upload'],
      datasets: ssids.map((ssid,i) => ({
        label:ssid,
        data:[D.stats[ssid].download_mbps.avg, D.stats[ssid].upload_mbps.avg],
        backgroundColor:COLORS_A[i%COLORS.length],
        borderColor:COLORS[i%COLORS.length],
        borderWidth:2, borderRadius:6,
      }))
    },
    options:{ responsive:true,
      scales:{ y:{beginAtZero:true,title:{display:true,text:'Mbps'}} },
      plugins:{ legend:{labels:{boxWidth:12,font:{size:11}}} } }
  });

  // Scatter RSSI vs Download
  new Chart(document.getElementById('scatterChart'), {
    type:'scatter',
    data:{ datasets: ssids.map((ssid,i) => ({
        label:ssid,
        data: D.time_series.filter(r=>r.ssid===ssid).map(r=>({x:r.rssi,y:r.download_mbps})),
        backgroundColor:COLORS[i%COLORS.length],
        pointRadius:6, pointHoverRadius:8,
      }))
    },
    options:{ responsive:true,
      scales:{ x:{title:{display:true,text:'RSSI (dBm)'}},
               y:{title:{display:true,text:'Download Mbps'}} },
      plugins:{ legend:{labels:{boxWidth:12,font:{size:11}}} } }
  });

  // Ping bar
  new Chart(document.getElementById('pingChart'), {
    type:'bar',
    data:{ labels:ssids,
      datasets:[{
        label:'avg Ping',
        data: ssids.map(s => D.stats[s].ping_ms.avg),
        backgroundColor: ssids.map((_,i) => COLORS_A[i%COLORS.length]),
        borderColor: ssids.map((_,i) => COLORS[i%COLORS.length]),
        borderWidth:2, borderRadius:6,
      }]
    },
    options:{ responsive:true,
      scales:{ y:{beginAtZero:true,title:{display:true,text:'ms'}} },
      plugins:{ legend:{display:false} } }
  });
})();
"""
    js = (
        js.replace("/*@JSON@*/null", json_blob)
        .replace("/*@COLORS@*/null", colors_json)
        .replace("/*@COLORS_A@*/null", colors_a_json)
    )

    # ── 組み立て ──────────────────────────────────────────────────────────────
    html = (
        '<!DOCTYPE html><html lang="ja"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Wi-Fi Benchmark Dashboard</title>"
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4/dist/chart.umd.min.js"></script>'
        f"<style>{css}</style></head><body>"
        "<header>"
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6366f1"'
        ' stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M5 12.55a11 11 0 0 1 14.08 0"/>'
        '<path d="M1.42 9a16 16 0 0 1 21.16 0"/>'
        '<path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>'
        '<circle cx="12" cy="20" r="1"/></svg>'
        "<h1>Wi-Fi Benchmark Dashboard</h1>"
        '<div class="meta" id="meta"></div></header>'
        '<div class="container">'
        f'<div class="kpi-row">{kpi_cards_html}</div>'
        '<div class="card">'
        '<div class="card-title">\u6642\u7cfb\u5217 \u2015 Download / Upload (Mbps)</div>'
        '<canvas id="tsChart"></canvas></div>'
        '<div class="two-col">'
        '<div class="card"><div class="card-title">SSID \u5225\u5e73\u5747\u901f\u5ea6 (Mbps)</div>'
        '<canvas id="barChart"></canvas></div>'
        '<div class="card"><div class="card-title">RSSI vs Download (Mbps)</div>'
        '<canvas id="scatterChart"></canvas></div></div>'
        '<div class="two-col">'
        '<div class="card"><div class="card-title">Ping \u5e73\u5747 (ms)</div>'
        '<canvas id="pingChart"></canvas></div>'
        '<div class="card"><div class="card-title">\u30e1\u30c8\u30ea\u30af\u30b9\u76f8\u95a2</div>'
        f'<table class="corr"><thead><tr><th></th>{corr_header}</tr></thead>'
        f"<tbody>{corr_rows_html}</tbody></table></div></div>"
        "</div>"
        f"<script>{js}</script>"
        "</body></html>"
    )

    out = out_dir / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"  保存: {out}")


def _corr_cell_color(v: float) -> str:
    """相関値 [-1,1] を赤青グラデーションの CSS 色に変換する。"""
    # 正 → indigo, 負 → rose, 0 → white
    if v > 0:
        a = round(v * 0.85, 2)
        return f"rgba(99,102,241,{a})"
    else:
        a = round(-v * 0.85, 2)
        return f"rgba(239,68,68,{a})"


# ── サマリー表示 ──────────────────────────────────────────────────────────────
def print_summary(df: pd.DataFrame) -> None:
    """SSID ごとの基本統計をコンソールに出力する。"""
    cols = ["download_mbps", "upload_mbps", "ping_ms", "rssi", "mcs_index"]
    print("\n" + "=" * 60)
    print("  計測サマリー")
    print("=" * 60)
    print(f"  総レコード数: {len(df)}")
    print(
        f"  期間: {df['timestamp'].min():%Y-%m-%d %H:%M} ～ {df['timestamp'].max():%Y-%m-%d %H:%M}"
    )
    print()
    for ssid, grp in df.groupby("ssid"):
        band = grp["band"].iloc[0]
        print(f"  [{ssid}]  帯域: {band}  レコード数: {len(grp)}")
        for col in cols:
            v = grp[col].dropna()
            print(
                f"    {METRIC_LABELS[col]:28s}  "
                f"avg={v.mean():.1f}  min={v.min():.1f}  max={v.max():.1f}  σ={v.std():.1f}"
            )
        print()
    print("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="visualize.py",
        description="Wi-Fi ベンチマークログ可視化ツール",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        metavar="PATH",
        help=f"JSONL ログファイルのパス (デフォルト: {DEFAULT_LOG})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        metavar="DIR",
        help=f"チャートの出力ディレクトリ (デフォルト: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="コンソールへのサマリー表示を抑制する",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    print(f"ログ読み込み中: {args.log}")
    df = load_log(args.log)
    print(f"  {len(df)} レコードを読み込みました。")

    if not args.no_summary:
        print_summary(df)

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"\nチャートを生成中 → {args.out}/")

    plot_time_series(df, args.out)
    plot_boxplot(df, args.out)
    plot_scatter_rssi(df, args.out)
    plot_bar_avg(df, args.out)
    plot_heatmap(df, args.out)

    print("\nJSON / ダッシュボードを生成中 →")
    stats_data = export_stats_json(df, args.out)
    export_dashboard(stats_data, args.out)

    print("\n完了。")
    print(f"  ブラウザで開く: open {args.out}/dashboard.html")


if __name__ == "__main__":
    main()
