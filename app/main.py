"""FastAPI application for document conversion service."""
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE, WEB_SERVER_URL, FIGURES_DIR, STATIC_DIR, ALLOWED_IPS
from app.converter import create_converter
from app.ip_whitelist import verify_ip_whitelist, get_client_ip

# Create FastAPI app
app = FastAPI(
    title="Document Converter API",
    description="Convert office documents to Markdown with extracted figures",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize converter
converter_service = create_converter()

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Document Converter API",
        "version": "1.0.0",
        "access_control": "IP-based whitelist",
        "allowed_ips": ALLOWED_IPS,
        "endpoints": {
            "convert/with-images": "POST /convert/with-images - Convert document to Markdown with extracted images",
            "convert/markdown": "POST /convert/markdown - Convert document to Markdown only (no image extraction)",
            "convert/html/with-images": "POST /convert/html/with-images - Convert document to HTML with extracted images",
            "convert/html": "POST /convert/html - Convert document to HTML only (no image extraction)",
            "convert": "POST /convert - Convert document to Markdown with extracted images (deprecated, use /convert/with-images)",
            "images": "GET /images/{filename} - Get image (IP whitelist required)",
            "figures": "GET /figures/{filename} - Get image (IP whitelist required, legacy)",
            "health": "GET /health - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "document-converter"}


async def _serve_image_with_ip_check(request: Request, filename: str):
    """
    Internal function to serve image files with IP-based access control.

    Args:
        request: FastAPI request object
        filename: Name of the image file to serve

    Returns:
        Image file response

    Raises:
        HTTPException: If IP not allowed, file not found, or access denied
    """
    # Verify IP is in whitelist
    client_ip = await verify_ip_whitelist(request, ALLOWED_IPS)

    # 파일 경로 생성
    file_path = FIGURES_DIR / filename

    # 파일 존재 여부 확인
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    # 경로 탐색 공격 방지 (path traversal attack prevention)
    try:
        file_path.resolve().relative_to(FIGURES_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - invalid path"
        )

    return FileResponse(file_path)


@app.get("/images/{filename}")
async def get_image(request: Request, filename: str):
    """
    Serve image files with IP-based access control (new endpoint).

    Only requests from whitelisted IPs are allowed.

    Args:
        request: FastAPI request object
        filename: Name of the image file to serve

    Returns:
        Image file response

    Raises:
        HTTPException: If IP not allowed or file not found
    """
    return await _serve_image_with_ip_check(request, filename)


@app.get("/figures/{filename}")
async def get_figure(request: Request, filename: str):
    """
    Serve image files with IP-based access control (legacy endpoint).

    This endpoint is provided for backward compatibility with existing markdown documents
    that reference /figures/... URLs. Only requests from whitelisted IPs are allowed.

    Args:
        request: FastAPI request object
        filename: Name of the image file to serve

    Returns:
        Image file response

    Raises:
        HTTPException: If IP not allowed or file not found
    """
    return await _serve_image_with_ip_check(request, filename)


async def _convert_document_helper(file: UploadFile, extract_images: bool, output_format: str = "markdown") -> Dict[str, Any]:
    """
    Helper function to convert document with optional image extraction.

    Args:
        file: Uploaded document file
        extract_images: Whether to extract and save images
        output_format: Output format - "markdown" or "html" (default: "markdown")

    Returns:
        JSON response dict

    Raises:
        HTTPException: If file validation fails or conversion errors occur
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename for temporary storage
    unique_id = str(uuid.uuid4())
    temp_filename = f"{unique_id}_{file.filename}"
    temp_file_path = UPLOAD_DIR / temp_filename

    try:
        # Save uploaded file
        with temp_file_path.open("wb") as buffer:
            content = await file.read()

            # Check file size
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size of {MAX_UPLOAD_SIZE / 1024 / 1024}MB"
                )

            buffer.write(content)

        # Convert document
        try:
            content, figures_info = converter_service.convert_document(
                temp_file_path,
                file.filename,
                extract_images=extract_images,
                output_format=output_format
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Conversion failed: {str(e)}"
            )

        # Prepare response with appropriate content key
        content_key = "html" if output_format.lower() == "html" else "markdown"
        response = {
            "status": "success",
            "original_filename": file.filename,
            "output_format": output_format,
            content_key: content,
            "figures": figures_info,
            "figures_count": len(figures_info)
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path.exists():
            temp_file_path.unlink()


@app.post("/convert/markdown")
async def convert_markdown_only(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert uploaded document to Markdown format only (without image extraction).

    Only requests from whitelisted IPs are allowed.

    Args:
        request: FastAPI request object
        file: Uploaded document file

    Returns:
        JSON response with markdown content only

    Raises:
        HTTPException: If IP not allowed, file validation fails, or conversion errors occur
    """
    # Verify IP is in whitelist
    await verify_ip_whitelist(request, ALLOWED_IPS)

    response = await _convert_document_helper(file, extract_images=False, output_format="markdown")
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@app.post("/convert/markdown/with-images")
async def convert_with_images(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert uploaded document to Markdown format with extracted images.

    Only requests from whitelisted IPs are allowed.

    Args:
        request: FastAPI request object
        file: Uploaded document file

    Returns:
        JSON response with markdown content and extracted figures information

    Raises:
        HTTPException: If IP not allowed, file validation fails, or conversion errors occur
    """
    # Verify IP is in whitelist
    await verify_ip_whitelist(request, ALLOWED_IPS)

    response = await _convert_document_helper(file, extract_images=True, output_format="markdown")
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@app.post("/convert")
async def convert_document(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert uploaded document to Markdown format with extracted images.

    DEPRECATED: Use /convert/with-images instead.
    Only requests from whitelisted IPs are allowed.

    Args:
        request: FastAPI request object
        file: Uploaded document file

    Returns:
        JSON response with markdown content and extracted figures information

    Raises:
        HTTPException: If IP not allowed, file validation fails, or conversion errors occur
    """
    # Verify IP is in whitelist
    await verify_ip_whitelist(request, ALLOWED_IPS)

    response = await _convert_document_helper(file, extract_images=True, output_format="markdown")
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@app.post("/convert/html")
async def convert_html_only(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert uploaded document to HTML format only (without image extraction).

    Only requests from whitelisted IPs are allowed.

    Args:
        request: FastAPI request object
        file: Uploaded document file

    Returns:
        JSON response with HTML content only

    Raises:
        HTTPException: If IP not allowed, file validation fails, or conversion errors occur
    """
    # Verify IP is in whitelist
    await verify_ip_whitelist(request, ALLOWED_IPS)

    response = await _convert_document_helper(file, extract_images=False, output_format="html")
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@app.post("/convert/html/with-images")
async def convert_html_with_images(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Convert uploaded document to HTML format with extracted images.

    Only requests from whitelisted IPs are allowed.

    Args:
        request: FastAPI request object
        file: Uploaded document file

    Returns:
        JSON response with HTML content and extracted figures information

    Raises:
        HTTPException: If IP not allowed, file validation fails, or conversion errors occur
    """
    # Verify IP is in whitelist
    await verify_ip_whitelist(request, ALLOWED_IPS)

    response = await _convert_document_helper(file, extract_images=True, output_format="html")
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)




if __name__ == "__main__":
    import uvicorn
    from app.config import API_HOST, API_PORT

    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
