# IP 기반 접근 제어 (IP-Based Access Control)

## 📋 개요

이 API 서버는 **IP 화이트리스트** 방식으로 접근을 제어합니다. JWT 인증이나 사용자 로그인 없이, **특정 IP 주소에서 온 요청만** API에 접근할 수 있습니다.

## 🔒 보안 아키텍처

```
외부 사용자
    ↓
인증 서버 (다른 서버에서 처리)
    ↓
API 게이트웨이 / 리버스 프록시
    ↓
Docling API 서버 (이 서버)
    → IP 화이트리스트로 접근 제어
```

### 설계 원칙

1. **인증은 외부에서 처리**: 별도의 인증 서버나 API 게이트웨이에서 사용자 인증을 담당
2. **Docling API는 내부 서비스**: 신뢰할 수 있는 IP에서만 접근 가능
3. **마이크로서비스 패턴**: 각 서비스는 단일 책임만 수행

## 🌐 허용된 IP 목록

### 기본 설정

```python
ALLOWED_IPS = [
    "127.0.0.1",           # localhost (IPv4)
    "::1",                 # localhost (IPv6)
    "172.16.0.0/12",       # Docker 기본 네트워크
    "192.168.0.0/16",      # 사설 네트워크 (Docker, 로컬 네트워크)
    "10.0.0.0/8"           # 사설 네트워크 (VPC, 내부 네트워크)
]
```

### 환경 변수로 설정

```bash
# .env 파일
ALLOWED_IPS=127.0.0.1,::1,192.168.1.0/24,10.0.0.5

# 또는 docker-compose.yaml
environment:
  - ALLOWED_IPS=127.0.0.1,::1,192.168.1.0/24,10.0.0.5
```

### 지원하는 형식

1. **개별 IP 주소**
   ```
   127.0.0.1
   192.168.1.100
   2001:db8::1
   ```

2. **CIDR 표기법 (서브넷)**
   ```
   192.168.1.0/24        # 192.168.1.0 ~ 192.168.1.255
   10.0.0.0/8            # 10.0.0.0 ~ 10.255.255.255
   172.16.0.0/12         # 172.16.0.0 ~ 172.31.255.255
   ```

## 🔧 설정 방법

### 방법 1: 환경 변수

```bash
# Docker Compose
docker-compose up -d

# 환경 변수 설정
export ALLOWED_IPS="127.0.0.1,192.168.1.0/24"
docker-compose up -d
```

### 방법 2: docker-compose.yaml 수정

```yaml
services:
  docling-api:
    environment:
      - ALLOWED_IPS=127.0.0.1,::1,192.168.1.0/24
```

### 방법 3: app/config.py 직접 수정

```python
# app/config.py
ALLOWED_IPS = os.getenv("ALLOWED_IPS", "127.0.0.1,::1,특정IP").split(",")
```

## 📡 보호되는 엔드포인트

### 모든 API 엔드포인트가 보호됨

| 엔드포인트 | 메서드 | IP 체크 | 설명 |
|-----------|--------|---------|------|
| `/convert/with-images` | POST | ✅ | 이미지 추출과 함께 변환 |
| `/convert/markdown` | POST | ✅ | Markdown만 변환 |
| `/convert` | POST | ✅ | 변환 (deprecated) |
| `/images/{filename}` | GET | ✅ | 이미지 파일 조회 |
| `/figures/{filename}` | GET | ✅ | 이미지 파일 조회 (legacy) |
| `/` | GET | ❌ | API 정보 (공개) |
| `/health` | GET | ❌ | 헬스 체크 (공개) |

## 🧪 테스트

### 테스트 1: 로컬호스트에서 접근 (성공)

```bash
# 이미지 조회
curl http://localhost:8001/images/test.png
→ HTTP 200 OK

# 문서 변환
curl -X POST -F "file=@document.pdf" http://localhost:8001/convert/with-images
→ HTTP 200 OK
```

### 테스트 2: 외부 IP에서 접근 (차단)

```bash
# 허용되지 않은 IP에서 요청
curl http://your-server-ip:8001/images/test.png
→ HTTP 403 Forbidden
→ {"detail": "Access denied for IP: xxx.xxx.xxx.xxx"}
```

### 테스트 3: 허용된 서브넷에서 접근 (성공)

```bash
# 192.168.1.0/24 네트워크에서 접근
# (192.168.1.1 ~ 192.168.1.254)
curl http://api-server:8001/images/test.png
→ HTTP 200 OK
```

## 🔍 IP 확인 방법

API 서버는 다음 순서로 클라이언트 IP를 확인합니다:

1. **X-Forwarded-For 헤더** (프록시/로드밸런서 뒤에 있는 경우)
   ```
   X-Forwarded-For: 203.0.113.1, 198.51.100.1
   → 첫 번째 IP (203.0.113.1) 사용
   ```

2. **request.client.host** (직접 연결)
   ```
   Client IP: 192.168.1.100
   ```

## 🏗️ 프로덕션 배포 시나리오

### 시나리오 1: Nginx 리버스 프록시

```nginx
# nginx.conf
upstream docling_api {
    server docling-api:8001;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        # 사용자 인증 처리
        auth_request /auth;

        # 인증 성공 시 Docling API로 프록시
        proxy_pass http://docling_api;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }

    location /auth {
        # 인증 서버로 요청
        proxy_pass http://auth-server:8000/verify;
    }
}
```

**Docling API 설정**:
```bash
# Nginx IP만 허용
ALLOWED_IPS=172.18.0.5
```

### 시나리오 2: Kubernetes Ingress

```yaml
# kubernetes/deployment.yaml
apiVersion: v1
kind: Service
metadata:
  name: docling-api
  annotations:
    # 내부 서비스로만 노출
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"
spec:
  type: ClusterIP
  ports:
    - port: 8001
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docling-api
spec:
  template:
    spec:
      containers:
      - name: docling-api
        image: docling-api:latest
        env:
        - name: ALLOWED_IPS
          # Kubernetes 클러스터 내부 IP 대역만 허용
          value: "10.0.0.0/8,172.16.0.0/12"
```

### 시나리오 3: AWS API Gateway + Lambda

```yaml
# API Gateway에서 인증 처리
# Lambda가 Docling API 호출
# Docling API는 Lambda의 NAT Gateway IP만 허용

ALLOWED_IPS=52.xxx.xxx.xxx,54.xxx.xxx.xxx  # NAT Gateway IPs
```

## ⚠️ 주의사항

### 1. Docker 네트워크

Docker 컨테이너에서 실행 시, 클라이언트 IP가 Docker 네트워크 게이트웨이 IP로 나타납니다:

```bash
# localhost에서 요청해도
curl http://localhost:8001/images/test.png

# 컨테이너 안에서는 다음과 같이 보임
Client IP: 192.168.32.1  # Docker gateway
```

**해결책**: Docker 네트워크 대역을 화이트리스트에 추가
```python
ALLOWED_IPS = "127.0.0.1,::1,172.16.0.0/12,192.168.0.0/16"
```

### 2. 로드 밸런서 / 프록시

로드 밸런서나 리버스 프록시 뒤에 있을 경우, `X-Forwarded-For` 헤더 설정이 필요합니다:

```nginx
# Nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

# HAProxy
option forwardfor
```

### 3. 보안 고려사항

- ✅ **권장**: 내부 네트워크에서만 접근 가능하도록 설정
- ✅ **권장**: API 게이트웨이/인증 서버만 화이트리스트에 추가
- ❌ **비권장**: `0.0.0.0/0` (모든 IP 허용)
- ❌ **비권장**: 공개 인터넷에 직접 노출

## 🔄 마이그레이션 (JWT → IP 기반)

이전 버전에서 JWT 인증을 사용했다면:

### 변경 사항

1. **제거됨**:
   - `/login` 엔드포인트
   - JWT 토큰 생성/검증
   - 쿠키 기반 인증
   - `app/auth.py` (더 이상 사용 안 함)

2. **추가됨**:
   - IP 화이트리스트 체크
   - `app/ip_whitelist.py`
   - `ALLOWED_IPS` 환경 변수

### 기존 코드 수정

**이전 (JWT)**:
```python
# 로그인 필요
session = requests.Session()
session.post('http://api:8001/login', data={'username': 'admin', 'password': 'pass'})
response = session.post('http://api:8001/convert/with-images', files=files)
```

**현재 (IP 기반)**:
```python
# 로그인 불필요 (허용된 IP에서만 호출)
response = requests.post('http://api:8001/convert/with-images', files=files)
```

## 📚 관련 파일

- `app/config.py` - IP 화이트리스트 설정
- `app/ip_whitelist.py` - IP 검증 로직
- `app/main.py` - API 엔드포인트 (IP 체크 적용)
- `docker-compose.yaml` - 환경 변수 설정

## 🆘 문제 해결

### 403 Forbidden 오류

```json
{"detail": "Access denied for IP: xxx.xxx.xxx.xxx"}
```

**해결책**:
1. `ALLOWED_IPS`에 해당 IP 추가
2. Docker 네트워크 대역 확인
3. X-Forwarded-For 헤더 설정 확인

### Docker에서 localhost가 안 됨

```bash
# 컨테이너 안에서 localhost는 컨테이너 자신을 가리킴
# 호스트의 localhost에 접근하려면 host.docker.internal 사용 (Mac/Windows)
curl http://host.docker.internal:8001/
```

**또는 네트워크 모드 변경**:
```yaml
# docker-compose.yaml
services:
  docling-api:
    network_mode: host  # 호스트 네트워크 사용
```

## 📞 지원

문제가 발생하면:
1. API 로그 확인: `docker logs docling-api`
2. 클라이언트 IP 확인: `curl http://localhost:8001/` (allowed_ips 항목 확인)
3. 네트워크 설정 확인: `docker network inspect docling-server_docling-network`
