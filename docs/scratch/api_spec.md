# MICE DX API 스펙 (EZ데이터허브 대시보드 연동용)

> 작성일: 2026-05-27  
> 확인 방법: Swagger UI + 실제 API 호출 테스트  
> Swagger UI: `https://apitest.ezpmp.co.kr:8443/v1/micedx/swagger-ui/index.html`  
> API 문서: `/v1/micedx/v3/api-docs`

---

## 기본 정보

| 항목 | 값 |
|------|---|
| 운영 Base URL | `https://apitest.ezpmp.co.kr:8443/v1/micedx-prod` |
| 개발 Base URL | `https://apitest.ezpmp.co.kr:8443/v1/micedx` |
| 인증 방식 | API Key — `Authorization` 헤더 (Bearer 토큰) |
| SSL | 자체 서명 인증서 (`verify=False` 필요) |

### 인증 헤더 형식
```
Authorization: Bearer <토큰값>
Content-Type: application/json
```
> 토큰은 `.streamlit/secrets.toml` 의 `[api] token` 에 저장

---

## 1. 직원정보 조회

| 항목 | 값 |
|------|---|
| 엔드포인트 | `GET /admin/user/evaluation/get` |
| 섹션 | ADMIN USER API |
| 페이지네이션 | query param (`page`, `size`) |
| 총 레코드 수 | 약 196명 (퇴사자 제외 시 148명) |

### 요청 파라미터
없음 (page/size query param만 사용)

### 응답 구조
```json
[
  {
    "userNo": 1,
    "userNm": "홍길동",
    "prsId": "hong@ezpmp.co.kr",
    "hireDt": "2022-10-04",
    "retireDt": null,
    "history": [
      {
        "year": 2026,
        "divisionNm": "디지털융합혁신부",
        "hqNm": "ICT융합개발본부",
        "deptNm": "융합개발 1팀",
        "jobNm": "팀원",
        "positionNm": "선임",
        "statPositionNm": "대리"
      }
    ]
  }
]
```

### 주요 필드 → 대시보드 컬럼 매핑
| API 필드 | 대시보드 컬럼 | 비고 |
|----------|-------------|------|
| `userNo` | `UserNo` | |
| `userNm` | `임직원명` | |
| `prsId` | `PRS ID` | 로그인 ID (이메일) |
| `hireDt` | `입사일자` | |
| `retireDt` | — | null 아니면 퇴사자 → 제외 |
| `history[year].deptNm` | `{year}_부서명` | |
| `history[year].hqNm` | `{year}_본부/실` | |
| `history[year].divisionNm` | `{year}_사업부` | 파일 소속 사업부 |
| `history[year].statPositionNm` | `{year}_통계 직급` | |

---

## 2. 로그인 이력 조회

| 항목 | 값 |
|------|---|
| 엔드포인트 | `POST /api/v1/admin/login-history/search` |
| 섹션 | ADMIN LOG API — 관리자 로그인 이력 조회 API |
| 페이지네이션 | body (`page`, `size`) |
| 총 레코드 수 | 약 5,763건 |

### 요청 Body
```json
{
  "page": 0,
  "size": 200,
  "dateFrom": "2026-01-01",
  "dateTo": "2026-05-27",
  "keyword": "홍길동"
}
```
> `dateFrom`, `dateTo`, `keyword` 는 선택 파라미터 (전체 조회 시 생략 가능)  
> `keyword` 는 이름·부서 통합 검색

### 응답 구조
```json
{
  "data": {
    "list": [
      {
        "rowNum": 1,
        "userNo": 1,
        "userNm": "홍길동",
        "departmentNm": "융합개발 1팀",
        "positionNm": "선임",
        "jobNm": "팀원",
        "ipAddress": "192.168.0.1",
        "userAgent": "Mozilla/5.0 ...",
        "deviceGbn": "PC",
        "osNm": "Windows",
        "browserNm": "Chrome",
        "createdDt": "2026-04-17T09:24:35+09:00"
      }
    ],
    "totalCount": 5763,
    "page": 0,
    "size": 200
  }
}
```

### 주요 필드 → 대시보드 컬럼 매핑
| API 필드 | 대시보드 컬럼 | 비고 |
|----------|-------------|------|
| `userNo` | `UserNo` | |
| `createdDt` | `로그인 일자` + `로그인 시간` | ISO 8601 (+09:00) |

### 관련 엔드포인트 (참고)
| 경로 | 설명 |
|------|------|
| `POST /api/v1/admin/login-history/excel` | 로그인 이력 엑셀 다운로드 (페이지네이션 없이 전체) |
| `POST /api/v1/admin/login-history/count/search` | 로그인 횟수 목록 조회 |
| `POST /api/v1/admin/login-history/count/excel` | 로그인 횟수 엑셀 다운로드 |

---

## 3. 다운로드 로그 조회

| 항목 | 값 |
|------|---|
| 엔드포인트 | `POST /api/v1/admin/download-logs/search` |
| 섹션 | ADMIN LOG API |
| 페이지네이션 | body (`page`, `size`) |
| 총 레코드 수 | 약 4,482건 |

### 요청 Body
```json
{
  "page": 0,
  "size": 200,
  "dateFrom": "2026-05-01",
  "dateTo": "2026-05-27",
  "fileNm": "보고서",
  "keyword": "홍길동"
}
```
> `keyword` 는 사용자ID·이름·부서·역할 통합 검색

### 응답 구조
```json
{
  "data": {
    "list": [
      {
        "rowNum": 1,
        "logNo": 1001,
        "fileNm": "샘플파일.pdf",
        "divisionNm": "디지털융합혁신부",
        "fileSize": 204800,
        "ipAddr": "192.168.0.1",
        "filePath": "https://micedx.ezpmp.co.kr/project-search/2026/...",
        "userNo": 1,
        "userId": "hong@ezpmp.co.kr",
        "userNm": "홍길동",
        "userDivisionNm": "디지털융합혁신부",
        "departmentNm": "융합개발 1팀",
        "jobNm": "팀원",
        "createDt": "2026-04-17T09:24:35+09:00"
      }
    ],
    "totalCount": 4482,
    "page": 0,
    "size": 200
  }
}
```

### 주요 필드 → 대시보드 컬럼 매핑
| API 필드 | 대시보드 컬럼 | 비고 |
|----------|-------------|------|
| `userNo` | `UserNo` | |
| `createDt` | `다운로드 일자` + `다운로드 시간` | ISO 8601 (+09:00) |
| `filePath` | `경로 메뉴명` | URL 키워드로 카테고리 분류 (아래 참고) |

### filePath 카테고리 매핑
| URL 키워드 | 경로 메뉴명 | KPI 집계 |
|-----------|------------|---------|
| `project-search` | 프로젝트 찾기 | ✅ |
| `manage-file` | 운영자료 찾기 | ✅ |
| `performance` | 프로젝트 실적 | ✅ |
| `support` | 서포트 센터 | ✅ |
| 그 외 | 기타 | ❌ |

---

## 4. 제안서(ezPDF DRM) 열람 로그 조회

| 항목 | 값 |
|------|---|
| 엔드포인트 | `POST /admin/drm/open-log/get` |
| 섹션 | ADMIN DRM API |
| 페이지네이션 | body (`page`, `size`) |
| 총 레코드 수 | 약 962건 |

### 요청 Body
```json
{}
```
> 요청 파라미터 없음 (page/size body로 전달)

### 응답 구조
```json
{
  "list": [
    {
      "no": 1,
      "itemId": "/data/micedx/2026년/샘플프로젝트/제안서/샘플제안서.pdf",
      "clientIp": "220.85.68.84",
      "resultYn": "성공",
      "type": "open",
      "openDate": "2026. 4. 29",
      "openTime": "13:07:52",
      "userNm": "홍길동",
      "teamNm": "컨벤션 1팀",
      "roleNm": "대리",
      "prsId": "hong@ezpmp.co.kr"
    }
  ],
  "totalCount": 962
}
```

### 주요 필드 → 대시보드 컬럼 매핑
| API 필드 | 대시보드 컬럼 | 비고 |
|----------|-------------|------|
| `prsId` | `PRS ID` | UserNo 역매핑용 |
| `openDate` | `등록일` | `"2026. 4. 29"` → `"2026-04-29"` 자동 변환 |
| `openTime` | `등록시간` | `"HH:MM:SS"` |
| `itemId` | `문서경로` | 파일 경로 (타임라인·Top10 분석용) |

---

## 5. 기타 확인된 엔드포인트

| 섹션 | 메서드 | 경로 | 설명 |
|------|--------|------|------|
| ADMIN AI GATE LOG API | GET | `/api/v1/admin/logs/events` | AI Gate 관리자 로그 목록 조회 |
| ADMIN ARCHIVE API | POST | `/admin/archive/list/get` | 운영자료(아카이브) 조회 |
| ADMIN CLICK LOG API | — | (하위 엔드포인트 있음) | 버튼 클릭 기록 조회 |
| ADMIN GROUP API | POST | `/admin/group/permission/get` | 그룹 권한 조회 |
| ADMIN GROUP API | POST | `/admin/group/get` | 그룹 조회 |

---

## 참고: 응답 구조 패턴

| 패턴 | 적용 API | 구조 |
|------|---------|------|
| A | 로그인·다운로드 | `{"data": {"list": [...], "totalCount": N, "page": N, "size": N}}` |
| B | 제안서 | `{"list": [...], "totalCount": N}` |
| C | 직원정보 | `[{...}, {...}]` (단순 배열) |
