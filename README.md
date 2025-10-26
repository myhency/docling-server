# Office 문서 변환기 (Document Converter API)

Docling을 기반으로 한 REST API 서버로, Office 문서를 Markdown으로 변환하고 문서 내의 이미지, 표, 다이어그램 등을 자동으로 추출하여 저장합니다.

## 주요 기능

- **다양한 문서 형식 지원**: PDF, DOCX, XLSX, PPTX, HTML, Markdown, CSV, 이미지 등
- **Markdown 변환**: 모든 문서를 깔끔한 Markdown 형식으로 변환
- **두 가지 변환 모드**:
  - **빠른 모드** (`/convert/markdown`): Markdown만 빠르게 변환 (이미지 추출 없음)
  - **완전 모드** (`/convert/with-images`): 이미지 추출과 함께 완전한 변환
- **자동 이미지 추출**: 문서 내의 이미지, 표, 다이어그램을 자동으로 추출하여 별도 파일로 저장
- **웹 접근 가능**: 추출된 이미지는 웹 URL로 접근 가능
- **REST API**: 간단한 HTTP API로 어디서든 사용 가능
- **Docker 지원**: Docker Compose로 한 번에 실행

## 빠른 시작

### 필수 요구사항

- Docker
- Docker Compose

### 1. 서버 시작

```bash
# 저장소 클론 또는 프로젝트 디렉토리로 이동
cd docling-server

# Docker Compose로 두 서버 모두 시작
docker-compose up -d

# 또는 개별적으로 시작
docker-compose up -d docling-api  # REST API 서버만
docker-compose up -d docling-web  # 웹 서버만
```

서버가 시작되면:
- **REST API 서버**: `http://localhost:8001`
- **웹 서버 (이미지 제공)**: `http://localhost:8002`

### 2. 상태 확인

```bash
# REST API 서버 상태 확인
curl http://localhost:8001/health

# 웹 서버 상태 확인
curl http://localhost:8002/
```

응답:
```json
{
  "status": "healthy",
  "service": "document-converter"
}
```

## API 사용법

### API 엔드포인트

서버는 두 가지 주요 엔드포인트를 제공합니다:

1. **`POST /convert/markdown`** - Markdown만 반환 (빠른 변환, 이미지 추출 없음)
2. **`POST /convert/with-images`** - 이미지 추출과 함께 Markdown 반환 (느리지만 완전한 변환)

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

**Endpoint**: `POST /convert/with-images`

문서 내의 이미지를 추출하여 별도 파일로 저장하고, Markdown에 이미지 URL을 포함합니다.

**요청**:
```bash
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/with-images
```

**응답 예시**:
```json
{
  "status": "success",
  "original_filename": "document.pdf",
  "markdown": "![Figure 1](http://localhost:8002/figures/document_figure_0_abc123.png)\n\n## 문서 제목\n\n본문 내용...",
  "figures": [
    {
      "id": "abc123",
      "filename": "document_figure_0_abc123.png",
      "path": "/app/static/figures/document_figure_0_abc123.png",
      "url": "http://localhost:8002/figures/document_figure_0_abc123.png",
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

# 방법 2: 이미지 추출과 함께 변환
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8001/convert/with-images', files=files)

result = response.json()
print(f"변환 상태: {result['status']}")
print(f"추출된 이미지 수: {result['figures_count']}")
print(f"\nMarkdown 내용:\n{result['markdown']}")

# 이미지 URL 출력
for figure in result['figures']:
    print(f"이미지: {figure['url']}")
```

### JavaScript/Node.js에서 사용하기

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

// 방법 1: Markdown만 빠르게 변환
const form1 = new FormData();
form1.append('file', fs.createReadStream('document.pdf'));

axios.post('http://localhost:8001/convert/markdown', form1, {
    headers: form1.getHeaders()
})
.then(response => {
    const result = response.data;
    console.log(`변환 상태: ${result.status}`);
    console.log(`\nMarkdown 내용:\n${result.markdown}`);
})
.catch(error => {
    console.error('에러:', error.response?.data || error.message);
});

// 방법 2: 이미지 추출과 함께 변환
const form2 = new FormData();
form2.append('file', fs.createReadStream('document.pdf'));

axios.post('http://localhost:8001/convert/with-images', form2, {
    headers: form2.getHeaders()
})
.then(response => {
    const result = response.data;
    console.log(`변환 상태: ${result.status}`);
    console.log(`추출된 이미지 수: ${result.figures_count}`);
    console.log(`\nMarkdown 내용:\n${result.markdown}`);

    result.figures.forEach(figure => {
        console.log(`이미지: ${figure.url}`);
    });
})
.catch(error => {
    console.error('에러:', error.response?.data || error.message);
});
```

### cURL로 파일 변환 후 저장

```bash
# Markdown만 빠르게 변환하여 저장
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/markdown \
  | jq -r '.markdown' > output.md

# 이미지 추출과 함께 변환하여 JSON으로 저장
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/with-images \
  -o result.json

# 이미지 추출과 함께 변환하여 Markdown만 저장
curl -X POST \
  -F "file=@document.pdf" \
  http://localhost:8001/convert/with-images \
  | jq -r '.markdown' > output.md
```

## 지원 파일 형식

| 형식 | 확장자 |
|-----|--------|
| PDF | `.pdf` |
| Word | `.docx` |
| Excel | `.xlsx` |
| PowerPoint | `.pptx` |
| HTML | `.html`, `.htm` |
| Markdown | `.md` |
| CSV | `.csv` |
| 이미지 | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp` |

## 프로젝트 구조

```
docling-server/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 애플리케이션
│   ├── converter.py      # 문서 변환 로직
│   └── config.py         # 설정
├── static/
│   └── figures/          # 추출된 이미지 저장 위치
├── uploads/              # 임시 업로드 디렉토리
├── requirements.txt      # Python 의존성
├── Dockerfile
├── docker-compose.yaml
└── README.md
```

## 아키텍처

이 프로젝트는 두 개의 독립적인 서버로 구성됩니다:

1. **REST API 서버** (포트 8001)
   - 문서 변환 로직 처리
   - Markdown 생성
   - 이미지 추출 및 저장

2. **웹 서버** (포트 8002)
   - 정적 파일 (이미지) 제공
   - CORS 지원

두 서버는 공유 볼륨을 통해 figures 디렉토리를 공유합니다.

## 환경 변수

`docker-compose.yaml` 또는 `.env` 파일에서 다음 환경 변수를 설정할 수 있습니다:

### API 서버
| 변수 | 기본값 | 설명 |
|-----|--------|------|
| `API_HOST` | `0.0.0.0` | API 서버 호스트 |
| `API_PORT` | `8001` | API 서버 포트 |
| `WEB_SERVER_URL` | `http://localhost:8002` | 웹 서버 URL (이미지 URL 생성에 사용) |

### 웹 서버
| 변수 | 기본값 | 설명 |
|-----|--------|------|
| `WEB_PORT` | `8002` | 웹 서버 포트 |

## 개발 모드

개발 중 코드 변경시 자동 재시작을 원한다면:

1. `docker-compose.yaml`에서 volumes 섹션의 주석을 해제:
```yaml
volumes:
  - ./static/figures:/app/static/figures
  - ./app:/app/app  # 이 줄의 주석 해제
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
  - "8080:8000"  # 호스트 포트를 8080으로 변경
```

### 메모리 부족

Docker Desktop 설정에서 메모리 할당을 늘려주세요 (최소 4GB 권장).

### 이미지가 추출되지 않는 경우

일부 PDF 문서의 경우 이미지 추출이 제한될 수 있습니다. 이런 경우:
- PDF가 암호화되어 있는지 확인
- PDF의 이미지가 임베디드 형식인지 확인

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

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해 주세요.

## 기술 스택

- **FastAPI**: 현대적이고 빠른 Python 웹 프레임워크
- **Docling**: IBM Research의 문서 처리 라이브러리
- **Docker**: 컨테이너화 및 배포
- **Python 3.11**: 최신 Python 기능 활용

## 참고 자료

- [Docling 공식 문서](https://github.com/docling-project/docling)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Docker 문서](https://docs.docker.com/)
