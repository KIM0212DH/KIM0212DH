"""VIX(공포지수) · 나스닥 종합 · 코스피 지수를 한 화면에서 비교하는 인터랙티브 차트.

사용법:
    pip install -r requirements.txt
    python vix_nasdaq_kospi.py                 # 최근 5년
    python vix_nasdaq_kospi.py --period 1y     # 최근 1년
    python vix_nasdaq_kospi.py --start 2020-01-01 --end 2020-12-31

결과: vix_nasdaq_kospi.html (브라우저로 열기, 줌/호버 가능)

데이터: Yahoo Finance (yfinance)
    ^VIX  : CBOE Volatility Index
    ^IXIC : NASDAQ Composite
    ^KS11 : KOSPI Composite
"""

import argparse

import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from plotly.subplots import make_subplots

TICKERS = {"^VIX": "VIX", "^IXIC": "NASDAQ", "^KS11": "KOSPI"}
COLORS = {"VIX": "#d62728", "NASDAQ": "#1f77b4", "KOSPI": "#2ca02c"}
# VIX 해석 구간 (관행적 기준선)
VIX_LEVELS = [(20, "20: 경계"), (30, "30: 공포")]


def load_closes(period, start, end):
    kwargs = {"start": start, "end": end} if start else {"period": period}
    raw = yf.download(list(TICKERS), auto_adjust=True, progress=False, **kwargs)
    closes = raw["Close"].rename(columns=TICKERS)[list(TICKERS.values())]
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
    return rows


def build_figure(closes, corr_rows):
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=[0.22, 0.22, 0.22, 0.34],
        subplot_titles=("VIX (공포지수)", "NASDAQ Composite", "KOSPI",
                        "정규화 비교 (시작일 = 100, VIX는 우측 축)"),
        specs=[[{}], [{}], [{}], [{"secondary_y": True}]],
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

    corr_text = "<br>".join(f"{k}: {v:+.2f}" for k, v in corr_rows)
    fig.add_annotation(text="<b>일간 수익률 상관계수</b><br>" + corr_text,
                       xref="paper", yref="paper", x=1.0, y=1.08,
                       xanchor="right", yanchor="bottom", align="left",
                       showarrow=False, font=dict(size=11),
                       bordercolor="#ccc", borderwidth=1, bgcolor="white")

    start, end = closes.index[0].date(), closes.index[-1].date()
    fig.update_layout(
        title=f"VIX · NASDAQ · KOSPI ({start} ~ {end})",
        height=1100, hovermode="x unified", template="plotly_white",
        margin=dict(t=160),
    )
    fig.update_yaxes(title_text="NASDAQ·KOSPI", row=4, col=1, secondary_y=False)
    fig.update_yaxes(title_text="VIX", row=4, col=1, secondary_y=True)
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.04), row=4, col=1)
    return fig


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--period", default="5y", help="예: 6mo, 1y, 5y, max (기본 5y)")
    p.add_argument("--start", help="시작일 YYYY-MM-DD (지정 시 --period 무시)")
    p.add_argument("--end", help="종료일 YYYY-MM-DD")
    p.add_argument("--out", default="vix_nasdaq_kospi.html")
    p.add_argument("--csv", help="종가 데이터를 CSV로도 저장할 경로")
    args = p.parse_args()

    raw = load_closes(args.period, args.start, args.end)
    corr_rows = correlation_report(raw)
    # 한·미 휴장일이 달라 날짜가 어긋나므로, 차트용으로는 직전 값으로 채움
    closes = raw.ffill().dropna()
    for k, v in corr_rows:
        print(f"{k:28s} {v:+.3f}")

    if args.csv:
        closes.to_csv(args.csv)
    build_figure(closes, corr_rows).write_html(args.out, include_plotlyjs="cdn")
    print(f"저장 완료: {args.out}")


if __name__ == "__main__":
    main()
