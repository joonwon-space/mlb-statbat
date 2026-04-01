# MLB StatBat — Tasks

Current work items. Read by `/auto-task` and `/next-task`.
Each item should be completable in a single commit.

---

## Current work

### P0 — 데이터 수집 파이프라인

- [ ] `PitchingStats` ORM 모델 추가 — `backend/app/models.py`에 투수 스탯 테이블 (games, games_started, innings_pitched, wins, losses, saves, strikeouts, walks, home_runs_allowed, era, whip, fip, xfip, k_per_9, bb_per_9, hr_per_9, war)
- [ ] `ingest_batting.py`에 `--qual` CLI 인자 추가 — 현재 `qual=50` 하드코딩 → argparse로 옵션화 (기본값 50 유지)
- [ ] `ingest_pitching.py` 작성 — `pybaseball.pitching_stats(season, qual)` 수집 → `PitchingStats` 테이블 upsert, `ingest_batting.py`와 동일한 패턴
- [ ] `data_pipeline/Dockerfile` 작성 — Python 3.12-slim 기반, requirements.txt 설치, entrypoint는 bash
- [ ] `docker-compose.yml`에 `data_pipeline` 서비스 추가 — `profiles: ["pipeline"]` 설정, DB 의존성, `.env` 연동
- [ ] 프론트엔드 메타데이터 수정 — `frontend/src/app/layout.tsx`의 title="MLB StatBat", description 업데이트
- [ ] `text_to_sql.py`의 `DB_SCHEMA`에 `pitching_stats` 테이블 설명 추가
