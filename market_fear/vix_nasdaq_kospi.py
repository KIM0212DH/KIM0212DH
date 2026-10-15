"""VIX(공포지수) · 나스닥 종합 · 코스피 지수를 한 화면에서 비교하는 인터랙티브 차트.

사용법:
    pip install -r requirements.txt
    python vix_nasdaq_kospi.py                 # 최근 5년
    python vix_nasdaq_kospi.py --period 1y     # 최근 1년
    python vix_nasdaq_kospi.py --start 2020-01-01 --end 2020-12-31
    python vix_nasdaq_kospi.py --vkospi        # VKOSPI 추가 (KRX_API_KEY 필요)

결과: vix_nasdaq_kospi.html (브라우저로 열기, 줌/호버 가능)

데이터: Yahoo Finance (yfinance)
    ^VIX  : CBOE Volatility Index
    ^IXIC : NASDAQ Composite
    ^KS11 : KOSPI Composite
    VKOSPI: KRX Open API (krx_vkospi.py, 인증키 KRX_API_KEY)
"""

import argparse

import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from plotly.subplots import make_subplots

from krx_vkospi import load_vkospi, verify

TICKERS = {"^VIX": "VIX", "^IXIC": "NASDAQ", "^KS11": "KOSPI"}
COLORS = {"VIX": "#d62728", "NASDAQ": "#1f77b4", "KOSPI": "#2ca02c", "VKOSPI": "#9467bd"}
# VIX 해석 구간 (관행적 기준선)
VIX_LEVELS = [(20, "20: 경계"), (30, "30: 공포")]


def load_closes(period, start, end):
    kwargs = {"start": start, "end": end} if start else {"period": period}
    # threads=False: 병렬 다운로드 시 yfinance 캐시(sqlite) 잠금으로 한 종목이 통째로 빠지는 문제 방지
    raw = yf.download(list(TICKERS), auto_adjust=True, progress=False, threads=False, **kwargs)
    closes = raw["Close"].rename(columns=TICKERS)[list(TICKERS.values())]
    missing = [c for c in closes if closes[c].isna().all()]
    if missing:
        raise SystemExit(f"다운로드 실패: {missing} — CSV를 덮어쓰지 않고 종료합니다.")
    return closes.dropna(how="all")


def correlation_report(closes):
    """일간 변화율 기준 상관계수.

    코스피는 미국장 개장 전에 마감하므로, 미국 t일 움직임은 코스피 t+1일에 반영된다.
    그래서 동일일(lag 0)과 코스피 1일 지연(lag 1) 상관을 함께 본다.
    """
    # 휴장일 0% 수익률이 섞이지 않도록 각 지수의 실제 거래일 기준으로 수익률 계산
    r = pd.DataFrame({c: closes[c].dropna().pct_change() for c in closes})
    kospi_next = r["KOSPI"].dropna().shift(-1).reindex(r.index)
    rows = [
        ("VIX vs NASDAQ (동일일)", r["VIX"].corr(r["NASDAQ"])),
        ("VIX vs KOSPI (동일일)", r["VIX"].corr(r["KOSPI"])),
        ("VIX(t) vs KOSPI(t+1)", r["VIX"].corr(kospi_next)),
        ("NASDAQ vs KOSPI (동일일)", r["NASDAQ"].corr(r["KOSPI"])),
        ("NASDAQ(t) vs KOSPI(t+1)", r["NASDAQ"].corr(kospi_next)),
    ]
    if "VKOSPI" in r:
        vkospi_next = r["VKOSPI"].dropna().shift(-1).reindex(r.index)
        rows += [
            ("VKOSPI vs KOSPI (동일일)", r["VKOSPI"].corr(r["KOSPI"])),
            ("VIX vs VKOSPI (동일일)", r["VIX"].corr(r["VKOSPI"])),
            ("VIX(t) vs VKOSPI(t+1)", r["VIX"].corr(vkospi_next)),
        ]
    return rows


def build_figure(closes, corr_rows):
    has_vkospi = "VKOSPI" in closes
    titles = ["VIX (공포지수)", "NASDAQ Composite", "KOSPI",
              "정규화 비교 (시작일 = 100, VIX는 우측 축)"]
    specs = [[{}], [{}], [{}], [{"secondary_y": True}]]
    heights = [0.22, 0.22, 0.22, 0.34]
    if has_vkospi:
        titles.append("VIX vs VKOSPI (같은 축, 연율 %)")
        specs.append([{}])
        heights = [0.17, 0.17, 0.17, 0.27, 0.22]
    fig = make_subplots(
        rows=len(titles), cols=1, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=heights, subplot_titles=titles, specs=specs,
    )

    for row, name in enumerate(["VIX", "NASDAQ", "KOSPI"], start=1):
        fig.add_trace(go.Scatter(x=closes.index, y=closes[name], name=name,
                                 line=dict(color=COLORS[name], width=1.5),
                                 legendgroup=name), row=row, col=1)

    for level, label in VIX_LEVELS:
        fig.add_hline(y=level, line=dict(color="gray", dash="dot", width=1),
                      annotation_text=label, annotation_position="top left",
                      row=1, col=1)

    norm = closes / closes.iloc[0] * 100
    for name in ["NASDAQ", "KOSPI"]:
        fig.add_trace(go.Scatter(x=norm.index, y=norm[name], name=f"{name} (정규화)",
                                 line=dict(color=COLORS[name], width=1.5),
                                 legendgroup=name, showlegend=False),
                      row=4, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=closes.index, y=closes["VIX"], name="VIX (우측 축)",
                             line=dict(color=COLORS["VIX"], width=1), opacity=0.5,
                             legendgroup="VIX", showlegend=False),
                  row=4, col=1, secondary_y=True)

    if has_vkospi:
        for name in ["VIX", "VKOSPI"]:
            fig.add_trace(go.Scatter(x=closes.index, y=closes[name], name=name,
                                     line=dict(color=COLORS[name], width=1.5),
                                     legendgroup=name, showlegend=name == "VKOSPI"),
                          row=5, col=1)

    corr_text = "<br>".join(f"{k}: {v:+.2f}" for k, v in corr_rows)
    fig.add_annotation(text="<b>일간 수익률 상관계수</b><br>" + corr_text,
                       xref="paper", yref="paper", x=1.0, y=1.08,
                       xanchor="right", yanchor="bottom", align="left",
                       showarrow=False, font=dict(size=11),
                       bordercolor="#ccc", borderwidth=1, bgcolor="white")

    start, end = closes.index[0].date(), closes.index[-1].date()
    fig.update_layout(
        title=f"VIX · NASDAQ · KOSPI ({start} ~ {end})",
        height=1400 if has_vkospi else 1100, hovermode="x unified", template="plotly_white",
        margin=dict(t=160),
    )
    fig.update_yaxes(title_text="NASDAQ·KOSPI", row=4, col=1, secondary_y=False)
    fig.update_yaxes(title_text="VIX", row=4, col=1, secondary_y=True)
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.04), row=len(titles), col=1)
    return fig


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--period", default="5y", help="예: 6mo, 1y, 5y, max (기본 5y)")
    p.add_argument("--start", help="시작일 YYYY-MM-DD (지정 시 --period 무시)")
    p.add_argument("--end", help="종료일 YYYY-MM-DD")
    p.add_argument("--out", default="vix_nasdaq_kospi.html")
    p.add_argument("--csv", help="종가 원본 데이터를 CSV로도 저장할 경로")
    p.add_argument("--vkospi", action="store_true",
                   help="VKOSPI 열 추가 (KRX Open API, 환경 변수 KRX_API_KEY 필요)")
    p.add_argument("--vkospi-cache", default="data/vkospi.csv",
                   help="VKOSPI 캐시 CSV (이미 받은 날짜는 다시 요청하지 않음)")
    args = p.parse_args()

    raw = load_closes(args.period, args.start, args.end)
    if args.vkospi:
        vkospi = load_vkospi(raw.index.min(), args.end, cache=args.vkospi_cache)
        if not verify(vkospi):
            raise SystemExit("VKOSPI가 공식 종가와 불일치 — 중단합니다.")
        raw = raw.join(vkospi, how="outer")
    corr_rows = correlation_report(raw)
    # 한·미 휴장일이 달라 날짜가 어긋나므로, 차트용으로는 직전 값으로 채움
    closes = raw.ffill().dropna()
    for k, v in corr_rows:
        print(f"{k:28s} {v:+.3f}")

    if args.csv:
        raw.to_csv(args.csv)  # 휴장일 미보정 원본 (빈 칸 = 해당 시장 휴장)
    build_figure(closes, corr_rows).write_html(args.out, include_plotlyjs="cdn")
    print(f"저장 완료: {args.out}")


if __name__ == "__main__":
    main()
