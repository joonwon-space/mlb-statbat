# MLB StatBat -- TODO

> **Sprint 2 Focus: LLM Integration + Test Suite + Alembic**
> Sprint 1 secured the foundation. Sprint 2 makes the app functional.

---

## P0 -- Sprint 2 Current Work

See `tasks.md` for detailed task list.

---

## P1 -- Next Sprint (Data Depth + Polish)

### [ ] 읽기 전용 DB 사용자 생성 (query 실행용) [team-analysis: SEC-013]
- `statbat_reader` PostgreSQL 역할 생성 (SELECT 권한만)
- `execute_sql()`에서 읽기 전용 커넥션 사용
- 관리자 커넥션은 마이그레이션 전용

### [ ] 멀티시즌 히스토리 데이터 수집 (2020-2025) [team-analysis: PROD-012]
- `--start-year`/`--end-year` CLI 인자 추가
- 최소 5개 시즌 배치 수집

### [ ] 질문 히스토리 기능 (localStorage 영속) [team-analysis: UX-012]
- 이전 질문/답변 목록 채팅 스타일 표시
- `localStorage`에 히스토리 저장
- P3에서 P1으로 승격 (핵심 경험)

### [ ] 결과 테이블 컬럼 헤더 사람이 읽을 수 있게 변경 [team-analysis: UX-016]
- batting_avg -> AVG, home_runs -> HR, wrc_plus -> wRC+ 등 매핑

### [ ] LLM 응답 캐싱 (TTLCache) [team-analysis: PERF-002]
- `cachetools.TTLCache` (1시간 TTL) 기반 캐시
- 정규화된 질문 텍스트를 키로 사용

### [ ] 결과 크기 제한 (fetchmany/LIMIT) [team-analysis: PERF-012]
- `execute_sql()`에 최대 100행 제한
- SYSTEM_PROMPT에 LIMIT 50 기본 포함 지시 [team-analysis: PERF-015]

### [ ] 파이프라인 공통 코드 추출 (common.py) [team-analysis: TD-016]
- 플레이어 upsert, PLAYER_COLUMN_MAP, DATABASE_URL 공유

### [ ] LLM 프롬프트 인젝션 방어 강화 [team-analysis: SEC-017]
- 유저 입력 구분자 래핑, 시스템 프롬프트 가드레일

### [ ] 플레이어 프로필 position/handedness 파이프라인 추가 [team-analysis: PROD-015]
- PLAYER_COLUMN_MAP에 position, bats, throws 추가

### [ ] 데이터 파이프라인 배치 인서트 -- 투수 일관성 [team-analysis: TD-014]
- (tasks.md에서 처리됨, P1으로 백업)

---

## P2 -- UX 개선 및 접근성

### [ ] 야구 통계 숫자 포맷팅 [team-analysis: UX-005]
- 타율 .300 (3자리), ERA 2자리, WAR 1자리, 카운팅 스탯 콤마

### [ ] 접근성 개선: aria-label + table scope [team-analysis: UX-014/UX-015]
- Textarea에 aria-label 추가, 테이블에 caption + scope 속성

### [ ] 빈 결과 상태 표시 [team-analysis: UX-013]
- 쿼리 결과 0건일 때 친화적 메시지 표시

### [ ] SQL 복사 버튼 [team-analysis: UX-017]
- Generated SQL 카드에 클립보드 복사 버튼

### [ ] page.tsx를 서버/클라이언트 컴포넌트로 분리 [team-analysis: PERF-013]
- QueryForm, ResultsTable 컴포넌트 추출
- 페이지 셸은 서버 렌더링

### [ ] 프론트엔드 테스트 스위트 (vitest) [team-analysis: TD-015]
- vitest + @testing-library/react 설정
- page.test.tsx 기본 테스트

### [ ] 다크/라이트 모드 토글 [team-analysis: UX-018]
- next-themes 또는 className 토글

### [ ] 501 에러 메시지 사용자 친화적으로 변경 [team-analysis: UX-011]
- "LLM integration not yet configured" -> 친화적 메시지
- (LLM 연동 완료 시 자동 해결)

---

## P2 -- 보안 강화 + 인프라

### [ ] Docker 컨테이너 non-root 사용자 설정 [team-analysis: SEC-014]
- backend/frontend Dockerfile에 appuser 추가

### [ ] 프론트엔드 보안 헤더 (CSP, X-Frame-Options) [team-analysis: SEC-015]
- next.config.ts headers() 설정

### [ ] API 키 미설정 경고 로그 [team-analysis: SEC-016]
- 앱 시작 시 양쪽 키 모두 비어있으면 WARNING 로그

### [ ] DB 커넥션 풀 설정 [team-analysis: TD-018/PERF-014]
- pool_size, max_overflow, pool_pre_ping, pool_recycle 명시

### [ ] 파이프라인 함수 타입 어노테이션 [team-analysis: TD-017]
- load(), main() 등 반환 타입 추가

---

## P3 -- 기능 확장

### [ ] 데이터 시각화 -- 리더보드 차트, 트렌드 차트 [team-analysis: PROD-007]
- recharts 또는 visx 사용

### [ ] LLM 응답 스트리밍 (SSE) [team-analysis: PERF-005]
- /api/query/stream 엔드포인트 + EventSource

### [ ] 수비 스탯, 팀 순위, 리그 평균 데이터 추가 [team-analysis: PROD-006]

### [ ] 자동 데이터 갱신 워크플로우 [team-analysis: PROD-016]
- 시즌 중 주간 자동 수집 (GitHub Actions 또는 cron)

### [ ] README.md 작성
- 프로젝트 소개, 아키텍처 다이어그램, 로컬 개발 세팅

---

## Completed

- [x] Monorepo 디렉토리 구조 생성
- [x] docker-compose.yml: PostgreSQL, FastAPI, Next.js, Cloudflared
- [x] FastAPI 기본 구조 (main.py, config.py, database.py)
- [x] SQLAlchemy ORM: Player, BattingStats, PitchingStats
- [x] Text-to-SQL 엔드포인트 (/api/query) + SQL guard
- [x] Next.js App Router + Tailwind + shadcn/ui
- [x] 메인 페이지 Chat UI (입력, 결과, SQL 뷰어, 테이블)
- [x] 백엔드 API 통신 유틸리티 (api.ts)
- [x] data_pipeline/ingest_batting.py + ingest_pitching.py
- [x] CORS 환경변수 기반 제한
- [x] 에러 메시지 sanitization
- [x] 입력 유효성 검사 (3-500자)
- [x] 예시 질문 칩 + 로딩 스켈레톤
- [x] batting_stats.season 인덱스
- [x] 파이프라인 logging 전환
- [x] 프론트엔드 메타데이터 업데이트
