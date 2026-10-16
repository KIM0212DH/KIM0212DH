# KRX Open API 키 등록 (복사·붙여넣기용)

VKOSPI(코스피200 변동성지수)는 KRX Open API 인증키로 받습니다.
키 값은 채팅·코드·커밋에 넣지 말고 아래 설정 화면에만 넣으세요.

## 1. Claude 클라우드 환경 (claude.ai/code)

세션 제목 표시줄의 환경 메뉴 → **Edit**

**환경 변수** (Network secrets 항목이 있으면 그곳에, 없으면 Environment variables에).
`여기에_발급받은_키`만 실제 키로 바꿔 붙여넣기:

```
KRX_API_KEY=여기에_발급받은_키
```

**Network access → Allowed domains** (한 줄에 하나씩 추가, "Allow package managers"는 체크 유지):

```
data-dbg.krx.co.kr
```

```
openapi.krx.co.kr
```

- `data-dbg.krx.co.kr`: 실제 데이터 호출 주소 (필수)
- `openapi.krx.co.kr`: 안내·키 관리 포털 (현재도 접속됨, 없어도 수집은 가능)

**더 이상 필요 없는 변수 (삭제 권장)**: `KRX_ID`, `KRX_PW`
— 웹 화면 자동 조회(pykrx)는 KRX 이용약관 제10조 제2호로 금지되어 쓰지 않습니다.

설정 변경은 **새 세션**부터 적용됩니다.

## 2. GitHub Actions (자동 갱신용)

저장소 → Settings → Secrets and variables → Actions → **New repository secret**

Name:

```
KRX_API_KEY
```

Secret: 발급받은 키 값

## 3. KRX Open API 쪽 확인 사항

- openapi.krx.co.kr → 마이페이지에서 인증키 승인 상태 확인
- **서비스별 이용 신청**: 지수 → `파생상품지수 시세정보` 승인 필요
- 데이터는 전 거래일까지 제공(실시간 아님), 매일 08:00 KST 무렵 갱신

## 4. 키 등록 후 실행

```
cd market_fear
python krx_vkospi.py --start 2021-10-15 --csv data/vkospi.csv
python vix_nasdaq_kospi.py --period 5y --vkospi --csv data/closes_5y.csv
```

첫 실행은 영업일 약 1,300일을 하루씩 조회하므로 몇 분 걸립니다.
이후에는 `data/vkospi.csv`에 없는 날짜만 받습니다.
2026-06-09 종가 91.23, 2026-06-29 종가 96.94와 일치하지 않으면 중단합니다.
