# MLB StatBat — Manual Tasks

Items that require user action (API keys, external service setup, manual commands).

---

- [ ] `.env` 파일 생성 — `.env.example`을 복사하여 `POSTGRES_PASSWORD`, LLM API 키 등 채우기
- [ ] `docker compose up -d db backend` 로 PostgreSQL 기동 확인
- [ ] `python ingest_batting.py --season 2025` 실행하여 첫 데이터 수집
- [ ] Cloudflare 대시보드에서 Tunnel 생성 및 `CLOUDFLARED_TOKEN` 발급
- [ ] LLM API 키 결정 (Anthropic 또는 OpenAI) 및 `.env`에 추가
