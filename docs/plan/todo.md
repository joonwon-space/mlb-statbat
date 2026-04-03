# MLB StatBat — TODO

> **우선순위 원칙: DB에 데이터가 쌓여야 모든 것이 의미 있다.**
> 데이터 수집 → 인프라 안정화 → LLM 연동 → 기능 개선 순으로 진행한다.

---

## 🔴 P0 — 데이터 수집 (가장 먼저)

### [ ] `.env` 파일 세팅 (로컬 환경)
- `.env.example`을 복사하여 `.env` 생성
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` 값 채우기
- LLM API 키, `CLOUDFLARED_TOKEN`은 이후 단계에서 추가

### [ ] Docker Compose로 DB + Backend 실행
- **할 일**:
  - `docker compose up -d db backend` 로 PostgreSQL 컨테이너 기동
  - `docker compose logs db` 로 헬스체크 통과 확인
  - FastAPI `/health` 엔드포인트 응답 확인

### [ ] 타자 스탯 수집 실행 (2025 시즌)
- **파일**: `data_pipeline/ingest_batting.py`
- **할 일**:
  - `data_pipeline/` 가상환경 세팅 (`pip install -r requirements.txt`)
  - `python ingest_batting.py --season 2025` 실행
  - DB에 `players`, `batting_stats` 데이터 정상 insert 확인
  - 이전 시즌(2024, 2023 등) 히스토리 데이터도 수집

### [ ] 투수 스탯 모델 추가
- **현재 상태**: 타자 스탯(`batting_stats`)만 존재, 투수 테이블 없음
- **할 일**:
  - `backend/app/models.py`에 `PitchingStats` 모델 추가
    - `player_mlb_id`, `season`, `team`
    - 카운팅: `games`, `games_started`, `innings_pitched`, `wins`, `losses`, `saves`, `strikeouts`, `walks`, `home_runs_allowed`
    - 레이트: `era`, `whip`, `fip`, `k_per_9`, `bb_per_9`, `hr_per_9`
    - 어드밴스드: `xfip`, `war`

### [ ] 투수 스탯 수집 스크립트 작성
- **파일**: `data_pipeline/ingest_pitching.py` (신규)
- **할 일**:
  - `pybaseball.pitching_stats(season, qual=30)` 로 데이터 수집
  - `ingest_batting.py`와 동일한 upsert 패턴 적용
  - `python ingest_pitching.py --season 2025` 실행 및 확인

### [ ] 데이터 파이프라인 Docker화
- **할 일**:
  - `data_pipeline/Dockerfile` 작성
  - `docker-compose.yml`에 `data_pipeline` 서비스 추가
    - `profiles: ["pipeline"]` 로 수동 실행 전용으로 설정
    - 실행 커맨드: `docker compose --profile pipeline run data_pipeline --season 2025`

### [ ] 데이터 파이프라인: `qual` 파라미터 옵션화
- **파일**: `data_pipeline/ingest_batting.py`
- **현재 상태**: `qual=50` 하드코딩
- **할 일**: `--qual` CLI 인자 추가 (기본값 50 유지)

---

## 🟡 P1 — 인프라 안정화 + 보안 강화

### [ ] DB 마이그레이션 관리 (Alembic)
- **현재 상태**: 앱 시작 시 `create_all()`로 테이블 생성 (프로덕션 비권장)
- **할 일**:
  - `alembic init` 으로 마이그레이션 환경 초기화
  - 최초 마이그레이션 파일 생성
  - `docker-compose.yml`에 마이그레이션 실행 커맨드 추가

### [ ] Cloudflare Tunnel 설정
- **할 일**:
  - Cloudflare 대시보드에서 Tunnel 생성 및 `CLOUDFLARED_TOKEN` 발급
  - `statbat.joonwon.dev` → `frontend:3000` 라우팅 설정
  - HTTPS 자동 인증서 확인

### [ ] 읽기 전용 DB 사용자 생성 (query 실행용) [team-analysis: SEC-002]
- **할 일**:
  - `statbat_reader` PostgreSQL 역할 생성 (SELECT 권한만)
  - `execute_sql()`에서 읽기 전용 커넥션 사용
  - 관리자 커넥션은 마이그레이션 전용

### [ ] Rate Limiting 추가 (`/api/query`) [team-analysis: SEC-004]
- **할 일**:
  - `slowapi` 설치 및 설정
  - `/api/query`에 10 req/min per IP 제한
  - 429 응답 메시지 사용자 친화적으로

### [ ] 테스트 스위트 구축 [team-analysis: TD-001]
- **할 일**:
  - `backend/tests/` 디렉토리 + pytest 설정
  - `test_main.py` (health 엔드포인트)
  - `test_text_to_sql.py` (execute_sql, SQL guard)
  - `frontend/__tests__/` 기본 컴포넌트 테스트
  - 80% 커버리지 목표

### [ ] LLM 응답 캐싱 (TTLCache) [team-analysis: PERF-002]
- **할 일**:
  - `cachetools.TTLCache` (1시간 TTL) 기반 캐시
  - 정규화된 질문 텍스트를 키로 사용
  - 생성된 SQL만 캐싱 (결과는 캐싱하지 않음)

### [ ] 데이터 파이프라인 배치 인서트 전환 [team-analysis: PERF-001/TD-002]
- **할 일**:
  - `iterrows()` → `executemany()` 또는 `execute_values()` 변환
  - 플레이어/스탯 각각 단일 배치 upsert
  - 예상 개선: 20-30배 빠른 수집

### [ ] 멀티시즌 히스토리 데이터 수집 (2020-2025) [team-analysis: PROD-003]
- **할 일**:
  - `--start-year`/`--end-year` CLI 인자 추가
  - 최소 5개 시즌 (2020-2025) 배치 수집
  - 시즌별 순차 처리 + 메모리 해제

### [ ] Docker Compose 전체 스택 통합 테스트
- **할 일**:
  - `docker compose up --build` 로 전체 4개 서비스 실행 확인
  - DB → Backend → Frontend → Cloudflared 연결 순서 검증

---

## 🟠 P2 — LLM 연동 (Text-to-SQL)

### [ ] LLM 연동: `generate_sql()` 구현
- **파일**: `backend/app/text_to_sql.py`
- **현재 상태**: `NotImplementedError` 반환 중 (스텁)
- **할 일**:
  - Anthropic(`claude-sonnet`) 또는 OpenAI(`gpt-4o`) 클라이언트 선택 및 초기화
  - `settings.anthropic_api_key` / `settings.openai_api_key` 연동
  - `SYSTEM_PROMPT` + 유저 질문을 LLM에 전송
  - LLM 응답에서 SQL만 파싱하여 반환
  - SQL 안전성: SELECT 쿼리만 허용하도록 가드 추가

### [ ] LLM 연동: `generate_answer()` 구현
- **파일**: `backend/app/text_to_sql.py`
- **현재 상태**: `str(rows)` 그대로 반환 (사람이 읽기 어려움)
- **할 일**:
  - SQL 결과 rows + 원래 질문을 LLM에 전달
  - 자연언어 요약 답변 생성 ("오타니의 2025 OPS는 1.012입니다.")

### [ ] `DB_SCHEMA` 에 투수 테이블 설명 추가
- **파일**: `backend/app/text_to_sql.py`
- **할 일**: `PitchingStats` 테이블 및 컬럼 설명을 `DB_SCHEMA` 상수에 반영

### [ ] 에러 핸들링 고도화
- **파일**: `backend/app/main.py`
- **할 일**:
  - LLM API 오류 (타임아웃, rate limit) 처리
  - SQL 실행 실패 시 사용자 친화적 메시지 반환
  - 전역 예외 핸들러 추가

---

## 🟢 P2 — UX 개선 및 데이터 확장 (team-analysis 2026-04-03)

### [ ] 결과 테이블 컬럼 헤더 사람이 읽을 수 있게 변경 [team-analysis: UX-004]
- batting_avg → AVG, home_runs → HR, wrc_plus → wRC+ 등 매핑

### [ ] 야구 통계 숫자 포맷팅 [team-analysis: UX-005]
- 타율 .300 (3자리), ERA 2자리, WAR 1자리, 카운팅 스탯 콤마

### [ ] 접근성 개선: aria-label + table scope [team-analysis: UX-006/UX-007]
- Textarea에 aria-label 추가, 테이블에 caption + scope 속성

### [ ] page.tsx를 서버/클라이언트 컴포넌트로 분리 [team-analysis: PERF-006/TD-009]
- QueryForm, ResultsTable, ErrorDisplay 컴포넌트 추출
- 페이지 셸은 서버 렌더링

### [ ] Docker 컨테이너 non-root 사용자 설정 [team-analysis: SEC-009]
- backend/frontend Dockerfile에 appuser 추가

### [ ] 수비 스탯, 팀 순위, 리그 평균 데이터 추가 [team-analysis: PROD-006]

### [ ] 데이터 시각화 — 리더보드 차트, 트렌드 차트 [team-analysis: PROD-007]
- recharts 또는 visx 사용, LLM이 차트 타입 제안

### [ ] LLM 응답 스트리밍 (SSE) [team-analysis: PERF-005]
- /api/query/stream 엔드포인트 + EventSource 프론트엔드

---

## 🟢 P3 — 기능 개선

### [ ] 프론트엔드 메타데이터 수정
- **파일**: `frontend/src/app/layout.tsx`
- **현재 상태**: title="Create Next App", description="Generated by create next app"
- **할 일**: title="MLB StatBat", description 업데이트

### [ ] CORS 범위 제한
- **파일**: `backend/app/main.py`
- **현재 상태**: `allow_origins=["*"]` (모든 출처 허용)
- **할 일**: 프로덕션에서 `statbat.joonwon.dev`만 허용하도록 env 기반 설정

### [ ] 질문 히스토리 기능 (프론트엔드)
- **파일**: `frontend/src/app/page.tsx`
- **할 일**:
  - 이전 질문/답변 목록 표시 (채팅 스타일)
  - `localStorage`에 히스토리 저장

### [ ] 예시 질문 버튼 (프론트엔드)
- **할 일**:
  - 메인 화면에 샘플 질문 칩 버튼 추가
  - 예: "올해 오타니 OPS는?", "2025년 홈런 1위 타자는?", "저지의 커리어 통산 WAR은?"

### [ ] README.md 작성
- **할 일**:
  - 프로젝트 소개 및 아키텍처 다이어그램
  - 로컬 개발 환경 세팅 방법 (`cp .env.example .env` → `docker compose up`)
  - 데이터 파이프라인 실행 방법

---

## ✅ 완료된 항목

- [x] Monorepo 디렉토리 구조 생성
- [x] `docker-compose.yml`: PostgreSQL, FastAPI, Next.js, Cloudflared 서비스 정의
- [x] FastAPI 앱 기본 구조 (`main.py`, `config.py`, `database.py`)
- [x] SQLAlchemy ORM 모델: `Player`, `BattingStats`
- [x] Text-to-SQL 엔드포인트 (`/api/query`) 라우팅 및 흐름 정의
- [x] Next.js (App Router) + Tailwind CSS + shadcn/ui 초기화
- [x] 메인 페이지 Chat UI (입력창, 결과 카드, SQL 뷰어, 결과 테이블)
- [x] 백엔드 API 통신 유틸리티 (`src/lib/api.ts`)
- [x] `data_pipeline/ingest_batting.py`: pybaseball 수집 → PostgreSQL upsert
- [x] GitHub 레포지토리 초기 커밋 및 브랜치 퍼블리시
