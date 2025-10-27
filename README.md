# Office 문서 변환기 (Document Converter API)

Docling을 기반으로 한 REST API 서버로, Office 문서를 Markdown으로 변환하고 문서 내의 이미지, 표, 다이어그램 등을 자동으로 추출하여 저장합니다.

## 주요 기능

-   **다양한 문서 형식 지원**: PDF, DOCX, XLSX, PPTX, HTML, Markdown, CSV, 이미지 등
-   **다양한 출력 형식**: Markdown 또는 HTML로 변환
-   **네 가지 변환 모드**:
    -   **Markdown 빠른 모드** (`/convert/markdown`): Markdown만 빠르게 변환 (이미지 추출 없음)
    -   **Markdown 완전 모드** (`/convert/markdown/with-images`): 이미지 추출과 함께 Markdown 변환
    -   **HTML 빠른 모드** (`/convert/html`): HTML만 빠르게 변환 (이미지 추출 없음)
    -   **HTML 완전 모드** (`/convert/html/with-images`): 이미지 추출과 함께 HTML 변환
-   **자동 이미지 추출**: 문서 내의 이미지, 표, 다이어그램을 자동으로 추출하여 별도 파일로 저장
-   **IP 기반 접근 제어**: 허용된 IP에서만 API 호출 가능 (마이크로서비스 아키텍처에 최적화)
-   **보안 이미지 서빙**: 화이트리스트 IP에서만 추출된 이미지에 접근 가능
-   **REST API**: 간단한 HTTP API로 어디서든 사용 가능
-   **Docker 지원**: Docker Compose로 한 번에 실행

## 빠른 시작

### 필수 요구사항

-   Docker
-   Docker Compose

### 1. 서버 시작

```bash
# 저장소 클론 또는 프로젝트 디렉토리로 이동
cd docling-server

# Docker Compose로 서버 시작
docker-compose up -d
```

서버가 시작되면:

-   **REST API 서버**: `http://localhost:8001`
    -   문서 변환 API
    -   이미지 파일 서빙
    -   IP 화이트리스트 기반 접근 제어

### 2. 상태 확인

```bash
# API 서버 상태 확인
curl http://localhost:8001/health
```

응답:

```json
{
    "status": "healthy",
    "service": "document-converter"
}
```

### 3. 기본 정보 확인

```bash
# API 엔드포인트 목록 확인
curl http://localhost:8001/
```

응답에서 사용 가능한 모든 엔드포인트와 허용된 IP 목록을 확인할 수 있습니다

## API 사용법

### API 엔드포인트

서버는 다음 엔드포인트를 제공합니다 (모든 엔드포인트는 IP 화이트리스트 검증 필요):

#### 문서 변환 - Markdown

1. **`POST /convert/markdown`** - Markdown만 반환 (빠른 변환, 이미지 추출 없음)
2. **`POST /convert/markdown/with-images`** - 이미지 추출과 함께 Markdown 반환 (완전한 변환)
3. **`POST /convert`** - (Deprecated) `/convert/markdown/with-images`와 동일

#### 문서 변환 - HTML

4. **`POST /convert/html`** - HTML만 반환 (빠른 변환, 이미지 추출 없음)
5. **`POST /convert/html/with-images`** - 이미지 추출과 함께 HTML 반환 (완전한 변환)

#### 이미지 접근

6. **`GET /images/{filename}`** - 추출된 이미지 조회 (IP 화이트리스트 검증)
7. **`GET /figures/{filename}`** - 추출된 이미지 조회 (레거시 엔드포인트, IP 화이트리스트 검증)

### 1. Markdown만 변환 (빠른 변환)

**Endpoint**: `POST /convert/markdown`

이미지를 추출하지 않고 Markdown 텍스트만 빠르게 변환합니다.

**요청**:

```bash
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/markdown
```

**응답 예시**:

```json
{
    "status": "success",
    "original_filename": "document.pdf",
    "markdown": "# 문서 제목\n\n본문 내용...\n\n<!-- image -->\n\n...",
    "figures": [],
    "figures_count": 0
}
```

### 2. 이미지 추출과 함께 변환 (완전한 변환)

**Endpoint**: `POST /convert/markdown/with-images`

문서 내의 이미지를 추출하여 별도 파일로 저장하고, Markdown에 이미지 URL을 포함합니다.

**요청**:

```bash
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/markdown/with-images
```

**응답 예시**:

```json
{
    "status": "success",
    "original_filename": "document.pdf",
    "output_format": "markdown",
    "markdown": "![Figure 1](http://localhost:8001/images/document_figure_0_abc123.png)\n\n## 문서 제목\n\n본문 내용...",
    "figures": [
        {
            "id": "abc123",
            "filename": "document_figure_0_abc123.png",
            "path": "/app/static/figures/document_figure_0_abc123.png",
            "url": "http://localhost:8001/images/document_figure_0_abc123.png",
            "type": "image",
            "caption": "Figure 1"
        }
    ],
    "figures_count": 1
}
```

### 3. HTML만 변환 (빠른 변환)

**Endpoint**: `POST /convert/html`

이미지를 추출하지 않고 HTML로만 빠르게 변환합니다.

**요청**:

```bash
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/html
```

**응답 예시**:

```json
{
    "status": "success",
    "original_filename": "document.pdf",
    "output_format": "html",
    "html": "<!DOCTYPE html>\n<html>\n<head>...</head>\n<body>\n<h1>문서 제목</h1>\n<p>본문 내용...</p>\n</body>\n</html>",
    "figures": [],
    "figures_count": 0
}
```

### 4. 이미지 추출과 함께 HTML 변환 (완전한 변환)

**Endpoint**: `POST /convert/html/with-images`

문서 내의 이미지를 추출하여 별도 파일로 저장하고, HTML에 이미지 태그를 포함합니다.

**요청**:

```bash
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/html/with-images
```

**응답 예시**:

```json
{
    "status": "success",
    "original_filename": "document.pdf",
    "output_format": "html",
    "html": "<!DOCTYPE html>\n<html>\n<head>...</head>\n<body>\n<figure><img src=\"http://localhost:8001/images/document_figure_0_abc123.png\" alt=\"Figure 1\"/><figcaption>Figure 1</figcaption></figure>\n<h1>문서 제목</h1>\n<p>본문 내용...</p>\n</body>\n</html>",
    "figures": [
        {
            "id": "abc123",
            "filename": "document_figure_0_abc123.png",
            "path": "/app/static/figures/document_figure_0_abc123.png",
            "url": "http://localhost:8001/images/document_figure_0_abc123.png",
            "type": "image",
            "caption": "Figure 1"
        }
    ],
    "figures_count": 1
}
```

### Python에서 사용하기

```python
import requests

# 방법 1: Markdown만 빠르게 변환
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8001/convert/markdown', files=files)

result = response.json()
print(f"변환 상태: {result['status']}")
print(f"\nMarkdown 내용:\n{result['markdown']}")

# 방법 2: 이미지 추출과 함께 Markdown 변환
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8001/convert/markdown/with-images', files=files)

result = response.json()
print(f"변환 상태: {result['status']}")
print(f"추출된 이미지 수: {result['figures_count']}")
print(f"\nMarkdown 내용:\n{result['markdown']}")

# 방법 3: HTML로 변환
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8001/convert/html', files=files)

result = response.json()
print(f"HTML 내용:\n{result['html']}")

# 방법 4: 이미지 추출과 함께 HTML 변환
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8001/convert/html/with-images', files=files)

result = response.json()
print(f"추출된 이미지 수: {result['figures_count']}")
print(f"\nHTML 내용:\n{result['html']}")

# 이미지 URL 출력
for figure in result['figures']:
    print(f"이미지: {figure['url']}")
```

### JavaScript/Node.js에서 사용하기

```javascript
const FormData = require("form-data");
const fs = require("fs");
const axios = require("axios");

// 방법 1: Markdown만 빠르게 변환
const form1 = new FormData();
form1.append("file", fs.createReadStream("document.pdf"));

axios
    .post("http://localhost:8001/convert/markdown", form1, {
        headers: form1.getHeaders(),
    })
    .then((response) => {
        const result = response.data;
        console.log(`변환 상태: ${result.status}`);
        console.log(`\nMarkdown 내용:\n${result.markdown}`);
    })
    .catch((error) => {
        console.error("에러:", error.response?.data || error.message);
    });

// 방법 2: 이미지 추출과 함께 Markdown 변환
const form2 = new FormData();
form2.append("file", fs.createReadStream("document.pdf"));

axios
    .post("http://localhost:8001/convert/markdown/with-images", form2, {
        headers: form2.getHeaders(),
    })
    .then((response) => {
        const result = response.data;
        console.log(`변환 상태: ${result.status}`);
        console.log(`추출된 이미지 수: ${result.figures_count}`);
        console.log(`\nMarkdown 내용:\n${result.markdown}`);

        result.figures.forEach((figure) => {
            console.log(`이미지: ${figure.url}`);
        });
    })
    .catch((error) => {
        console.error("에러:", error.response?.data || error.message);
    });

// 방법 3: 이미지 추출과 함께 HTML 변환
const form3 = new FormData();
form3.append("file", fs.createReadStream("document.pdf"));

axios
    .post("http://localhost:8001/convert/html/with-images", form3, {
        headers: form3.getHeaders(),
    })
    .then((response) => {
        const result = response.data;
        console.log(`변환 상태: ${result.status}`);
        console.log(`추출된 이미지 수: ${result.figures_count}`);
        console.log(`\nHTML 내용:\n${result.html}`);

        result.figures.forEach((figure) => {
            console.log(`이미지: ${figure.url}`);
        });
    })
    .catch((error) => {
        console.error("에러:", error.response?.data || error.message);
    });
```

### cURL로 파일 변환 후 저장

```bash
# Markdown만 빠르게 변환하여 저장
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/markdown \
  | jq -r '.markdown' > output.md

# 이미지 추출과 함께 Markdown 변환하여 JSON으로 저장
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/markdown/with-images \
  -o result.json

# 이미지 추출과 함께 Markdown 변환하여 Markdown만 저장
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/markdown/with-images \
  | jq -r '.markdown' > output.md

# HTML로 변환하여 저장
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/html/with-images \
  | jq -r '.html' > output.html
```

## IP 기반 접근 제어

이 API 서버는 IP 화이트리스트 기반 접근 제어를 사용합니다. 이는 마이크로서비스 아키텍처에서 API 게이트웨이나 인증 서버가 별도로 존재하는 경우에 적합합니다.

### 동작 방식

- 모든 API 엔드포인트는 요청자의 IP 주소를 검증합니다
- 허용된 IP 목록에 있는 IP만 API를 호출할 수 있습니다
- Docker 컨테이너 네트워크, 프록시, 로드밸런서 등을 고려하여 `X-Forwarded-For` 헤더도 확인합니다

### 기본 허용 IP 목록

기본적으로 다음 IP 범위가 허용됩니다:

- `127.0.0.1` - 로컬호스트 (IPv4)
- `::1` - 로컬호스트 (IPv6)
- `172.16.0.0/12` - Docker 네트워크 범위
- `192.168.0.0/16` - 사설 네트워크 범위
- `10.0.0.0/8` - 사설 네트워크 범위

### IP 화이트리스트 설정

환경 변수 `ALLOWED_IPS`를 사용하여 허용 IP를 설정할 수 있습니다:

```bash
# .env 파일에 추가
ALLOWED_IPS=127.0.0.1,::1,192.168.1.0/24,10.0.0.5

# 또는 docker-compose.yaml에서
environment:
  - ALLOWED_IPS=127.0.0.1,::1,192.168.1.0/24,10.0.0.5
```

### 프로덕션 환경 설정 예시

#### 1. 특정 서버만 허용

```yaml
# docker-compose.yaml
environment:
    - ALLOWED_IPS=10.0.1.10,10.0.1.11,10.0.1.12
```

#### 2. Kubernetes 환경

```yaml
# Kubernetes ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
    name: docling-config
data:
    ALLOWED_IPS: "10.244.0.0/16" # Pod network CIDR
```

#### 3. Nginx 리버스 프록시 사용 시

Nginx가 `X-Forwarded-For` 헤더를 설정하도록 구성:

```nginx
location /api/ {
    proxy_pass http://docling-api:8001/;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $host;
}
```

### 접근 거부 시 응답

허용되지 않은 IP에서 접근 시:

```json
{
    "detail": "Access forbidden - IP 203.0.113.1 is not in whitelist"
}
```

자세한 내용은 [IP_ACCESS_CONTROL.md](./IP_ACCESS_CONTROL.md) 문서를 참조하세요

## 지원 파일 형식

| 형식       | 확장자                                            |
| ---------- | ------------------------------------------------- |
| PDF        | `.pdf`                                            |
| Word       | `.docx`                                           |
| Excel      | `.xlsx`                                           |
| PowerPoint | `.pptx`                                           |
| HTML       | `.html`, `.htm`                                   |
| Markdown   | `.md`                                             |
| CSV        | `.csv`                                            |
| 이미지     | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp` |

## 프로젝트 구조

```
docling-server/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 애플리케이션
│   ├── converter.py      # 문서 변환 로직
│   ├── config.py         # 설정
│   └── ip_whitelist.py   # IP 화이트리스트 검증
├── static/
│   └── figures/          # 추출된 이미지 저장 위치
├── uploads/              # 임시 업로드 디렉토리
├── web_server.py         # 정적 파일 서버 (deprecated)
├── requirements.txt      # Python 의존성
├── Dockerfile
├── docker-compose.yaml
└── README.md
```

## 아키텍처

### 마이크로서비스 아키텍처

**REST API 서버** (포트 8001)

-   문서 변환 로직 처리
-   Markdown 및 HTML 생성
-   이미지 추출 및 저장
-   **IP 화이트리스트 기반 접근 제어** (보안)
-   이미지 파일 서빙
-   CORS 지원

이 구성에서는 모든 기능이 하나의 API 서버에 통합되어 있으며, IP 화이트리스트를 통해 허용된 서버만 API를 호출할 수 있습니다. 사용자 인증은 별도의 API 게이트웨이나 인증 서버에서 처리하는 것을 권장합니다.

### 전형적인 배포 구조

```
[사용자] → [API 게이트웨이/인증 서버] → [Docling 변환 서버]
                ↓ 인증 처리                  ↓ IP 검증
           JWT/세션 관리              문서 변환 & 이미지 추출
```

**보안 모델**:

1. API 게이트웨이/인증 서버가 사용자 인증 처리
2. 인증된 요청만 Docling 서버로 전달
3. Docling 서버는 API 게이트웨이의 IP만 허용
4. 최종 사용자는 Docling 서버에 직접 접근 불가

## 환경 변수

`docker-compose.yaml` 또는 `.env` 파일에서 다음 환경 변수를 설정할 수 있습니다:

### API 서버

| 변수              | 기본값                                                              | 설명                                                                       |
| ----------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `API_HOST`        | `0.0.0.0`                                                           | API 서버 호스트                                                            |
| `API_PORT`        | `8001`                                                              | API 서버 포트                                                              |
| `API_SERVER_URL`  | `http://localhost:8001`                                             | API 서버 URL (이미지 URL 생성에 사용)                                      |
| `ALLOWED_IPS`     | `127.0.0.1,::1,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8`            | 허용된 IP 주소 목록 (쉼표로 구분, CIDR 표기 지원)                          |
| `MAX_UPLOAD_SIZE` | `52428800` (50MB)                                                   | 최대 업로드 파일 크기 (바이트)                                             |
| `UPLOAD_DIR`      | `/app/uploads`                                                      | 임시 업로드 디렉토리                                                       |
| `FIGURES_DIR`     | `/app/static/figures`                                               | 추출된 이미지 저장 디렉토리                                                |

## 보안 설정

### IP 기반 접근 제어

이 API 서버는 IP 화이트리스트를 사용하여 접근을 제어합니다.

#### 보안 기능

-   **IP 화이트리스트**: 허용된 IP만 API 접근 가능
-   **CIDR 표기 지원**: IP 범위를 유연하게 설정 가능
-   **프록시 지원**: X-Forwarded-For 헤더를 통한 실제 클라이언트 IP 확인
-   **경로 탐색 방지**: Directory traversal 공격 차단

### 프로덕션 환경 설정

#### 1. IP 화이트리스트 구성

프로덕션 환경에서는 특정 서버의 IP만 허용하도록 설정하세요:

```bash
# .env 파일에 추가
ALLOWED_IPS=10.0.1.10,10.0.1.11,192.168.1.0/24

# 또는 docker-compose.yaml에서
environment:
  - ALLOWED_IPS=10.0.1.10,10.0.1.11,192.168.1.0/24
```

#### 2. CORS 설정

프로덕션에서는 CORS를 특정 도메인으로 제한하세요. **app/main.py**에서:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 실제 도메인으로 변경
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

#### 3. HTTPS 설정

프로덕션에서는 반드시 HTTPS를 사용하고, Nginx나 AWS ALB 같은 리버스 프록시를 통해 SSL 종료를 처리하세요.

#### 4. 프록시 설정

Nginx 리버스 프록시 예시:

```nginx
location /api/ {
    proxy_pass http://docling-api:8001/;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Host $host;
}
```

### 테스트 방법

#### 1. 허용된 IP에서 접근 (성공)

```bash
# 로컬호스트에서 API 호출
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/markdown
```

#### 2. 허용되지 않은 IP에서 접근 (실패)

허용되지 않은 IP에서 접근 시 다음과 같은 응답을 받습니다:

```json
{
    "detail": "Access forbidden - IP 203.0.113.1 is not in whitelist"
}
```

#### 3. Docker 네트워크 테스트

Docker Compose로 실행 중인 경우, 컨테이너 간 통신을 테스트:

```bash
# API 컨테이너 내부에서 테스트
docker exec -it docling-api curl http://localhost:8001/health
```

## 개발 모드

개발 중 코드 변경시 자동 재시작을 원한다면:

1. `docker-compose.yaml`에서 volumes 섹션의 주석을 해제:

```yaml
volumes:
    - ./static/figures:/app/static/figures
    - ./app:/app/app # 이 줄의 주석 해제
```

2. 컨테이너 재시작:

```bash
docker-compose down
docker-compose up -d
```

## 로컬 개발 (Docker 없이)

Docker 없이 로컬에서 개발하려면:

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python -m app.main
# 또는
uvicorn app.main:app --reload
```

## 문제 해결

### 포트가 이미 사용 중인 경우

`docker-compose.yaml`에서 포트를 변경:

```yaml
ports:
    - "8080:8000" # 호스트 포트를 8080으로 변경
```

### 메모리 부족

Docker Desktop 설정에서 메모리 할당을 늘려주세요 (최소 4GB 권장).

### 이미지가 추출되지 않는 경우

일부 PDF 문서의 경우 이미지 추출이 제한될 수 있습니다. 이런 경우:

-   PDF가 암호화되어 있는지 확인
-   PDF의 이미지가 임베디드 형식인지 확인

## 성능 최적화

### 대용량 파일 처리

`app/config.py`에서 최대 파일 크기 조정:

```python
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
```

### OCR 활성화 (스캔된 문서용)

스캔된 PDF의 텍스트를 추출하려면 `app/converter.py`에서 OCR 활성화:

```python
pipeline_options.do_ocr = True
```

그리고 `requirements.txt`에 OCR 라이브러리 추가:

```
docling[easyocr]==2.10.0
```

## API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

-   Swagger UI: http://localhost:8001/docs
-   ReDoc: http://localhost:8001/redoc

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해 주세요.

## 기술 스택

-   **FastAPI**: 현대적이고 빠른 Python 웹 프레임워크
-   **Docling**: IBM Research의 문서 처리 라이브러리
-   **Docker**: 컨테이너화 및 배포
-   **Python 3.11**: 최신 Python 기능 활용

## 참고 자료

-   [Docling 공식 문서](https://github.com/docling-project/docling)
-   [FastAPI 문서](https://fastapi.tiangolo.com/)
-   [Docker 문서](https://docs.docker.com/)
