"""ทดสอบ invariant ของ tools/ladder_grid_sim.py (ตัวจำลองอ้างอิงของ XAU_LadderGrid.mq5)

รัน: python3 -m pytest tools/test_ladder_grid_sim.py -q
"""
import os
import sys
from dataclasses import replace

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ladder_grid_sim import (CONTRACT, Params, make_ticks, required_equity, scenarios,  # noqa: E402
                             simulate, size_lot, stop_distance, summarize, worst_case_per_lot)

BASE = 4200.0
H = 3600


def basket_lot(res, basket_id):
    return next(t["lot"] for t in res["trades"] if t["basket"] == basket_id)


# ------------------------------------------------------------------ ขนาดไม้
def test_default_grid_refuses_300_and_reports_required_equity():
    p = Params()
    assert size_lot(p, 300.0, 0.3) == 0.0
    worst_at_min_lot = worst_case_per_lot(p, 0.3) * 0.01
    assert worst_at_min_lot == pytest.approx(232.2, abs=0.5)
    assert 11_500 < required_equity(p, 0.01, 0.3, 2.0) < 11_700
    assert size_lot(p, 20_000.0, 0.3) == 0.01


def test_hard_cap_blocks_oversized_fixed_lot():
    p = Params(lot=0.09, max_total_lots=10.0)
    assert size_lot(p, 20_000.0, 0.3) == 0.0            # เสี่ยง ~10.4% > hard cap 10%
    assert size_lot(replace(p, lot=0.03), 20_000.0, 0.3) == 0.03


def test_single_order_grid_is_the_only_shape_that_fits_300():
    p = Params(max_levels=1, ladder=(1.0,), stop_buffer=10.0, risk_pct=5.0)
    assert size_lot(p, 300.0, 0.3) == 0.01


# ------------------------------------------------------------------ เพดานขาดทุน
@pytest.mark.parametrize("hours,move,seed", [(1, 60, 1), (3, 90, 2), (8, 180, 3), (2, 120, 4)])
def test_basket_loss_never_exceeds_worst_case_on_continuous_rally(hours, move, seed):
    p = Params(start_equity=20_000.0, daily_loss_pct=None, max_dd_pct=None, direction="sell")
    tk = make_ticks([(hours * H, BASE + move), (H, BASE + move)], seed=seed)
    res = simulate(*tk, p)
    assert res["baskets"], "ต้องมี basket อย่างน้อย 1 อัน"
    assert any(b["stopped"] for b in res["baskets"])
    for b in res["baskets"]:
        bound = basket_lot(res, b["id"]) * worst_case_per_lot(p, p.max_spread)
        assert b["pnl"] >= -bound - 1e-6, (b, bound)


def test_gap_through_stop_breaks_the_bound_as_documented():
    """ราคากระโดดทะลุ stop ใน tick เดียว: ขาดทุนเกินระยะ stop ตามขนาด gap (เพดานไม่คุ้มครอง gap)"""
    p = Params(start_equity=20_000.0, daily_loss_pct=None, max_dd_pct=None, direction="sell")
    times, bids, asks = make_ticks([(600, BASE + 6)], seed=5)
    last = times[-1]
    for k in range(1, 121):                              # กระโดดขึ้น +45 แล้วค้างไว้ 2 นาที
        times.append(last + k)
        bids.append(bids[-1] if k > 1 else BASE + 6 + 45 - 0.15)
        asks.append(asks[-1] if k > 1 else BASE + 6 + 45 + 0.15)
    res = simulate(times, bids, asks, p)
    first = res["baskets"][0]
    lot = basket_lot(res, first["id"])
    n = len(p.ladder)
    no_gap_loss = lot * n * stop_distance(p) * CONTRACT   # ถ้า stop ทำงานที่ราคา stop พอดี (ชั้น 0 ชั้นเดียว)
    assert first["stopped"]
    assert first["pnl"] < -no_gap_loss


# ------------------------------------------------------------------ โครงสร้าง basket
def test_levels_open_once_and_caps_hold():
    p = Params(start_equity=20_000.0)
    n = len(p.ladder)
    for name, seg in scenarios().items():
        res = simulate(*make_ticks(seg), p)
        assert res["max_open_pos"] <= n * p.max_levels, name
        assert res["max_open_lots"] <= p.max_total_lots + 1e-9, name
        groups = {}
        for t in res["trades"]:
            groups.setdefault((t["basket"], t["level"]), []).append(t)
        for (bid_, level), items in groups.items():
            assert level <= p.max_levels - 1
            assert len(items) == n, (name, bid_, level)   # ชั้นหนึ่งเปิด order ครบ n ตัวครั้งเดียว


def test_tp_ladder_prices_on_reversion():
    p = Params(start_equity=20_000.0, direction="sell")
    res = simulate(*make_ticks(scenarios()["reversion (ยืดแล้วดึงกลับ)"]), p)
    tps = [t for t in res["trades"] if t["why"] == "TP"]
    assert tps and all(t["why"] == "TP" for t in res["trades"])
    for t in tps:
        dist = t["entry"] - t["exit"]
        assert any(dist == pytest.approx(m * p.step, abs=1e-6) for m in p.ladder), dist
    assert summarize(res)["net"] > 0


def test_baskets_do_not_overlap_and_respect_cooldown():
    p = Params(start_equity=20_000.0)
    res = simulate(*make_ticks(scenarios()["rally_long (ไล่ขึ้น 180 ใน 8 ชม.)"]), p)
    bk = res["baskets"]
    assert len(bk) >= 2
    for a, b in zip(bk, bk[1:]):
        assert b["open_t"] >= a["close_t"] + p.cooldown_sec - 1e-9


# ------------------------------------------------------------------ ความถูกต้องของตรรกะ
def test_no_lookahead_prefix_invariance():
    p = Params(start_equity=20_000.0)
    tk = make_ticks(scenarios()["drop_day (ขึ้น 15 แล้วร่วง 140)"], seed=7)
    cut = 43200 + 9000            # หลังช่วงอุ่นเครื่อง: basket เปิดแล้วและราคาเริ่มร่วง
    full = simulate(*tk, p)
    part = simulate(tk[0][:cut], tk[1][:cut], tk[2][:cut], p)
    t_cut = tk[0][cut - 1]

    def opens(res):
        return sorted({(t["open_t"], t["dir"], t["level"], t["entry"]) for t in res["trades"] if t["open_t"] <= t_cut})
    assert opens(full) == opens(part)
    assert opens(full)


def test_buy_sell_mirror_symmetry():
    seg = scenarios()["rally (ไล่ขึ้น 90 ใน 3 ชม.)"]
    times, bids, asks = make_ticks(seg, seed=11, spread=0.0)   # spread 0: กระจกภาพสมมาตรแบบตรงตัว
    m_bids = [2 * BASE - a for a in asks]
    m_asks = [2 * BASE - b for b in bids]
    base = Params(start_equity=20_000.0, daily_loss_pct=None, max_dd_pct=None)
    a = simulate(times, bids, asks, replace(base, direction="sell"))
    b = simulate(times, m_bids, m_asks, replace(base, direction="buy"))
    assert len(a["trades"]) == len(b["trades"]) > 0
    assert a["balance"] == pytest.approx(b["balance"], abs=1e-6)


def test_daily_loss_guard_halts_and_limits_drawdown():
    p = Params(start_equity=20_000.0, daily_loss_pct=1.0, max_dd_pct=None, direction="sell")
    # warm-up 12 ชม. เริ่ม 08:00 UTC -> rally 2 ชม. + ค้าง 1 ชม. จบ 23:00 UTC ยังอยู่วันเดียวกัน
    res = simulate(*make_ticks([(2 * H, BASE + 120), (H, BASE + 120)], seed=3), p)
    assert res["n_halts"] >= 1
    assert res["max_dd_pct"] < 1.3
