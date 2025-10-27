#!/usr/bin/env python3
"""
마크다운 파일의 이미지 URL을 변환하는 스크립트

사용법:
    python convert_markdown_urls.py input.md output.md
    python convert_markdown_urls.py input.md  # in-place 변경
"""
import sys
import re
from pathlib import Path

def convert_markdown_urls(content: str, from_port: int = 8002, to_port: int = 8001) -> str:
    """
    마크다운 내용의 이미지 URL을 변환합니다.

    Args:
        content: 마크다운 내용
        from_port: 기존 포트 번호 (기본: 8002)
        to_port: 새 포트 번호 (기본: 8001)

    Returns:
        변환된 마크다운 내용
    """
    # http://localhost:8002/figures/ -> http://localhost:8001/figures/
    pattern1 = rf'http://localhost:{from_port}/figures/'
    replacement1 = f'http://localhost:{to_port}/figures/'
    content = re.sub(pattern1, replacement1, content)

    # 선택적: /figures/ -> /images/로도 변경하고 싶다면 아래 주석 해제
    # content = content.replace('/figures/', '/images/')

    return content

def main():
    if len(sys.argv) < 2:
        print("사용법: python convert_markdown_urls.py input.md [output.md]")
        print("\n예제:")
        print("  python convert_markdown_urls.py document.md              # in-place 변경")
        print("  python convert_markdown_urls.py document.md output.md   # 새 파일로 저장")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else input_file

    if not input_file.exists():
        print(f"오류: 입력 파일을 찾을 수 없습니다: {input_file}")
        sys.exit(1)

    # 파일 읽기
    print(f"읽기: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # URL 변환
    original_content = content
    content = convert_markdown_urls(content)

    # 변경 사항 확인
    if content == original_content:
        print("변경할 URL이 없습니다.")
        return

    # 변경 사항 표시
    changes = 0
    for line_num, (old_line, new_line) in enumerate(zip(original_content.split('\n'), content.split('\n')), 1):
        if old_line != new_line:
            changes += 1
            print(f"\n줄 {line_num}:")
            print(f"  이전: {old_line}")
            print(f"  이후: {new_line}")

    # 파일 저장
    print(f"\n✓ {changes}개의 URL이 변경되었습니다.")
    print(f"저장: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ 완료!")

if __name__ == "__main__":
    main()
