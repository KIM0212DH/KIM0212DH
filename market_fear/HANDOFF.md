# 인수인계 노트 — 공포지수와 매수 타이밍 (새 세션용)

마지막 갱신: 2026-10-15. 새 세션에서 작업을 이어갈 때 **이 문서를 먼저 읽으세요.**
자격 증명(아이디·비밀번호·API 키)의 **값**은 어디에도 출력·로그·커밋·대시보드에 넣지 않습니다. 설정 여부만 확인합니다.

---

## 1. 목표

- 연구 질문: **장기 투자 시, 공포지수(내재변동성)가 높을 때 사면 상대적 저점 매수인가?**
- 대응 관계: **나스닥 ↔ VIX / VXN**, **코스피 ↔ VKOSPI**.
- 과거 데이터 분석 + 가능한 한 최신(자동 갱신) 데이터.
- 사용자: 한국어 설명, 근거·출처 중심, 약어 풀이 필요.

## 2. 현재 상태

| 항목 | 상태 |
|---|---|
| VIX·VXN·나스닥·코스피 | 완료. Yahoo Finance(yfinance)로 수집 |
| VKOSPI | **대기**. KRX Open API 인증키 발급 대기 중. 코드는 준비됨, 실데이터로 실행한 적 없음 |
| 대시보드 | https://claude.ai/artifact/NjvX1QhNC72LrCMye8HNzD (Dashboard 타입 Artifact) |
| 브랜치 | `claude/vix-nasdaq-kospi-comparison-q1ujie` (PR 없음, 만들지 말 것: 사용자 요청 전까지) |

### 저장소 파일 (`market_fear/`)

| 파일 | 내용 |
|---|---|
| `vix_nasdaq_kospi.py` | 메인. yfinance로 ^VIX, ^VXN, ^IXIC, ^KS11 수집 → CSV + Plotly HTML. `--vkospi`로 VKOSPI 병합 |
| `krx_vkospi.py` | VKOSPI 수집 (KRX Open API). 캐시 CSV, 공식값 검증 |
| `data/closes_5y.csv` | 최근 5년 (열: Date, VIX, VXN, NASDAQ, KOSPI) |
| `data/closes_long.csv` | **대시보드가 쓰는 데이터.** VIX·나스닥 1990-01-02~, VXN 2001-01-23~, 코스피 1996-12-11~ |
| `data/vkospi.csv` | (아직 없음) VKOSPI 캐시. 생기면 커밋 |
| `dashboard/index.html` | 대시보드 페이지 원본 백업 (Artifact `files/index.html`과 동일하게 유지) |
| `KRX_SETUP.md` | 사용자용 키·도메인 등록 복사·붙여넣기 안내 |
| `requirements.txt` | yfinance, pandas, plotly, requests |
| `../.github/workflows/market-data.yml` | Actions 수집·커밋 워크플로 |

## 3. 환경 설정 (이름만, 값 금지)

| 위치 | 이름 | 용도 | 상태 |
|---|---|---|---|
| 클라우드 환경 변수 | `KRX_API_KEY` | KRX Open API 인증키 | 사용자가 발급 신청함 (2026-10-15) |
| 클라우드 환경 변수 | `KRX_ID`, `KRX_PW` | KRX 웹 로그인 (pykrx) | **사용 안 함** (§5-1). 삭제 권장 안내함 |
| 네트워크 허용 도메인 | Yahoo Finance 관련 | yfinance | 허용됨 |
| 네트워크 허용 도메인 | `data-dbg.krx.co.kr` | **KRX Open API 실제 호출 주소** | **미허용 (2026-10-15에 프록시 403)**. 사용자에게 추가 요청함 |
| 네트워크 허용 도메인 | `openapi.krx.co.kr` | KRX Open API 포털 | 접속됨 |
| 네트워크 허용 도메인 | `data.krx.co.kr` | KRX 정보데이터시스템 (웹) | 허용돼 있으나 **이 IP는 차단됨** (§5-1) |
| GitHub Actions Secret | `KRX_API_KEY` | Actions에서 VKOSPI 수집 | 사용자 등록 필요 |

환경 설정 변경은 **새 세션부터** 적용됩니다. 환경 관련 문제는 `read_documentation` 도구(environment.secrets / environment.network)로 최신 절차를 확인하고 안내하세요.

## 4. 데이터 출처별 핵심 사실

### Yahoo Finance (yfinance)
- 티커: `^VIX` (CBOE VIX, S&P 500 옵션), `^VXN` (CBOE 나스닥100 변동성, 2001-01-23~), `^IXIC` (나스닥 종합), `^KS11` (코스피, 1996-12-11~).
- **장중에 받으면 마지막 행이 종가가 아님.** 2026-10-15 행의 VIX·나스닥은 미국장 개장 직후 장중 값이고, VXN은 빈칸이었음. 코스피는 확정 종가.
- 휴장일은 CSV에서 빈칸(보정하지 않음). 한·미 휴장일이 다르므로 수익률은 각 지수의 실제 거래일 기준으로 계산.

### KRX Open API (VKOSPI)
- 엔드포인트: `GET https://data-dbg.krx.co.kr/svc/apis/idx/drvprod_dd_trd?basDd=YYYYMMDD` ('파생상품지수 시세정보').
  - **출처 주의**: 공식 문서로 직접 확인하지 못했고, 커뮤니티 구현 https://github.com/RealYoungk/openkrx-mcp (`src/openkrx_mcp/client.py`)에서 확인. 키 승인 후 실제 응답으로 꼭 검증할 것.
- 인증: `AUTH_KEY`. 우리 코드는 **헤더**로 보냄. 커뮤니티 구현은 쿼리 파라미터로 보냄. 401/403이면 쿼리 방식도 시도해 볼 것(단, URL에 키가 남으니 오류 메시지·로그에 URL을 출력하지 말 것).
- 응답 필드 가정: `OutBlock_1` 배열, 지수명 `IDX_NM`, 종가 `CLSPRC_IDX`. **실제 응답으로 확인되지 않음.** 코드는 이름에 "변동성"과 "200"이 들어간 행을 찾고, 필드를 못 찾으면 받은 필드 목록을 담아 중단하도록 작성됨.
- 기준일 하루당 요청 1번. 전 거래일까지만 제공(실시간 아님). 08:00 KST 무렵 갱신(커뮤니티 문서 기준). 일일 호출 한도가 있는 것으로 알려짐(커뮤니티 문서상 10,000).
- 서비스별 이용 신청이 따로 필요(지수 → 파생상품지수 시세정보).
- VKOSPI 공식 발표 시작: 2009-04-13. 코드에서 이전 날짜는 요청하지 않음(`FIRST_DAY`).
- **검증 기준값 (반드시 확인)**: 2026-06-09 종가 **91.23**, 2026-06-29 종가 **96.94** (공식 발표 이후 최고). 불일치하면 저장하지 말고 중단.

## 5. 이번 작업에서 놓쳤던 점·수정한 점 (교훈)

1. **KRX 웹 로그인(pykrx) 방식은 쓰면 안 됨.**
   - pykrx 1.2.9는 `KRX_ID`/`KRX_PW`가 있으면 **import 시점에 자동 로그인**하고, 콘솔에 로그인 ID를 출력함. 그 결과 이 세션 콘솔에 ID가 찍혔음(파일·커밋에는 없음). → pykrx를 다시 import하지 말 것.
   - 로그인 응답이 JSON이 아니라 `blockError_01.jsp`(차단 안내 페이지)였음. 내용: 이용약관 제10조 제2호(자동화 수단 수집 금지) 위반 탐지, IP 1일 차단, 해제 후에도 자동 수집 금지, 공식 경로(화면 다운로드·데이터 상품·Open API) 이용 권고.
   - 원인은 비밀번호 문제가 아니라 **IP 차단 + 약관상 금지**. 우회 시도 금지.
2. **yfinance 병렬 다운로드 버그로 CSV가 덮어써짐.**
   - 증상: `OperationalError('database is locked')`(yfinance 시간대 캐시 sqlite 잠금) → `^IXIC`가 통째로 빠진 채 CSV 저장, 이후 차트 단계에서 IndexError.
   - 수정: `yf.download(..., threads=False)`, 한 종목이라도 전부 비면 **CSV를 쓰기 전에** `SystemExit`. 망가진 CSV는 `git checkout`으로 복구했음.
3. **`market_fear/.gitignore`가 `*.csv`, `*.html`을 무시함.**
   - 데이터 CSV는 `git add -f`로 추가해야 함(워크플로도 `-f` 사용). `closes_long.csv`가 첫 커밋에서 빠졌다가 다시 추가했음.
   - `dashboard/index.html`은 `.gitignore`에 `!dashboard/index.html` 예외를 추가했음.
4. **GitHub Actions가 같은 브랜치에 데이터 커밋을 푸시함.**
   - 워크플로는 `market_fear/vix_nasdaq_kospi.py`, `krx_vkospi.py`, 워크플로 파일이 바뀐 push에 트리거되고, 실행 후 "Update market data" 커밋을 푸시함.
   - 그래서 내 다음 push가 non-fast-forward로 거절됐음. → **push 전 항상 `git fetch` + merge(또는 `git pull`)**. CSV 충돌이 나면 로컬에서 스크립트를 다시 실행해 재생성.
   - 예약 실행(`schedule`, 평일 23:30 UTC = 08:30 KST)은 GitHub 규칙상 **기본 브랜치에서만** 동작. 현재 브랜치에서는 push·수동 실행만 됨.
5. **표본 기간이 결론을 뒤집음.**
   - 최근 5년만 보면 VIX 상위 20% 구간의 1년 수익률이 가장 낮았음(2022 하락장 편중). 1990년부터 보면 가장 높음. → 대시보드를 장기 데이터(`closes_long.csv`)로 전환했음.
6. **차트 시작일 처리.** VXN(2001~)·VKOSPI(2009~)가 늦게 시작해서 `raw.ffill().dropna()`가 앞쪽 기간을 다 잘라냄. → `dropna(subset=["VIX","NASDAQ","KOSPI"])`로 수정.
7. **Write 도구 실패.** 셸(python)로 수정한 파일을 Write로 덮어쓰려 하면 "modified since read"로 거부됨. → 먼저 Read하고 Write.
8. **Python 출력을 `| head`로 자르면 BrokenPipeError**가 남(스크립트 마지막 print). CSV·HTML은 이미 저장된 상태라 무해하지만 혼동 주의.
9. **KRX 실제 호출 도메인이 포털과 다름.** `openapi.krx.co.kr`(포털)만 허용해서는 안 되고 `data-dbg.krx.co.kr`가 필요함. 처음 안내에서 빠졌다가 보완했음.

## 6. 대시보드 운영법

Dashboard 타입 Artifact이며, 내용은 Artifact의 자체 저장소 문서로 관리함(`ArtifactData` 도구). **수정 전 반드시** `Artifact` `action: "read"`(url)로 타입 지침을 읽고, 바꿀 문서를 `ArtifactData get`으로 읽은 뒤 `if_version`을 붙여 씀.

| 문서 | 내용 | 마지막 버전 |
|---|---|---|
| `dash/meta` | `{title: "공포지수와 매수 타이밍"}` | 2 |
| `datasets/prices` | file source, `closes_long.csv` blob `/_blob/64b36ca79cd9a57415c1a3d3de7a27ad` | 4 |
| `files/index.html` | 페이지 (`market_fear/dashboard/index.html`과 동일) | 4 |

- **새 CSV 반영 절차**: `Artifact publish`(url, file_path, `asset: true`)로 업로드 → 결과의 `/_blob/<id>`로 `datasets/prices`의 `source.url`·`name`·`updated{at,by}`·`description`을 update.
- **페이지 수정 절차**: `dashboard/index.html` 수정 → `{"text": <전체 HTML>}` JSON 파일 생성 → `files/index.html` update(file_path, if_version) → 저장소에도 커밋.
- 페이지 규칙(타입 지침): 숫자는 마크업에 직접 쓰지 않고 데이터셋/`dash.calc`에서 채움. 값을 보여주는 요소는 `data-source`/`data-field`/`data-where`로 표시. 표는 `data-row-key` + `<tr data-key>`. 외부 스크립트·네트워크 불가, d3 v7 전역 사용.
- 타입 지침상 대시보드 렌더링·스크린샷 검증은 사용자 요청 없이 하지 않음. 대신 calc 로직은 `<script>`를 추출해 node로 문법 검사(`node --check`) + 실제 CSV로 계산을 돌려 Python 결과와 대조했음.
- 계산(dash.calc):
  - `latest`: 지수별 마지막 두 거래일 → close, chg (VKOSPI는 열이 있을 때만).
  - `fear`: VIX·VXN·VKOSPI 각각 전체 기간 5분위 경계(q20~q80), min/max, 마지막 값의 분위(pct), start/end.
  - `fwd`: 공포 구간별 21/63/126/252 거래일 뒤 평균 수익률, 1년 뒤 상승 비율, 표본(n = 3개월 수익률 일수). key는 `VIX-Q1`…`VIX-Q5`, `VIX-all`, `VXN-…`, VKOSPI 데이터가 없으면 `VKOSPI-wait`.
  - `corr`: 일간 변화율 피어슨 상관(한국 지표 1일 지연 포함).
- 화면 구성: 상단 차트 기간 버튼(1년/5년/10년/전체) → 나스닥 섹션(VIX/VXN 전환 버튼, 타일 3개, 위아래 연동 차트에 상위 20% 음영, 구간별 수익률 표) → 코스피×VKOSPI 섹션(현재 "대기") → 표 읽는 법과 한계 → VIX vs VKOSPI 같은 축 차트(2026년 6월 음영) → 상관계수 → 용어.
- **VKOSPI가 들어오면 페이지 수정은 필요 없음**: CSV에 `VKOSPI` 열만 생기면 타일·차트·표·상관이 자동으로 채워지도록 작성됨.
- 더 이상 참조되지 않는 옛 asset: `1d13931340378bf8ed6b52513675691e`, `6643c3eeb4d5f52bad520ba91ba3cbea`, `8bffa6637f56d8db4a601d8d4b6d73a8`. 삭제는 사용자 확인 후에만.

## 7. 분석 결과 요약 (사용자에게 보고한 내용)

나스닥, 공포지수 5분위별 "그날 종가에 사서 1년 보유" 평균 수익률(배당 제외)과 1년 뒤 상승 비율:

| 구간 | VIX (1990~2026) | VXN (2001~2026) | VIX를 2001~로 제한 |
|---|---|---|---|
| 하위 20% | +14.9% / 86% | +14.3% / 85% | +13.2% / 85% |
| 2분위 | +16.4% / 89% | +13.5% / 85% | +15.2% / 86% |
| 3분위 | +11.8% / 81% | +11.1% / 78% | +9.9% / 76% |
| 4분위 | +8.1% / 67% | +8.8% / 74% | +3.9% / 63% |
| 상위 20% | **+23.7% / 77%** | **+16.0% / 67%** | **+21.8% / 79%** |
| 전체 | +15.0% / 80% | +12.9% / 78% | +12.9% / 78% |

- VIX 상위 20% 경계 24.2, VXN 상위 20% 경계 30.6. VIX≥30: 736일, 1년 평균 +36.1%, 상승 88%. VIX≥40: 208일, +50.3%, 98%.
- VIX 상위 20%의 연대별 1년 평균: 1990년대 +49%, 2000년대 +10%, 2010년대 +20%, 2020년대 +28%.
- 최근 5년(2021-10~)만: VIX 상위 20% 1년 +14.3%(전체 +18.8%), 상승 74%. 상위 20% 251일 중 170일이 2022년.
- 같은 날 상관: VIX↔나스닥 −0.645, VXN↔나스닥 −0.687 (1990/2001~).
- 해석 요지: (1) 평균은 가설 지지, (2) 상승 비율은 오히려 낮아 위험 대가형 보상, (3) 4분위(애매한 공포)가 최악, (4) VXN 상위 구간에는 2001~02 닷컴 붕괴가 많이 포함돼 신호가 약함, (5) 독립 사례가 적어(겹치는 보유 기간, 사건 군집) 통계적 확신은 제한적.
- 관련 문헌(기억 기반, 원문 확인 권장): Giot (2005, *Journal of Portfolio Management*), Banerjee·Doran·Peterson (2007, *Journal of Banking & Finance*), Bollerslev·Tauchen·Zhou (2009, *Review of Financial Studies*).
- 이전 분석: 2026년 코스피 연율 변동성 61%, 고점 9,115(2026-06-22) 대비 −39%. 같은 기간 VIX 평균 약 18로 안정 → 한국 고유 리스크. 2026-10-15 코스피 −7.6%(5,554.22).

## 8. 남은 작업

1. 사용자가 `KRX_API_KEY` 등록 + `data-dbg.krx.co.kr` 허용 → **새 세션**에서:
   ```
   cd market_fear
   pip install -r requirements.txt
   python krx_vkospi.py --start 2009-04-13 --csv data/vkospi.csv     # 검증 91.23 / 96.94
   python vix_nasdaq_kospi.py --start 1990-01-01 --vkospi --csv data/closes_long.csv --out /tmp/long.html
   python vix_nasdaq_kospi.py --period 5y --vkospi --csv data/closes_5y.csv --out /tmp/5y.html
   ```
   - 첫 실행 시 응답 필드명이 가정과 다르면 `krx_vkospi.py`의 `NAME_KEYS`/`CLOSE_KEYS`를 실제 값으로 수정.
   - 성공하면 `git add -f data/vkospi.csv data/closes_*.csv` → 커밋 → fetch/merge → push.
2. 대시보드: 새 `closes_long.csv`를 asset 업로드하고 `datasets/prices`를 update(§6). 설명(description)에서 "VKOSPI 대기" 문구를 바꾸고 출처(KRX Open API)를 추가.
3. 사용자 보고: VKOSPI 구간별 수익률, 현재 VKOSPI의 분위(10/15 코스피 −7.6% 급락일), VIX vs VKOSPI 2026년 6월 비교.
4. (선택) 실시간: 증권사 API(예: 한국투자증권 KIS Developers) 검토. KRX Open API는 일별·전일 기준이라 실시간이 아님.
5. (선택) 워크플로 예약 실행을 쓰려면 기본 브랜치 병합 필요. 사용자 결정 사항.

## 9. 새 세션 시작 체크리스트

1. `git fetch origin claude/vix-nasdaq-kospi-comparison-q1ujie && git checkout claude/vix-nasdaq-kospi-comparison-q1ujie && git pull` (Actions 커밋 반영).
2. 환경 변수 설정 여부만 확인: `[ -n "$KRX_API_KEY" ] && echo set` (값 출력 금지).
3. 도메인 확인: `curl -sS -o /dev/null -w "%{http_code}" "https://data-dbg.krx.co.kr/svc/apis/idx/drvprod_dd_trd?basDd=20260629"` → 프록시 403이면 아직 미허용.
4. `pip install -r market_fear/requirements.txt` (pykrx는 설치·import하지 말 것).
5. 대시보드 수정 전 `Artifact read` → `ArtifactData get`으로 현재 버전 확인.
6. 사용자에게는 한국어, 근거 중심, 약어 풀이.
