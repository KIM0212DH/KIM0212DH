"""VKOSPI(코스피200 변동성지수) 일별 종가를 KRX Open API로 받는다.

사용법:
    export KRX_API_KEY=...            # openapi.krx.co.kr 에서 발급한 인증키
    python krx_vkospi.py --start 2021-10-15 --csv data/vkospi.csv

API: KRX Open API '파생상품지수 시세정보' (idx/drvprod_dd_trd)
    - 기준일(basDd, YYYYMMDD) 하나당 요청 1번, 그날의 파생상품지수 전체가 온다.
    - 전 거래일 데이터까지만 제공(실시간 아님), 매일 08:00 KST 무렵 갱신.
    - 일일 호출 한도가 있으므로 --csv 캐시에 이미 있는 날짜는 다시 받지 않는다.

VKOSPI: 한국거래소가 2009-04-13부터 공식 발표. 코스피200 옵션 가격으로 계산한
향후 30일 기대변동성(연율, %).
"""

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://data-dbg.krx.co.kr/svc/apis/idx/drvprod_dd_trd"
NAME_KEYS = ("IDX_NM", "IDX_NM_KOR")
CLOSE_KEYS = ("CLSPRC_IDX", "CLSPRC", "TDD_CLSPRC")
# 공식 발표값으로 검증 (2026-06-29: 공식 발표 이후 최고치)
KNOWN_CLOSES = {"2026-06-09": 91.23, "2026-06-29": 96.94}
FIRST_DAY = "2009-04-13"  # VKOSPI 공식 발표 시작일: 이전 날짜는 요청하지 않음


def is_vkospi(name):
    name = name.replace(" ", "")
    return "변동성" in name and "200" in name


def fetch_day(session, api_key, day):
    """basDd 하루치 응답에서 VKOSPI 종가를 찾는다. 휴장일이면 None."""
    params = {"basDd": day.strftime("%Y%m%d")}
    resp = session.get(API_URL, params=params, headers={"AUTH_KEY": api_key}, timeout=30)
    if resp.status_code != 200:
        # raise_for_status()는 URL을 메시지에 넣으므로 쓰지 않는다(키 노출 방지)
        raise RuntimeError(f"KRX Open API {resp.status_code} ({day:%Y-%m-%d}): {resp.text[:200]}")
    rows = resp.json().get("OutBlock_1") or []
    for row in rows:
        name_key = next((k for k in NAME_KEYS if k in row), None)
        if name_key and is_vkospi(row[name_key]):
            close_key = next((k for k in CLOSE_KEYS if k in row), None)
            if close_key is None:
                raise RuntimeError(f"종가 필드를 찾지 못함. 응답 필드: {sorted(row)}")
            value = str(row[close_key]).replace(",", "").strip()
            return float(value) if value not in ("", "-") else None
    if rows:
        names = sorted({r.get(NAME_KEYS[0], "?") for r in rows})
        raise RuntimeError(f"응답에 VKOSPI가 없음. 받은 지수: {names[:20]}")
    return None


def load_vkospi(start, end=None, api_key=None, cache=None, pause=0.05):
    """start~end 영업일의 VKOSPI 종가 Series. cache CSV가 있으면 그 이후 날짜만 받는다."""
    api_key = api_key or os.getenv("KRX_API_KEY")
    if not api_key:
        sys.exit("KRX_API_KEY 환경 변수가 없습니다 (openapi.krx.co.kr 인증키).")

    cached = pd.Series(dtype=float, name="VKOSPI")
    if cache and Path(cache).exists():
        cached = pd.read_csv(cache, index_col=0, parse_dates=True)["VKOSPI"]

    start = max(pd.Timestamp(start), pd.Timestamp(FIRST_DAY))
    end = pd.Timestamp(end) if end else pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
    days = pd.bdate_range(start, end)
    if not cached.empty:
        days = days[days > cached.index.max()]

    fetched = {}
    with requests.Session() as session:
        for i, day in enumerate(days, 1):
            value = fetch_day(session, api_key, day)
            if value is not None:
                fetched[day] = value
            if i % 100 == 0:
                print(f"  {i}/{len(days)}일 조회 ({day:%Y-%m-%d})")
            time.sleep(pause)

    parts = [x for x in (cached, pd.Series(fetched, name="VKOSPI", dtype=float)) if not x.empty]
    series = pd.concat(parts).sort_index() if parts else cached
    series = series[~series.index.duplicated(keep="last")]
    series = series[series.index >= pd.Timestamp(start)]
    series.index.name = "Date"
    if cache:
        series.to_frame().to_csv(cache)
    return series


def verify(series):
    """알려진 공식 종가와 대조. 범위 안의 날짜만 검사."""
    ok = True
    for day, expected in KNOWN_CLOSES.items():
        if pd.Timestamp(day) not in series.index:
            continue
        got = series[pd.Timestamp(day)]
        match = abs(got - expected) < 0.005
        ok &= match
        print(f"  검증 {day}: {got:.2f} (기대 {expected:.2f}) {'OK' if match else '불일치'}")
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--start", default="2021-10-15")
    p.add_argument("--end", help="종료일 YYYY-MM-DD (기본: 어제)")
    p.add_argument("--csv", default="data/vkospi.csv", help="저장 겸 캐시 CSV")
    args = p.parse_args()

    series = load_vkospi(args.start, args.end, cache=args.csv)
    print(f"VKOSPI {len(series)}일: {series.index.min():%Y-%m-%d} ~ {series.index.max():%Y-%m-%d}")
    if not verify(series):
        sys.exit("공식 종가와 불일치 — 데이터를 확인하세요.")


if __name__ == "__main__":
    main()
