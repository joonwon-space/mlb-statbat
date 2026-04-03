# MLB StatBat -- Tasks

Current work items. Read by `/auto-task` and `/next-task`.
Each item should be completable in a single commit.

---

## Current work

### P0 -- Test Suite (Sprint 2 core)

- [x] pytest 설정 추가 -- `backend/pyproject.toml` ([tool.pytest.ini_options] asyncio_mode='auto'), `conftest.py` (httpx.AsyncClient 픽스처), `pytest-asyncio` + `pytest-cov` 의존성 [team-analysis: TD-012]
- [x] `test_main.py` 엔드포인트 테스트 -- GET /health, POST /api/query (501 stub, 400 validation, 성공 경로 mock) [team-analysis: TD-011]
- [ ] `test_text_to_sql.py` 확장 -- `execute_sql()` mocked AsyncSession 테스트, `generate_answer()` 스텁 테스트 [team-analysis: TD-011]
- [ ] `test_schemas.py` 유효성 검사 테스트 -- min_length/max_length 경계값, 빈 문자열, 초과 길이 [team-analysis: TD-011]

### P0 -- Infrastructure (Sprint 2)

- [ ] Alembic 초기화 -- `alembic init`, async env.py 설정, 초기 마이그레이션 --autogenerate, `main.py`의 `create_all()` 제거 [team-analysis: TD-013]
- [ ] SQL 실행 타임아웃 추가 -- `execute_sql()`에 `SET LOCAL statement_timeout = 5000` 또는 커넥션 풀 레벨 설정 [team-analysis: SEC-011]
- [ ] Rate Limiting 추가 -- `slowapi` 설치, `/api/query`에 10 req/min per IP 제한, 429 사용자 친화적 메시지 [team-analysis: SEC-012]
- [ ] `ingest_batting.py` 배치 upsert 전환 -- `ingest_pitching.py` 패턴 맞춤 (iterrows → to_dict('records') + 단일 conn.execute) [team-analysis: TD-014/PERF-011]

### P1 -- LLM Integration (마지막)

- [ ] `generate_sql()` Anthropic Claude 연동 -- `text_to_sql.py`에서 `anthropic.AsyncAnthropic` 클라이언트로 `SYSTEM_PROMPT` + 유저 질문 전송, SQL 파싱 반환 [team-analysis: PROD-011]
- [ ] `generate_answer()` LLM 자연어 답변 생성 -- SQL 결과 rows + 원래 질문을 LLM에 전달, 사람이 읽을 수 있는 요약 생성 [team-analysis: PROD-011b]

---

## Completed (Sprint 1)

### P0 -- Data Pipeline

- [x] `PitchingStats` ORM model added
- [x] `ingest_batting.py` --qual CLI arg
- [x] `ingest_pitching.py` created
- [x] `data_pipeline/Dockerfile` created
- [x] docker-compose data_pipeline service
- [x] Frontend metadata update
- [x] `DB_SCHEMA` pitching_stats description

### P0 -- Security & Stability

- [x] SQL guard (SELECT-only with sqlparse) + 25 tests
- [x] Error message sanitization
- [x] CORS env-based restriction
- [x] QueryRequest min_length/max_length validation
- [x] batting_stats.season index
- [x] Pipeline print() -> logging

### P0 -- UX

- [x] Example question chips
- [x] Loading skeleton/spinner
