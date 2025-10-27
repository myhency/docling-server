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

    def convert_document(
        self,
        file_path: Path,
        original_filename: str,
        extract_images: bool = True,
        output_format: str = "markdown"
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Convert a document to Markdown or HTML and optionally extract figures.

        Args:
            file_path: Path to the input document
            original_filename: Original filename for reference
            extract_images: Whether to extract and save images (default: True)
            output_format: Output format - "markdown" or "html" (default: "markdown")

        Returns:
            Tuple of (content, list of figure info dicts)
            content is markdown or html based on output_format
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

            # Generate content with figure references based on format
            if output_format.lower() == "html":
                content = self._generate_html_with_figures(doc, figures_info)
            else:
                content = self._generate_markdown_with_figures(doc, figures_info)
        else:
            # Export without image extraction
            if output_format.lower() == "html":
                content = doc.export_to_html()
            else:
                content = doc.export_to_markdown()

        return content, figures_info

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
                    'url': f"{SERVER_URL}/images/{filename}",
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

    def _generate_html_with_figures(self, doc, figures_info: List[Dict[str, str]]) -> str:
        """
        Generate HTML content with figure references maintaining original position.

        Since Docling's HTML export doesn't preserve image positions like Markdown does,
        we use Markdown as an intermediate format and convert it to HTML.

        Args:
            doc: DoclingDocument instance
            figures_info: List of figure information dicts

        Returns:
            HTML string with figure references at correct positions
        """
        # First get markdown with figures (which preserves positions)
        markdown = self._generate_markdown_with_figures(doc, figures_info)

        # Convert markdown to HTML manually with proper image positioning
        # Start with Docling's base HTML for styling
        base_html = doc.export_to_html()

        # Extract just the CSS from base HTML
        css_start = base_html.find('<style>')
        css_end = base_html.find('</style>') + 8 if base_html.find('</style>') != -1 else -1
        css = base_html[css_start:css_end] if css_start != -1 and css_end != -1 else ''

        # Convert markdown to HTML
        import re

        # Escape HTML special characters in markdown (except image tags)
        html_body = markdown

        # Convert markdown images to HTML images (preserve position!)
        # ![caption](url) -> <figure><img src="url" alt="caption" /><figcaption>caption</figcaption></figure>
        html_body = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            r'<figure class="document-figure"><img src="\2" alt="\1" title="\1" style="max-width: 100%; height: auto;" /><figcaption>\1</figcaption></figure>',
            html_body
        )

        # Convert markdown headers to HTML
        html_body = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
        html_body = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
        html_body = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)

        # Convert double line breaks to paragraphs
        paragraphs = html_body.split('\n\n')
        html_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # Don't wrap figures and headers in <p> tags
                if para.startswith('<figure') or para.startswith('<h1>') or para.startswith('<h2>') or para.startswith('<h3>'):
                    html_paragraphs.append(para)
                else:
                    # Replace single line breaks with <br> within paragraphs
                    para = para.replace('\n', '<br>\n')
                    html_paragraphs.append(f'<p>{para}</p>')

        html_body = '\n'.join(html_paragraphs)

        # Build final HTML with CSS from Docling and converted body
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8"/>
<title>Document</title>
<meta name="generator" content="Docling HTML Serializer"/>
{css}
</head>
<body>
<div class='page'>
{html_body}
</div>
</body>
</html>'''

        return html


def create_converter() -> DocumentConverterService:
    """Factory function to create a converter instance."""
    return DocumentConverterService()
