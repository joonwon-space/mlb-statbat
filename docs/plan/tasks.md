# MLB StatBat — Tasks

Current work items. Read by `/auto-task` and `/next-task`.
Each item should be completable in a single commit.

---

## Current work

### P0 — 데이터 수집 파이프라인

- [x] `PitchingStats` ORM 모델 추가 — `backend/app/models.py`에 투수 스탯 테이블 (games, games_started, innings_pitched, wins, losses, saves, strikeouts, walks, home_runs_allowed, era, whip, fip, xfip, k_per_9, bb_per_9, hr_per_9, war)
- [x] `ingest_batting.py`에 `--qual` CLI 인자 추가 — 현재 `qual=50` 하드코딩 → argparse로 옵션화 (기본값 50 유지)
- [x] `ingest_pitching.py` 작성 — `pybaseball.pitching_stats(season, qual)` 수집 → `PitchingStats` 테이블 upsert, `ingest_batting.py`와 동일한 패턴
- [ ] `data_pipeline/Dockerfile` 작성 — Python 3.12-slim 기반, requirements.txt 설치, entrypoint는 bash
- [ ] `docker-compose.yml`에 `data_pipeline` 서비스 추가 — `profiles: ["pipeline"]` 설정, DB 의존성, `.env` 연동
- [ ] 프론트엔드 메타데이터 수정 — `frontend/src/app/layout.tsx`의 title="MLB StatBat", description 업데이트
- [ ] `text_to_sql.py`의 `DB_SCHEMA`에 `pitching_stats` 테이블 설명 추가

### P0 — 보안 및 안정성 (team-analysis 2026-04-03)

- [ ] `execute_sql()`에 SQL 가드 추가 — SELECT 쿼리만 허용, DROP/DELETE/UPDATE/INSERT/ALTER 차단 [team-analysis: SEC-001]
- [ ] SQL 실행 에러 메시지를 사용자에게 노출하지 않도록 변경 — 서버 로그만, 클라이언트에는 일반 메시지 [team-analysis: SEC-006]
- [ ] CORS `allow_origins`를 환경변수 기반으로 제한 — 개발: localhost, 프로덕션: statbat.joonwon.dev [team-analysis: SEC-003]
- [ ] `QueryRequest.question`에 `min_length=3, max_length=500` 유효성 검사 추가 [team-analysis: TD-005/SEC-007]
- [ ] `batting_stats.season` 컬럼에 인덱스 추가 [team-analysis: PERF-003]
- [ ] `data_pipeline/ingest_batting.py`의 `print()`를 `logging` 모듈로 교체 [team-analysis: TD-003]

### P0 — UX 개선 (team-analysis 2026-04-03)

- [ ] 메인 페이지에 예시 질문 칩 버튼 추가 — 클릭 시 자동 입력 및 제출 [team-analysis: UX-002]
- [ ] 쿼리 실행 중 로딩 스켈레톤/스피너 추가 — 버튼 '...' 대신 결과 영역에 표시 [team-analysis: UX-003]
