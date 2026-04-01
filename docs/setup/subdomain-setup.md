# Subdomain Setup (Mac Mini + Docker + Cloudflare Tunnel)

Mac Mini에서 Docker로 mlb-statbat을 실행하고, Cloudflare Tunnel을 통해 서브도메인으로 외부 접속을 허용하는 방법.

## 사전 요구사항

- Mac Mini에 Docker Desktop 설치
- Cloudflare 계정 + 도메인 등록 완료 (예: `example.com`)
- 도메인의 네임서버가 Cloudflare로 설정되어 있어야 함

## 1. Cloudflare Tunnel 생성

### 1-1. Cloudflare Zero Trust 대시보드에서 생성 (권장)

1. [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) 접속
2. **Networks > Tunnels > Create a tunnel**
3. Tunnel 이름 입력 (예: `mac-mini-statbat`)
4. 생성 후 표시되는 **Tunnel Token** 복사

### 1-2. CLI로 생성 (대안)

```bash
# cloudflared 설치 (Mac)
brew install cloudflared

# 로그인
cloudflared tunnel login

# 터널 생성
cloudflared tunnel create mac-mini-statbat

# 토큰 확인
cloudflared tunnel token mac-mini-statbat
```

## 2. 서브도메인 라우팅 설정

Cloudflare Zero Trust 대시보드에서 **Public Hostnames** 탭으로 이동하여 라우팅 추가:

| Subdomain | Domain | Service |
|-----------|--------|---------|
| `statbat` | `example.com` | `http://frontend:3000` |
| `statbat-api` | `example.com` | `http://backend:8000` |

결과:
- `statbat.example.com` → Next.js 프론트엔드
- `statbat-api.example.com` → FastAPI 백엔드

> **참고**: Cloudflare 대시보드에서 설정하면 DNS CNAME 레코드가 자동 생성됨.

## 3. 환경변수 설정

Mac Mini에서 프로젝트 루트에 `.env` 파일 생성:

```bash
# Database
POSTGRES_USER=statbat
POSTGRES_PASSWORD=<강력한-비밀번호>
POSTGRES_DB=mlb_statbat
DATABASE_URL=postgresql+asyncpg://statbat:<비밀번호>@db:5432/mlb_statbat

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Cloudflare Tunnel
CLOUDFLARED_TOKEN=<1단계에서-복사한-토큰>
```

## 4. 프론트엔드 API URL 업데이트

`docker-compose.yml`에서 프론트엔드의 `NEXT_PUBLIC_API_URL`을 서브도메인으로 변경:

```yaml
frontend:
  environment:
    NEXT_PUBLIC_API_URL: https://statbat-api.example.com
```

> `http://backend:8000`은 Docker 내부 통신용이므로, 브라우저에서 접근할 때는 외부 URL 필요.

## 5. Docker 실행

```bash
# Mac Mini에서 실행
cd /path/to/mlb-statbat

# 전체 서비스 시작 (백그라운드)
docker compose up -d

# 로그 확인
docker compose logs -f

# cloudflared 터널 연결 상태 확인
docker compose logs cloudflared
```

정상 연결 시 cloudflared 로그에 다음과 같이 표시:

```
INF Connection registered connIndex=0 ...
INF Connection registered connIndex=1 ...
```

## 6. 동작 확인

```bash
# 프론트엔드 접속 확인
curl -I https://statbat.example.com

# API 헬스체크
curl https://statbat-api.example.com/docs
```

## 7. Mac Mini 재부팅 시 자동 시작

Docker Desktop이 로그인 시 자동 시작되도록 설정:

1. **Docker Desktop > Settings > General > Start Docker Desktop when you sign in to your Mac** 체크
2. `docker-compose.yml`에 `restart: unless-stopped`이 이미 설정되어 있으므로 Docker 시작 시 컨테이너 자동 복구됨

## 트러블슈팅

### 터널이 연결되지 않음

```bash
# 토큰 확인
docker compose exec cloudflared cloudflared tunnel info

# 컨테이너 재시작
docker compose restart cloudflared
```

### 502 Bad Gateway

- 백엔드 또는 프론트엔드 컨테이너가 아직 시작 중일 수 있음
- `docker compose ps`로 모든 서비스 상태 확인
- Cloudflare 라우팅의 Service URL이 Docker 서비스명과 일치하는지 확인 (`frontend:3000`, `backend:8000`)

### DNS 전파 지연

- Cloudflare Tunnel 사용 시 일반적으로 즉시 적용됨
- 브라우저 캐시/DNS 캐시 클리어: `sudo dscacheutil -flushcache`
