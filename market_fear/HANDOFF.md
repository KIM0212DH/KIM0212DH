# 인수인계 노트 — 공포지수와 매수 타이밍 (새 세션용)

마지막 갱신: 2026-10-16. 새 세션에서 작업을 이어갈 때 **이 문서를 먼저 읽으세요.**
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
| VKOSPI | **완료 (2026-10-16)**. KRX Open API, 2010-01-04~2026-10-15, 4,130일. 검증값 91.23·96.94 일치. `closes_*.csv`에 `VKOSPI` 열 병합됨 |
| 대시보드 | https://claude.ai/artifact/NjvX1QhNC72LrCMye8HNzD (Dashboard 타입 Artifact) |
| 브랜치 | `claude/vix-nasdaq-kospi-comparison-q1ujie` (PR 없음, 만들지 말 것: 사용자 요청 전까지) |

### 저장소 파일 (`market_fear/`)

| 파일 | 내용 |
|---|---|
| `vix_nasdaq_kospi.py` | 메인. yfinance로 ^VIX, ^VXN, ^IXIC, ^KS11 수집 → CSV + Plotly HTML. `--vkospi`로 VKOSPI 병합 |
| `krx_vkospi.py` | VKOSPI 수집 (KRX Open API). 캐시 CSV, 공식값 검증 |
| `data/closes_5y.csv` | 최근 5년 (열: Date, VIX, VXN, NASDAQ, KOSPI) |
| `data/closes_long.csv` | **대시보드가 쓰는 데이터.** VIX·나스닥 1990-01-02~, VXN 2001-01-23~, 코스피 1996-12-11~, VKOSPI 2010-01-04~ |
| `data/vkospi.csv` | VKOSPI 캐시 (열: Date, VKOSPI). 2010-01-04~. 다음 실행부터는 마지막 날짜 이후만 요청 |
| `dashboard/index.html` | 대시보드 페이지 원본 백업 (Artifact `files/index.html`과 동일하게 유지) |
| `KRX_SETUP.md` | 사용자용 키·도메인 등록 복사·붙여넣기 안내 |
| `requirements.txt` | yfinance, pandas, plotly, requests |
| `../.github/workflows/market-data.yml` | Actions 수집·커밋 워크플로 |

## 3. 환경 설정 (이름만, 값 금지)

| 위치 | 이름 | 용도 | 상태 |
|---|---|---|---|
| 클라우드 환경 변수 | `KRX_API_KEY` | KRX Open API 인증키 | **설정됨, 동작 확인** (키 발급 2026-10-16, 유효기간 ~2027-10-15) |
| 클라우드 환경 변수 | `KRX_ID`, `KRX_PW` | KRX 웹 로그인 (pykrx) | **사용 안 함** (§5-1). 삭제 권장 안내함 |
| 네트워크 허용 도메인 | Yahoo Finance 관련 | yfinance | 허용됨 |
| 네트워크 허용 도메인 | `data-dbg.krx.co.kr` | **KRX Open API 실제 호출 주소** | 허용됨 (2026-10-16 확인) |
| 네트워크 허용 도메인 | `openapi.krx.co.kr` | KRX Open API 포털 | 접속됨 |
| 네트워크 허용 도메인 | `data.krx.co.kr` | KRX 정보데이터시스템 (웹) | 허용돼 있으나 **이 IP는 차단됨** (§5-1) |
| GitHub Actions Secret | `KRX_API_KEY` | Actions에서 VKOSPI 수집 | 사용자 등록 필요 |

환경 설정 변경은 **새 세션부터** 적용됩니다. 환경 관련 문제는 `read_documentation` 도구(environment.secrets / environment.network)로 최신 절차를 확인하고 안내하세요.

## 4. 데이터 출처별 핵심 사실

### Yahoo Finance (yfinance)
- 티커: `^VIX` (CBOE VIX, S&P 500 옵션), `^VXN` (CBOE 나스닥100 변동성, 2001-01-23~), `^IXIC` (나스닥 종합), `^KS11` (코스피, 1996-12-11~).
- **장중에 받으면 마지막 행이 종가가 아님.** 2026-10-15 행의 VIX·나스닥은 미국장 개장 직후 장중 값이고, VXN은 빈칸이었음. 코스피는 확정 종가.
- 휴장일은 CSV에서 빈칸(보정하지 않음). 한·미 휴장일이 다르므로 수익률은 각 지수의 실제 거래일 기준으로 계산.

### KRX Open API (VKOSPI) — 2026-10-16 실제 응답으로 확인
- 엔드포인트: `GET https://data-dbg.krx.co.kr/svc/apis/idx/drvprod_dd_trd?basDd=YYYYMMDD` (포털 서비스명: 지수 → **파생상품지수 시세정보**). 처음 주소를 찾은 출처는 커뮤니티 구현 https://github.com/RealYoungk/openkrx-mcp 였고, 실제 호출로 동작 확인.
- 인증: `AUTH_KEY` **헤더**로 동작 확인(코드가 쓰는 방식). 쿼리 파라미터는 승인 후 시험하지 않음.
- **승인 2단계**: (1) 인증키 발급, (2) **서비스별 이용 신청 → 관리자 승인**. (2) 전에는 모든 API가 `401 {"respMsg":"Unauthorized API Call"}`. 키가 맞아도 401이면 이용 신청 상태부터 확인.
- 응답: `{"OutBlock_1": [...]}`, 행 필드 `BAS_DD, IDX_CLSS, IDX_NM, CLSPRC_IDX, CMPPREVDD_IDX, FLUC_RT, OPNPRC_IDX, HGPRC_IDX, LWPRC_IDX` (값은 문자열). 하루 약 300여 개 지수.
- VKOSPI 행: `IDX_CLSS`="옵션지수", `IDX_NM`="코스피 200 변동성지수", 종가 `CLSPRC_IDX`.
  - **주의**: "코스피 200 현선물 목표변동성 24% 지수", "코스피 200 변동성매칭 양매도지수" 등 이름이 비슷한 지수가 같이 옴. 코드는 공백 제거 후 `코스피200변동성지수`와 **정확히 일치**하는 행만 씀(처음 코드는 "변동성"+"200" 포함 검사라 잘못된 행을 고를 위험이 있어 수정).
- **API 데이터 시작일: 2010-01-04.** VKOSPI 공식 발표는 2009-04-13부터지만 2009년 날짜는 빈 `OutBlock_1`. 2009-04-13~2009-12-30 VKOSPI는 이 API로는 없음(필요하면 KRX 정보데이터시스템 화면 다운로드 등 공식 경로).
- 기준일 하루당 요청 1번. 전 거래일까지만 제공. 전체 수집(2010~, 약 4,400 요청)은 초당 약 2.6건, 약 28분.
- 2026-10-16 첫 전체 수집이 4,200일째에 **200 응답인데 본문이 JSON이 아닌** 일시 오류로 중단됐고, 캐시가 끝에만 저장돼 모두 잃었음 → 재시도(최대 4회, 2/4/8/16초)와 100일마다 중간 저장을 추가. 두 번째 실행은 재시도 없이 완료.
- **검증 결과**: 2026-06-09 **91.23**, 2026-06-29 **96.94** 모두 일치. 4,130일, 결측 없음. 최솟값 9.72, 중앙값 17.11, 평균 19.92. 상위 5개가 모두 2026-06 하순(96.94, 95.09, 94.81, 93.80, 92.71).
- 코스피(Yahoo) 거래일과 대조: VKOSPI만 있고 Yahoo 코스피가 빈 날 5일(2011-10-04, 2017-09-22, 2017-12-20, 2022-01-03, 2022-05-09, Yahoo 쪽 누락으로 보임), 반대는 수집 당일 1일뿐.
- 사용한 날의 호출 수: 실패한 첫 실행 + 재실행 + 탐색으로 약 8,600회(커뮤니티 문서상 일일 한도 10,000). 하루에 전체 수집을 세 번 하지 말 것.

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

1. ~~VKOSPI 수집~~ **완료 (2026-10-16)**. `data/vkospi.csv`, `closes_long.csv`, `closes_5y.csv`에 VKOSPI 반영·커밋됨. 매일 갱신은 `python krx_vkospi.py --start 2010-01-04 --csv data/vkospi.csv`(캐시 이후 날짜만 요청) 후 `vix_nasdaq_kospi.py --vkospi`.
   - GitHub Actions에서 VKOSPI를 받으려면 저장소 Secret `KRX_API_KEY` 등록 필요(2026-10-16 Actions 커밋은 VKOSPI 없이 Yahoo 데이터만 갱신됨 → 아직 미등록으로 보임).
   - 주의: Yahoo 코스피 마지막 행이 한국 장중이면 종가가 아님(2026-10-16 행은 장중 값).
2. 대시보드: 새 `closes_long.csv`를 asset 업로드하고 `datasets/prices`를 update(§6). 설명(description)에서 "VKOSPI 대기" 문구를 바꾸고 출처(KRX Open API, 2010-01-04~)를 추가.
3. 사용자 보고: VKOSPI 구간별 수익률, 현재 VKOSPI의 분위(2026-10-15 코스피 −7.6% 급락일 VKOSPI 55.38, 전날 44.91), VIX vs VKOSPI 2026년 6월 비교.
4. (선택) 실시간: 증권사 API(예: 한국투자증권 KIS Developers) 검토. KRX Open API는 일별·전일 기준이라 실시간이 아님.
5. (선택) 워크플로 예약 실행을 쓰려면 기본 브랜치 병합 필요. 사용자 결정 사항.

## 8-1. 사용자와 합의한 방향 (2026-10-15)

- **백테스트를 포함한 모든 검증은 KRX API 키를 받은 뒤 진행.** 검증 항목:
  - 사후확증 편향 제거: 현재 대시보드의 5분위 기준은 전체 기간(미래 포함)으로 계산돼 있음 → 그날까지의 과거 데이터로만 기준 계산(expanding window)
  - 표본 외 검증(out-of-sample)
  - DCA(매달 정액 적립) vs 공포 구간 추가 매수를 같은 금액으로 비교(현금 대기 비용 포함)
  - Newey-West 표준오차 또는 블록 부트스트랩
  - 연복리 수익률(CAGR), 최대 낙폭(MDD), 거래비용
- **알림은 GitHub Actions로.** 장 마감 후 판정 → 알림. 텔레그램 봇 / 이메일 중 선택은 사용자에게 물어볼 것.
- **자동매매 검토 결과** (2026-10 웹 조사, 공식 문서 미확인):
  - 토스증권: Open API(REST, OAuth 2.0)로 국내·미국 주문 가능. **모의투자 없음, 등록 IP만 허용**
  - 카카오페이증권: 개인용 주문 API 확인 안 됨
  - 미래에셋증권: 개인 신청 경로 확인 못 함
  - 대안: 한국투자증권 KIS(모의투자 있음), KB증권(2026-08 개인 Open API 오픈베타)
- **구성 계획**: GitHub Actions(수집·판정·알림) + 로컬 PC(주문만, 하루 1회 스케줄러). 로컬 주문 스크립트는 **dry-run 기본, 현재 공인 IP가 등록 IP와 다르면 중단, 금액 한도 설정**. 가정용 유동 IP 변경 가능성과 PC 꺼짐에 대비한 알림 필요. 대안은 고정 IP 클라우드 VM.
- 실제 주문은 사용자 계정·승인 아래에서만. 투자 권유가 아님을 유지.

## 9. 새 세션 시작 체크리스트

1. `git fetch origin claude/vix-nasdaq-kospi-comparison-q1ujie && git checkout claude/vix-nasdaq-kospi-comparison-q1ujie && git pull` (Actions 커밋 반영).
2. 환경 변수 설정 여부만 확인: `[ -n "$KRX_API_KEY" ] && echo set` (값 출력 금지).
3. 도메인 확인: `curl -sS -o /dev/null -w "%{http_code}" "https://data-dbg.krx.co.kr/svc/apis/idx/drvprod_dd_trd?basDd=20260629"` → 프록시 403이면 아직 미허용.
4. `pip install -r market_fear/requirements.txt` (pykrx는 설치·import하지 말 것).
5. 대시보드 수정 전 `Artifact read` → `ArtifactData get`으로 현재 버전 확인.
6. 사용자에게는 한국어, 근거 중심, 약어 풀이.
