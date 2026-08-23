#!/usr/bin/env python3
"""อ่านรายงาน Strategy Tester ของ MT5 (.htm/.html) แล้วสร้างกราฟ + สรุปตัวเลข

ใช้:
    python3 tools/mt5_report_charts.py ReportTester.htm -o charts/ --server-gmt 3

กราฟที่ได้ (ไฟล์ .png ในโฟลเดอร์ผลลัพธ์):
    1_equity.png     เส้นทุน + ช่วงติดลบ (drawdown)
    2_monthly.png    กำไร/ขาดทุนรายเดือน
    3_by_hour.png    กำไรแยกตามชั่วโมงที่ "ปิดไม้" -- ใช้ตรวจว่าขอบมาจากชั่วโมงไหนจริง
    4_dist.png       การกระจายกำไรต่อไม้

รองรับรายงานที่เซฟเป็น UTF-8 / UTF-16 / cp1252 (MT5 เซฟไม่เหมือนกันในแต่ละบิลด์)
"""
import argparse
import os
import re
import sys
from datetime import datetime
from html.parser import HTMLParser

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager


def _use_thai_font():
    """ฟอนต์เริ่มต้นของ matplotlib ไม่มีตัวอักษรไทย ป้ายกำกับจะกลายเป็นสี่เหลี่ยม
    โหลด Noto Sans Thai ที่วางไว้ข้าง ๆ สคริปต์ ถ้าไม่มีก็ปล่อยผ่าน"""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "fonts", "NotoSansThai-Regular.ttf")
    if not os.path.exists(path):
        print("เตือน: ไม่พบ tools/fonts/NotoSansThai-Regular.ttf -> ป้ายภาษาไทยจะเพี้ยน",
              file=sys.stderr)
        return
    font_manager.fontManager.addfont(path)
    name = font_manager.FontProperties(fname=path).get_name()
    plt.rcParams["font.family"] = [name, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


_use_thai_font()


# ---------------------------------------------------------------- อ่าน HTML
class TableGrab(HTMLParser):
    """เก็บทุก <tr> เป็น list ของข้อความในเซลล์ โดยไม่สนใจโครงสร้างตารางซ้อน"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            text = " ".join("".join(self._cell).split())
            self._row.append(text)
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(c for c in self._row):
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def read_text(path):
    raw = open(path, "rb").read()
    for enc in ("utf-16", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
        # utf-16 ถอดไฟล์ utf-8 ได้แบบขยะ เช็คว่ามีแท็ก html จริง
        if "<tr" in text.lower() or "<table" in text.lower():
            return text
    raise SystemExit(f"อ่านไฟล์ไม่ออก (ลอง utf-16/utf-8/cp1252 แล้ว): {path}")


# ------------------------------------------------------- ดึงตารางรายการดีล
NUM_RE = re.compile(r"^-?[\d\s ]+(?:[.,]\d+)?$")


def to_num(s):
    if s is None:
        return None
    s = s.replace(" ", "").replace(" ", "").replace(",", "")
    if not s or not NUM_RE.match(s.replace(",", "")):
        try:
            return float(s)
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_time(s):
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def extract_deals(rows):
    """หาแถวหัวตารางดีล แล้วอ่านแถวถัดไปจนหมด"""
    header_idx = None
    cols = {}
    for i, r in enumerate(rows):
        low = [c.lower() for c in r]
        if "profit" in low and "balance" in low and any(c.startswith("time") for c in low):
            header_idx = i
            for j, c in enumerate(low):
                cols[c] = j
            break
    if header_idx is None:
        raise SystemExit(
            "ไม่พบตารางรายการดีลในรายงาน\n"
            "  -> ต้องเป็นไฟล์ 'ReportTester-xxxx.htm' ที่ Strategy Tester สร้าง\n"
            "     (คลิกขวาในแท็บ Backtest -> Report -> Save as Report)\n"
            "     ไม่ใช่ไฟล์ Optimization และไม่ใช่ภาพหน้าจอ"
        )

    ncol = len(rows[header_idx])
    deals = []
    for r in rows[header_idx + 1:]:
        if len(r) < ncol - 2:
            if deals:
                break
            continue
        t = parse_time(r[cols.get("time", 0)])
        if t is None:
            if deals:
                break
            continue
        get = lambda name: r[cols[name]] if name in cols and cols[name] < len(r) else ""
        deals.append({
            "time": t,
            "type": get("type").lower(),
            "dir": get("direction").lower(),
            "volume": to_num(get("volume")),
            "commission": to_num(get("commission")) or 0.0,
            "swap": to_num(get("swap")) or 0.0,
            "profit": to_num(get("profit")),
            "balance": to_num(get("balance")),
        })
    if not deals:
        raise SystemExit("พบหัวตารางแต่ไม่มีแถวข้อมูล — รายงานนี้อาจไม่มีไม้เลย")
    return deals


# ------------------------------------------------------------------ สถิติ
def summarize(deals):
    closes = [d for d in deals if d["dir"].startswith("out") and d["profit"] is not None]
    pnl = [d["profit"] + d["commission"] + d["swap"] for d in closes]
    times = [d["time"] for d in closes]

    bal_pts = [(d["time"], d["balance"]) for d in deals if d["balance"] is not None]
    start_bal = bal_pts[0][1] if bal_pts else 0.0
    balances = [b for _, b in bal_pts]

    peak, maxdd, maxdd_pct = -1e18, 0.0, 0.0
    dd_series = []
    for b in balances:
        peak = max(peak, b)
        dd = peak - b
        dd_series.append(dd / peak * 100 if peak > 0 else 0.0)
        if dd > maxdd:
            maxdd, maxdd_pct = dd, (dd / peak * 100 if peak > 0 else 0.0)

    wins = [p for p in pnl if p > 0]
    losses = [p for p in pnl if p < 0]
    gross_w, gross_l = sum(wins), -sum(losses)

    return {
        "closes": closes, "pnl": pnl, "times": times,
        "bal_times": [t for t, _ in bal_pts], "balances": balances,
        "dd_series": dd_series,
        "start_balance": start_bal,
        "end_balance": balances[-1] if balances else 0.0,
        "net": sum(pnl),
        "trades": len(pnl),
        "win_rate": len(wins) / len(pnl) * 100 if pnl else 0.0,
        "pf": (gross_w / gross_l) if gross_l > 0 else float("inf"),
        "avg": sum(pnl) / len(pnl) if pnl else 0.0,
        "max_dd": maxdd, "max_dd_pct": maxdd_pct,
        "period": (min(times), max(times)) if times else None,
    }


def print_summary(s, gmt):
    p = s["period"]
    print("═" * 62)
    print("สรุปผล backtest")
    print("═" * 62)
    if p:
        print(f"  ช่วงเวลา        : {p[0]:%Y.%m.%d} ถึง {p[1]:%Y.%m.%d}  (เวลาเซิร์ฟเวอร์ GMT{gmt:+d})")
    print(f"  ทุนเริ่ม/จบ      : ${s['start_balance']:,.2f} -> ${s['end_balance']:,.2f}")
    print(f"  กำไรสุทธิ        : ${s['net']:+,.2f}")
    print(f"  Profit Factor   : {s['pf']:.3f}")
    print(f"  จำนวนไม้         : {s['trades']}")
    print(f"  อัตราชนะ         : {s['win_rate']:.1f}%")
    print(f"  กำไรต่อไม้       : ${s['avg']:+.3f}")
    print(f"  ติดลบลึกสุด      : ${s['max_dd']:,.2f}  ({s['max_dd_pct']:.1f}%)")
    print("═" * 62)


# ------------------------------------------------------------------ กราฟ
FG, GRID, POS, NEG, ACCENT = "#1a1a1a", "#d8d8d8", "#2e7d5b", "#b23b3b", "#2b6cb0"


def style(ax, title, xlabel="", ylabel=""):
    ax.set_title(title, fontsize=12, color=FG, pad=12)
    ax.set_xlabel(xlabel, fontsize=9, color=FG)
    ax.set_ylabel(ylabel, fontsize=9, color=FG)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=FG, labelsize=8)


def chart_equity(s, out):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True,
                                 gridspec_kw={"height_ratios": [3, 1]})
    a1.plot(s["bal_times"], s["balances"], color=ACCENT, linewidth=1.4)
    a1.axhline(s["start_balance"], color=FG, linewidth=0.8, linestyle="--", alpha=0.5)
    a1.fill_between(s["bal_times"], s["start_balance"], s["balances"],
                    where=[b >= s["start_balance"] for b in s["balances"]],
                    color=POS, alpha=0.15, interpolate=True)
    a1.fill_between(s["bal_times"], s["start_balance"], s["balances"],
                    where=[b < s["start_balance"] for b in s["balances"]],
                    color=NEG, alpha=0.15, interpolate=True)
    style(a1, f"เส้นทุน   สุทธิ ${s['net']:+,.2f}  ·  PF {s['pf']:.2f}  ·  "
              f"{s['trades']} ไม้  ·  ชนะ {s['win_rate']:.1f}%", ylabel="Balance ($)")

    a2.fill_between(s["bal_times"], 0, s["dd_series"], color=NEG, alpha=0.35)
    a2.plot(s["bal_times"], s["dd_series"], color=NEG, linewidth=0.9)
    a2.invert_yaxis()
    style(a2, "", xlabel="", ylabel="Drawdown (%)")
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def chart_monthly(s, out):
    buckets = {}
    for t, p in zip(s["times"], s["pnl"]):
        buckets.setdefault(f"{t:%Y-%m}", 0.0)
        buckets[f"{t:%Y-%m}"] += p
    keys = sorted(buckets)
    vals = [buckets[k] for k in keys]

    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.bar(keys, vals, color=[POS if v >= 0 else NEG for v in vals], width=0.65)
    ax.axhline(0, color=FG, linewidth=0.9)
    for k, v in zip(keys, vals):
        ax.annotate(f"{v:+.0f}", (k, v), ha="center", fontsize=7, color=FG,
                    va="bottom" if v >= 0 else "top",
                    xytext=(0, 3 if v >= 0 else -3), textcoords="offset points")
    style(ax, "กำไร/ขาดทุน รายเดือน", ylabel="$")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def chart_by_hour(s, out, gmt):
    """กราฟสำคัญที่สุดสำหรับปัญหา DST — ขอบมาจากชั่วโมงไหนกันแน่"""
    tot = [0.0] * 24
    cnt = [0] * 24
    for t, p in zip(s["times"], s["pnl"]):
        tot[t.hour] += p
        cnt[t.hour] += 1

    fig, ax = plt.subplots(figsize=(11, 4.6))
    xs = list(range(24))
    ax.bar(xs, tot, color=[POS if v >= 0 else NEG for v in tot], width=0.7)
    ax.axhline(0, color=FG, linewidth=0.9)
    for h in xs:
        if cnt[h]:
            ax.annotate(f"{cnt[h]}", (h, tot[h]), ha="center", fontsize=7,
                        color=FG, alpha=0.75,
                        va="bottom" if tot[h] >= 0 else "top",
                        xytext=(0, 3 if tot[h] >= 0 else -3), textcoords="offset points")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{h:02d}" for h in xs], fontsize=7)
    style(ax, f"กำไรแยกตามชั่วโมงที่ปิดไม้ (เวลาเซิร์ฟเวอร์ GMT{gmt:+d})  "
              f"— ตัวเลขบนแท่ง = จำนวนไม้", xlabel="ชั่วโมง (เซิร์ฟเวอร์)", ylabel="$")

    sec = ax.secondary_xaxis("top")
    sec.set_xticks(xs)
    sec.set_xticklabels([f"{(h - gmt) % 24:02d}" for h in xs], fontsize=7)
    sec.set_xlabel("ชั่วโมง (UTC)", fontsize=9, color=FG)
    sec.tick_params(colors=FG)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def chart_dist(s, out):
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.hist(s["pnl"], bins=45, color=ACCENT, alpha=0.85, edgecolor="white", linewidth=0.4)
    ax.axvline(0, color=FG, linewidth=1.0)
    ax.axvline(s["avg"], color=POS if s["avg"] >= 0 else NEG, linewidth=1.4,
               linestyle="--", label=f"เฉลี่ย ${s['avg']:+.3f}")
    ax.legend(fontsize=8, frameon=False, labelcolor=FG)
    style(ax, "การกระจายกำไรต่อไม้", xlabel="$ ต่อไม้", ylabel="จำนวนไม้")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="สร้างกราฟจากรายงาน Strategy Tester ของ MT5")
    ap.add_argument("report", help="ไฟล์ ReportTester-xxxx.htm หรือ deals.csv จาก ea_backtest_engine.py")
    ap.add_argument("-o", "--outdir", default="charts", help="โฟลเดอร์ผลลัพธ์")
    ap.add_argument("--server-gmt", type=int, default=0,
                    help="เขตเวลาเซิร์ฟเวอร์ (ใช้ใส่แกน UTC ในกราฟชั่วโมง)")
    args = ap.parse_args()

    if args.report.lower().endswith(".csv"):
        import csv as _csv
        with open(args.report, newline="", encoding="utf-8-sig") as fh:
            rows = [r for r in _csv.reader(fh) if any(c.strip() for c in r)]
    else:
        parser = TableGrab()
        parser.feed(read_text(args.report))
        rows = parser.rows
    stats = summarize(extract_deals(rows))
    print_summary(stats, args.server_gmt)

    os.makedirs(args.outdir, exist_ok=True)
    jobs = [
        ("1_equity.png", lambda p: chart_equity(stats, p)),
        ("2_monthly.png", lambda p: chart_monthly(stats, p)),
        ("3_by_hour.png", lambda p: chart_by_hour(stats, p, args.server_gmt)),
        ("4_dist.png", lambda p: chart_dist(stats, p)),
    ]
    for name, fn in jobs:
        path = os.path.join(args.outdir, name)
        fn(path)
        print(f"  เขียนกราฟ: {path}")


if __name__ == "__main__":
    sys.exit(main())
