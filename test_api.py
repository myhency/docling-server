#!/usr/bin/env python3
"""
Test script for the Document Converter API.

Usage:
    python test_api.py <path_to_document>

Example:
    python test_api.py document.pdf
"""

import sys
import requests
import json
from pathlib import Path


def test_convert(file_path: str, api_url: str = "http://localhost:8000"):
    """Test the document conversion API."""

    # Check if file exists
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        return False

    print(f"Testing API at {api_url}")
    print(f"Converting file: {file_path}")
    print("-" * 60)

    # Check health
    try:
        health_response = requests.get(f"{api_url}/health")
        health_response.raise_for_status()
        print(f"✓ Health check: {health_response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        print("Make sure the server is running: docker-compose up -d")
        return False

    # Convert document
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            print(f"\nUploading and converting document...")
            response = requests.post(f"{api_url}/convert", files=files)
            response.raise_for_status()

        result = response.json()

        print(f"\n✓ Conversion successful!")
        print(f"  - Original filename: {result['original_filename']}")
        print(f"  - Figures extracted: {result['figures_count']}")

        # Print markdown preview
        markdown = result['markdown']
        print(f"\n{'='*60}")
        print("MARKDOWN OUTPUT (first 500 chars):")
        print(f"{'='*60}")
        print(markdown[:500])
        if len(markdown) > 500:
            print(f"\n... ({len(markdown) - 500} more characters)")

        # Print figures info
        if result['figures']:
            print(f"\n{'='*60}")
            print("EXTRACTED FIGURES:")
            print(f"{'='*60}")
            for i, figure in enumerate(result['figures'], 1):
                print(f"\n{i}. {figure['filename']}")
                print(f"   URL: {figure['url']}")
                print(f"   Type: {figure['type']}")
                print(f"   Caption: {figure['caption']}")

        # Save full result to JSON
        output_file = "result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Full result saved to: {output_file}")

        # Save markdown to file
        markdown_file = "output.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        print(f"✓ Markdown saved to: {markdown_file}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"\n✗ Conversion failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <path_to_document>")
        print("\nExample:")
        print("  python test_api.py document.pdf")
        print("  python test_api.py presentation.pptx")
        sys.exit(1)

    file_path = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"

    success = test_convert(file_path, api_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
