"""Document conversion logic using Docling."""
import uuid
from pathlib import Path
from typing import Tuple, List, Dict
import base64
from io import BytesIO

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from PIL import Image

from app.config import FIGURES_DIR, SERVER_URL


class DocumentConverterService:
    """Service for converting documents to Markdown with extracted figures."""

    def __init__(self):
        """Initialize the document converter with optimal settings."""
        # Configure pipeline options for better figure extraction
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True  # Enable table structure
        pipeline_options.do_ocr = False  # Disable OCR for faster processing
        pipeline_options.images_scale = 2.0  # Higher resolution for better quality
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True  # Extract picture images

        # Create converter with PyPdfium backend for better compatibility
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
        self.figures_dir = FIGURES_DIR

    def convert_document(self, file_path: Path, original_filename: str, extract_images: bool = True) -> Tuple[str, List[Dict[str, str]]]:
        """
        Convert a document to Markdown and optionally extract figures.

        Args:
            file_path: Path to the input document
            original_filename: Original filename for reference
            extract_images: Whether to extract and save images (default: True)

        Returns:
            Tuple of (markdown_content, list of figure info dicts)
        """
        # Convert the document
        result = self.converter.convert(file_path)

        if result.status.value != "success":
            raise ValueError(f"Document conversion failed: {result.status}")

        doc = result.document

        # Extract and save figures if requested
        figures_info = []
        if extract_images:
            figures_info = self._extract_figures(doc, original_filename)
            # Generate markdown with figure references
            markdown = self._generate_markdown_with_figures(doc, figures_info)
        else:
            # Just export to markdown without image extraction
            markdown = doc.export_to_markdown()

        return markdown, figures_info

    def _extract_figures(self, doc, original_filename: str) -> List[Dict[str, str]]:
        """
        Extract figures (images, tables as images, etc.) from the document.

        Args:
            doc: DoclingDocument instance
            original_filename: Original filename for naming figures

        Returns:
            List of dicts with figure information (id, path, url, type)
        """
        figures_info = []
        base_name = Path(original_filename).stem

        # Extract images/pictures
        if hasattr(doc, 'pictures') and doc.pictures:
            for idx, picture in enumerate(doc.pictures):
                figure_info = self._save_picture(picture, base_name, idx)
                if figure_info:
                    figures_info.append(figure_info)

        # Extract tables as images if they have rendered content
        if hasattr(doc, 'tables') and doc.tables:
            for idx, table in enumerate(doc.tables):
                # Tables can be saved as images or kept as markdown
                # For now, we'll keep them as markdown tables
                # But you can extend this to render tables as images if needed
                pass

        return figures_info

    def _save_picture(self, picture, base_name: str, idx: int) -> Dict[str, str]:
        """
        Save a picture from the document.

        Args:
            picture: Picture item from DoclingDocument
            base_name: Base name for the file
            idx: Index of the picture

        Returns:
            Dict with figure info or None if failed
        """
        try:
            # Generate unique filename
            figure_id = str(uuid.uuid4())[:8]
            filename = f"{base_name}_figure_{idx}_{figure_id}.png"
            file_path = self.figures_dir / filename

            # Get caption from picture
            caption = f"Figure {idx + 1}"
            if hasattr(picture, 'text') and picture.text:
                caption = picture.text
            elif hasattr(picture, 'caption') and picture.caption:
                caption = picture.caption

            # Try multiple methods to extract image
            saved = False

            # Method 1: Check for pil_image attribute
            if hasattr(picture, 'pil_image') and picture.pil_image is not None:
                picture.pil_image.save(file_path, format='PNG')
                saved = True

            # Method 2: Check for image.pil_image
            elif hasattr(picture, 'image'):
                if picture.image is not None:
                    if hasattr(picture.image, 'pil_image') and picture.image.pil_image is not None:
                        picture.image.pil_image.save(file_path, format='PNG')
                        saved = True
                    elif isinstance(picture.image, bytes):
                        img = Image.open(BytesIO(picture.image))
                        img.save(file_path, format='PNG')
                        saved = True

            # Method 3: Check for data URI
            elif hasattr(picture, 'data') and picture.data:
                data_str = str(picture.data)
                if data_str.startswith('data:image'):
                    # Extract base64 data
                    base64_data = data_str.split(',', 1)[1] if ',' in data_str else data_str
                    img_bytes = base64.b64decode(base64_data)
                    img = Image.open(BytesIO(img_bytes))
                    img.save(file_path, format='PNG')
                    saved = True

            if saved:
                return {
                    'id': figure_id,
                    'filename': filename,
                    'path': str(file_path),
                    'url': f"{SERVER_URL}/static/figures/{filename}",
                    'type': 'image',
                    'caption': caption
                }

            return None

        except Exception as e:
            print(f"Error saving picture {idx}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_markdown_with_figures(self, doc, figures_info: List[Dict[str, str]]) -> str:
        """
        Generate Markdown content with figure references.

        Args:
            doc: DoclingDocument instance
            figures_info: List of figure information dicts

        Returns:
            Markdown string with figure references
        """
        # Get base markdown
        markdown = doc.export_to_markdown()

        # Replace <!-- image --> placeholders with actual image URLs
        for idx, figure in enumerate(figures_info):
            caption = figure['caption']
            url = figure['url']

            # Create markdown image syntax
            img_markdown = f"![{caption}]({url})"

            # Replace the first occurrence of <!-- image --> with the actual image
            markdown = markdown.replace('<!-- image -->', img_markdown, 1)

        return markdown


def create_converter() -> DocumentConverterService:
    """Factory function to create a converter instance."""
    return DocumentConverterService()
