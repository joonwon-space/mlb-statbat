# MLB StatBat — Manual Tasks

Items that require user action (API keys, external service setup, manual commands).

---

## 환경 설정

- [ ] `.env` 파일 생성 — `.env.example`을 복사하여 `POSTGRES_PASSWORD`, LLM API 키 등 채우기
- [ ] LLM API 키 결정 (Anthropic 또는 OpenAI) 및 `.env`에 추가

## 서브도메인 & 배포 (docs/setup/subdomain-setup.md 참조)

- [ ] Cloudflare Tunnel 생성 — Zero Trust 대시보드에서 `mac-mini-statbat` 터널 생성 후 `CLOUDFLARED_TOKEN` 복사
- [ ] Public Hostnames 설정 — `statbat.joonwon.dev` → `http://frontend:3000`, `statbat-api.joonwon.dev` → `http://backend:8000`
- [ ] `docker-compose.yml` 프론트엔드 `NEXT_PUBLIC_API_URL`을 `https://statbat-api.joonwon.dev`로 변경
- [ ] Mac Mini에서 `docker compose up -d` 전체 스택 기동 확인
- [ ] `curl -I https://statbat.joonwon.dev` 로 외부 접속 확인
- [ ] Docker Desktop 자동 시작 설정 (Settings > General > Start on login)

## GitHub Actions 자동 배포

- [ ] Mac Mini에 self-hosted runner 설치 — `Settings > Actions > Runners > New self-hosted runner` 에서 macOS 스크립트 실행
- [ ] Runner를 서비스로 등록 — `./svc.sh install && ./svc.sh start` (Mac 재부팅 시 자동 시작)

## 데이터 수집

- [ ] `docker compose up -d db backend` 로 PostgreSQL 기동 확인
- [ ] `python ingest_batting.py --season 2025` 실행하여 첫 데이터 수집
