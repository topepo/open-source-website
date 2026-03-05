#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pdf2image>=1.17.0",
#     "pillow>=10.0.0",
#     "pyyaml>=6.0",
#     "rich>=13.0.0",
# ]
# ///
"""
Create thumbnails from a cheatsheet PDF.

Converts each page of a PDF into a PNG thumbnail and updates the
thumbnails key in the _index.md frontmatter of the same directory.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from pdf2image import convert_from_path
from PIL import Image
from rich.console import Console

console = Console(stderr=True)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str, str]:
    """Parse YAML frontmatter from markdown content."""
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        return {}, "", content

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, "", content

    yaml_section = "\n".join(lines[1:end_idx])

    try:
        frontmatter = yaml.safe_load(yaml_section) or {}
    except yaml.YAMLError as e:
        console.print(f"[yellow]Warning:[/] Failed to parse YAML: {e}")
        return {}, "", content

    remaining_content = "\n".join(lines[end_idx + 1 :])
    return frontmatter, yaml_section, remaining_content


def write_frontmatter(
    file_path: Path, frontmatter: dict[str, Any], remaining_content: str
) -> None:
    """Write updated frontmatter back to the markdown file."""
    yaml_content = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        indent=2,
    ).strip()

    new_content = f"---\n{yaml_content}\n---\n{remaining_content}"
    file_path.write_text(new_content, encoding="utf-8")


def create_thumbnails(pdf_path: Path, output_dir: Path, width: int = 600) -> list[str]:
    """Create PNG thumbnails of all pages of a PDF."""
    console.print(f"  Creating thumbnails from [cyan]{pdf_path.name}[/]")

    images = convert_from_path(pdf_path, dpi=150)
    if not images:
        console.print("  [red]✗[/] No images extracted from PDF")
        return []

    console.print(f"  Processing {len(images)} pages...")
    thumbnails: list[str] = []

    for page_num, image in enumerate(images, start=1):
        aspect_ratio = image.height / image.width
        new_height = int(width * aspect_ratio)
        resized = image.resize((width, new_height), Image.Resampling.LANCZOS)

        filename = f"page-{page_num}.png"
        resized.save(output_dir / filename, "PNG", optimize=True)
        thumbnails.append(filename)

    console.print(f"  [green]✓[/] Created {len(thumbnails)} thumbnails")
    return thumbnails


def update_index(index_path: Path, thumbnails: list[str]) -> bool:
    """Update the thumbnails key in _index.md frontmatter."""
    content = index_path.read_text(encoding="utf-8")
    frontmatter, _, remaining_content = parse_frontmatter(content)

    if not frontmatter:
        console.print(f"  [yellow]Warning:[/] No frontmatter in {index_path}")
        return False

    frontmatter["thumbnails"] = thumbnails
    write_frontmatter(index_path, frontmatter, remaining_content)
    console.print(f"  [green]✓[/] Updated {index_path}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create thumbnails from a cheatsheet PDF."
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        required=True,
        help="Full path to the cheatsheet PDF",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=600,
        help="Thumbnail width in pixels (default: 600)",
    )
    args = parser.parse_args()

    pdf_path: Path = args.pdf.resolve()
    if not pdf_path.is_file():
        console.print(f"[bold red]Error:[/] PDF not found: {pdf_path}")
        sys.exit(1)

    output_dir = pdf_path.parent
    console.print("\n[bold blue]Creating cheatsheet thumbnails[/]")
    console.print(f"  PDF:    {pdf_path}")
    console.print(f"  Output: {output_dir}")
    console.print(f"  Width:  {args.width}px\n")

    thumbnails = create_thumbnails(pdf_path, output_dir, width=args.width)
    if not thumbnails:
        console.print("\n[bold red]✗ No thumbnails created[/]\n")
        sys.exit(1)

    index_path = output_dir / "_index.md"
    if index_path.is_file():
        update_index(index_path, thumbnails)
    else:
        console.print(f"  [yellow]Warning:[/] No _index.md found in {output_dir}")

    console.print("\n[bold green]✓ Done![/]\n")


if __name__ == "__main__":
    main()
