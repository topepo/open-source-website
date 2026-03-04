# Plan: `scripts/format-transcription.py`

## Overview

The script reads `transcription.vtt` (and metadata from `_index.md`) from each
video directory, sends it to the Anthropic API, and writes the resulting HTML
fragment to `transcription.html`.  The implementation closely mirrors
`scripts/transcribe.py`: asyncio semaphore, rate limiter, Rich progress bar,
exponential backoff, PEP 723 inline dependencies.

After the API call, a post-processing pass injects `<a href="...">` links for
mentions of known people and software packages (loaded from the site's content
directories).

---

## Decisions made

1. **Context injection from `_index.md`** — yes; passing title, software tags,
   and people listed in the frontmatter helps the model spell proper nouns
   correctly and recognise whether the video is a solo talk or panel.

2. **Multi-speaker handling** — yes; the prompt instructs the model to start a
   new paragraph on clear speaker changes without inventing names.

3. **Chunked processing for long videos** — yes, implemented as Phase 3
   (not optional).

4. **Model** — `claude-sonnet-4-6` (default; override with `--model`).

5. **Strip Markdown fences** — yes; models sometimes wrap the output in
   ` ```html … ``` `.

6. **Blockquotes must contain `<a>` elements** — yes; same rule as normal text.

7. **Entity linking** — a post-processing step (Phase 4) wraps the first
   occurrence of each known person name and software package name in an
   `<a href="…">` tag, using the site's `/content/people/` and
   `/content/software/` directories as the source of truth.  The
   `data/software-match-ignore.toml` list prevents linking common English words
   that coincidentally match a software slug.

8. **No nested `<a>` elements** — `<a>` cannot be nested in HTML.  When an
   entity match occurs inside an existing `<a data-t="…">` element, that
   element is split into up to three pieces around the match.  The surrounding
   text pieces keep the original `data-t` attribute; the matched fragment gets
   only `href` (no `data-t`).

9. **Skip if `transcribe: false`** — if `_index.md` frontmatter contains
   `transcribe: false`, the directory is skipped (counted as "excluded").
   A missing `transcribe` key is treated as `true` (i.e. proceed normally).

10. **Section headings** — the model may emit `<h3>` elements as short headings
    that group thematically related paragraphs.  Sentence casing; used sparingly.

---

## Phase 1 — Prompt design

This is the most important phase.  The `PROMPT` constant (system message) lives
at the top of the script.

### 1.1  System message (`PROMPT`)

```python
PROMPT = """\
You convert WebVTT transcription files into clean HTML fragments for video pages.

## Your role
You receive a WebVTT file, optionally preceded by metadata about the video.
You return an HTML fragment — nothing else.

## Strict output rules
- Output ONLY the HTML fragment. No explanations, no Markdown fences
  (no ```html), no prose before or after the HTML.
- Use ONLY these four element types: <h3>  <p>  <a>  <blockquote>
- Do NOT include <html>, <head>, <body>, <div>, <span>, <h1>, <h2>, <h4>–<h6>,
  or any other element.
- Do NOT add class, id, style, or any attribute other than data-t on <a>.

## Timestamps → data-t attribute
Every <a> element MUST have a data-t attribute set to the start timestamp of
that VTT cue expressed in WHOLE SECONDS (floor, not round).

Conversion formula:  data-t = HH*3600 + MM*60 + SS  (discard milliseconds)

  00:00:00.000  →  data-t="0"
  00:01:30.500  →  data-t="90"
  00:04:46.999  →  data-t="286"
  01:02:03.100  →  data-t="3723"

## Text — keep it verbatim
Do NOT paraphrase, correct grammar, fix spelling, or improve wording.
Copy the spoken words exactly as they appear in the VTT, including filler
words ("um", "uh", "sort of", "you know") and false starts.

## Combining multi-cue sentences
A sentence in the VTT often spans several consecutive cues.
Join them into a single sentence; each cue becomes its own <a> element.
Put a single space between consecutive <a> elements within a sentence.

## Paragraphs
Wrap sentences in <p> elements.  Start a NEW paragraph when ANY of these
conditions holds:
  - There is a timestamp gap larger than roughly 5 seconds between cues.
  - The topic changes.
  - The speaker changes (panels, Q&A, multi-person sessions).
  - The paragraph would exceed roughly 5–7 sentences.

## Section headings
You may group related paragraphs under an <h3> heading.
Rules:
  - Use sentence casing (e.g. "Setting up the environment", not "Setting Up
    The Environment").
  - Keep headings short — a few words to a short phrase.
  - Only add a heading when a clear topic shift justifies it.
  - Do NOT start a heading at the very beginning of the document; the first
    content should be a <p> or <blockquote>.
  - Do NOT add headings so frequently that every paragraph gets one.

## Blockquotes
Identify 0–3 memorable, insightful, or surprising quotes.
Wrap each in a <blockquote>, using the same <a> elements as normal text.
Rules:
  - At most one quote per 10 minutes of video.
  - Space them evenly throughout the document.
  - Keep the quote verbatim.
  - If no quote stands out, omit blockquotes entirely — that is fine.

## Examples

### ✗ WRONG — text was modified
VTT:  I was kind of unsure about this approach
HTML: <a data-t="120">I was somewhat uncertain about this method</a>
WHY:  The wording was changed. Keep it verbatim.

### ✗ WRONG — data-t used minutes instead of seconds
VTT:  00:02:05.500 --> 00:02:10.000
      some text
HTML: <a data-t="2">some text</a>
WHY:  2 min 5 sec = 125 seconds; correct value is data-t="125".

### ✗ WRONG — text not wrapped in <p>
HTML: <a data-t="0">Hello everyone.</a> <a data-t="5">Today we talk about R.</a>
WHY:  Every sentence must live inside a <p> element.

### ✗ WRONG — disallowed elements
HTML: <h2>Introduction</h2><p>...</p>
WHY:  Only <h3>, <p>, <a>, <blockquote> are allowed.

### ✗ WRONG — blockquote without <a> elements
HTML: <blockquote>The best code is reproducible code.</blockquote>
WHY:  Text in blockquotes must also be wrapped in <a data-t="..."> elements.

### ✗ WRONG — heading at the very start of the document
HTML: <h3>Introduction</h3><p><a data-t="0">Hello everyone.</a></p>
WHY:  Do not open with a heading; start with a <p>.

### ✗ WRONG — heading casing
HTML: <h3>Setting Up The Environment</h3>
WHY:  Use sentence casing: <h3>Setting up the environment</h3>

### ✓ CORRECT — multi-cue sentence, single paragraph
VTT:
  00:01:30.000 --> 00:01:35.000
  Today I want to talk about

  00:01:35.000 --> 00:01:40.000
  reproducible research with Quarto.

  00:01:41.000 --> 00:01:46.000
  It has changed how I work.

HTML:
  <p><a data-t="90">Today I want to talk about</a> <a data-t="95">reproducible research with Quarto.</a> <a data-t="101">It has changed how I work.</a></p>

### ✓ CORRECT — paragraph break on topic change + blockquote
HTML:
  <p><a data-t="300">So that covers the basics of reactive programming.</a></p>

  <p><a data-t="320">Now I want to shift gears and talk about testing.</a> <a data-t="324">Testing Shiny apps used to be really hard.</a> <a data-t="328">But shinytest2 has changed that.</a></p>

  <blockquote><a data-t="335">The best Shiny app is one you're not afraid to change, and tests give you that confidence.</a></blockquote>

  <p><a data-t="342">Let me show you a simple example.</a></p>

### ✓ CORRECT — gap-based paragraph break (8-second gap between cues)
HTML:
  <p><a data-t="305">And that's how you configure the layout.</a></p>

  <p><a data-t="318">Alright, let's move on to deployment.</a></p>

### ✓ CORRECT — section heading on clear topic shift
HTML:
  <p><a data-t="540">And that wraps up our overview of the data pipeline.</a></p>

  <h3>Building the Shiny dashboard</h3>

  <p><a data-t="558">Now let's actually build the app.</a> <a data-t="562">I'll start with a minimal ui definition.</a></p>
"""
```

### 1.2  User message builder

The `people` field in the frontmatter lists the people featured in the video
(as a list of names or slugs — use whatever is stored in the YAML).  Pass it
alongside software so the model can identify speaker names and spell them
correctly.

```python
def build_user_message(vtt_content: str, frontmatter: dict) -> str:
    """Prepend video metadata to the VTT content as context for the model."""
    title       = frontmatter.get("title", "")
    description = (frontmatter.get("description") or "").strip()
    software    = frontmatter.get("software") or []
    people      = frontmatter.get("people") or []

    header_parts = []
    if title:
        header_parts.append(f"Video title: {title}")
    if people:
        header_parts.append(f"People featured: {', '.join(str(p) for p in people)}")
    if software:
        header_parts.append(f"Technologies mentioned: {', '.join(str(s) for s in software)}")
    if description:
        header_parts.append(f"Description: {description[:600]}")  # cap length

    header = "\n".join(header_parts)
    return f"{header}\n\n---\n\n{vtt_content}" if header else vtt_content
```

---

## Phase 2 — Script implementation

### 2.1  Script header and dependencies

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "rich>=13.0.0",
#   "anthropic>=0.40.0",
#   "python-dotenv>=1.0.0",
#   "tomli>=2.0.0; python_version < '3.11'",
# ]
# ///
```

`tomllib` is stdlib since Python 3.11; the `tomli` shim covers older versions.

### 2.2  Imports and constants

```python
import argparse
import asyncio
import os
import random
import re
import sys
from pathlib import Path
from typing import Any

import anthropic
import yaml
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

console = Console(stderr=True)

MAX_RETRIES            = 5
BASE_BACKOFF           = 1.0
CHUNK_DURATION_S       = 1_800   # 30 min per chunk (default)
LONG_VIDEO_THRESHOLD_S = 5_400   # 90 min — chunk automatically
```

### 2.3  CLI arguments

```
--jobs N               parallel workers (default: 5)
--force                overwrite existing transcription.html files
--video NAME           process only this directory (name or full path)
--model ID             Anthropic model ID (default: claude-sonnet-4-6)
--max-tokens N         maximum output tokens per API call (default: 16384)
--chunk-duration SECS  VTT seconds per chunk for long videos (default: 1800)
```

### 2.4  Helpers reused from `transcribe.py`

Copy `parse_frontmatter` verbatim (or import it if the scripts ever become a
package).  The `RateLimiter` class is also identical — copy it unchanged.

### 2.5  Strip Markdown fence

```python
def strip_markdown_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.strip())
    return text.strip()
```

### 2.6  Lightweight output validation

```python
def validate_html(html: str) -> None:
    if not html.lstrip().startswith("<"):
        raise ValueError("Response does not start with '<' — not HTML")
    for bad in ("<html", "<body", "<head", "<div", "<span", "<h1", "<h2"):
        if bad in html:
            raise ValueError(f"Response contains disallowed element: {bad}")
    if "<p>" not in html and "<blockquote>" not in html:
        raise ValueError("Response contains no <p> or <blockquote> elements")
```

### 2.7  API call with exponential backoff

```python
async def call_api(
    client: anthropic.AsyncAnthropic,
    user_message: str,
    model: str,
    max_tokens: int,
    rate_limiter: RateLimiter,
    name: str,
    system: str = PROMPT,
) -> str:
    for attempt in range(MAX_RETRIES):
        if attempt > 0:
            delay = BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0, 1)
            console.print(
                f"  [yellow]↻[/] {name}  retry {attempt + 1}/{MAX_RETRIES} in {delay:.1f}s"
            )
            await asyncio.sleep(delay)

        await rate_limiter.wait()
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=0,
                system=system,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
        except anthropic.APIStatusError as e:
            if e.status_code < 500 or attempt == MAX_RETRIES - 1:
                raise

    raise RuntimeError("Exceeded max retries")
```

The optional `system` parameter lets Phase 3 (chunking) pass a per-segment
system message without duplicating the retry logic.

### 2.8  Per-video processing coroutine

The early-exit checks are evaluated in this order:
1. `transcription.html` already exists and `--force` not set → `"skipped"`
2. `_index.md` frontmatter has `transcribe: false` → `"excluded"`
3. No `transcription.vtt` file → `"no_vtt"`

```python
async def process_video_async(
    video_dir: Path,
    client: anthropic.AsyncAnthropic,
    semaphore: asyncio.Semaphore,
    rate_limiter: RateLimiter,
    progress: Progress,
    overall_task: TaskID,
    args: argparse.Namespace,
    people: dict[str, str],
    software: dict[str, str],
) -> str:
    async with semaphore:
        name     = video_dir.name
        job_task = progress.add_task(f"[dim]{name}", total=None)
        try:
            html_file  = video_dir / "transcription.html"
            vtt_file   = video_dir / "transcription.vtt"
            index_file = video_dir / "_index.md"

            if html_file.exists() and not args.force:
                return "skipped"

            frontmatter = (
                parse_frontmatter(index_file.read_text(encoding="utf-8"))
                if index_file.exists() else {}
            )

            if frontmatter.get("transcribe", True) is False:
                return "excluded"

            if not vtt_file.exists():
                return "no_vtt"

            vtt_content = vtt_file.read_text(encoding="utf-8")
            duration = (frontmatter.get("external") or {}).get("duration", 0)

            if duration > LONG_VIDEO_THRESHOLD_S:
                # Phase 3: split into chunks and concatenate results
                html = await format_chunked(
                    vtt_content, frontmatter, client, rate_limiter,
                    args, name, progress, job_task,
                )
            else:
                user_message = build_user_message(vtt_content, frontmatter)
                progress.update(job_task, description=f"[cyan]{name}  formatting")
                raw  = await call_api(
                    client, user_message, args.model, args.max_tokens,
                    rate_limiter, name,
                )
                html = strip_markdown_fence(raw)

            validate_html(html)
            html = inject_links(html, people, software)  # Phase 4
            html_file.write_text(html, encoding="utf-8")
            return "formatted"

        except Exception as e:
            console.print(f"  [red]✗[/] {name}: {e}")
            return "error"
        finally:
            progress.remove_task(job_task)
            progress.advance(overall_task)
```

### 2.9  Directory resolver for `--video`

```python
def resolve_video_dir(name_or_path: str, videos_dir: Path) -> Path:
    p = Path(name_or_path)
    if p.is_absolute() and p.is_dir():
        return p
    candidate = videos_dir / name_or_path
    if candidate.is_dir():
        return candidate
    # Prefix match (handy when the user types a partial slug)
    matches = [d for d in videos_dir.iterdir()
               if d.is_dir() and d.name.startswith(name_or_path)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        listed = "\n  ".join(m.name for m in sorted(matches))
        raise ValueError(f"Ambiguous --video value, matches:\n  {listed}")
    raise ValueError(f"Video directory not found: {name_or_path}")
```

### 2.10  `main_async` and `main`

```python
async def main_async(args: argparse.Namespace) -> None:
    console.print("\n[bold blue]Transcription Formatter[/]\n")

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/] ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    client     = anthropic.AsyncAnthropic(api_key=api_key)
    repo_root  = Path(__file__).parent.parent
    videos_dir = repo_root / "content" / "resources" / "videos"

    if not videos_dir.exists():
        console.print(f"[bold red]Error:[/] Videos directory not found: {videos_dir}")
        sys.exit(1)

    people, software = build_entity_dicts(repo_root)  # Phase 4
    console.print(f"[dim]Loaded {len(people)} people and {len(software)} software entries[/]")

    if args.video:
        dirs = [resolve_video_dir(args.video, videos_dir)]
    else:
        dirs = sorted(d for d in videos_dir.iterdir() if d.is_dir())

    console.print(f"[dim]Found {len(dirs)} director(ies) to process (--jobs {args.jobs})[/]\n")

    semaphore    = asyncio.Semaphore(args.jobs)
    rate_limiter = RateLimiter(min_interval=1.0)

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        overall_task = progress.add_task("[bold cyan]Formatting", total=len(dirs))
        results: list[str] = await asyncio.gather(*[
            process_video_async(d, client, semaphore, rate_limiter,
                                progress, overall_task, args, people, software)
            for d in dirs
        ])

    formatted = results.count("formatted")
    skipped   = results.count("skipped")
    excluded  = results.count("excluded")
    no_vtt    = results.count("no_vtt")
    errors    = results.count("error")

    console.print("\n[bold]Summary:[/]")
    console.print(f"  [green]✓[/] Formatted: {formatted}")
    console.print(f"  [dim]○[/] Skipped:   {skipped}")
    console.print(f"  [dim]○[/] Excluded:  {excluded}")
    console.print(f"  [dim]○[/] No VTT:    {no_vtt}")
    if errors:
        console.print(f"  [red]✗[/] Errors:    {errors}")
    console.print("\n[bold green]✓ Done![/]\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Format VTT transcriptions into HTML using the Anthropic API"
    )
    parser.add_argument("--jobs", type=int, default=5, metavar="N",
                        help="parallel formatting jobs (default: 5)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing transcription.html files")
    parser.add_argument("--video", metavar="NAME",
                        help="process only this video directory (name or path)")
    parser.add_argument("--model", default="claude-sonnet-4-6",
                        metavar="ID", help="Anthropic model ID")
    parser.add_argument("--max-tokens", type=int, default=16384, metavar="N",
                        help="max output tokens per API call (default: 16384)")
    parser.add_argument("--chunk-duration", type=int, default=CHUNK_DURATION_S,
                        metavar="SECS",
                        help=f"VTT seconds per chunk for long videos (default: {CHUNK_DURATION_S})")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
```

---

## Phase 3 — Chunked processing for long videos

Videos longer than 90 minutes (5 400 s) are split into chunks before sending
to the API.  The longest VTT on disk is ~10 000 lines (4 h, 15 126 s); sending
it whole would exceed both the input context window and the output token limit.

### 3.1  VTT splitter

Reuse `parse_vtt` from `transcribe.py` to get a list of `(start, end, text)`
tuples, then group cues into segments of at most `args.chunk_duration` seconds.
Always split on cue boundaries so no cue is cut mid-sentence.

```python
def split_vtt_into_chunks(
    vtt_content: str, chunk_duration: int
) -> list[tuple[str, int]]:
    """Return list of (chunk_vtt_text, segment_start_seconds)."""
    cues = parse_vtt(vtt_content)   # from transcribe.py
    chunks: list[tuple[str, int]] = []
    seg_start = 0.0
    seg_cues: list[tuple[float, float, str]] = []

    for start, end, text in cues:
        if seg_cues and (start - seg_start) >= chunk_duration:
            chunks.append((_render_vtt(seg_cues), int(seg_start)))
            seg_start = start
            seg_cues = []
        seg_cues.append((start, end, text))

    if seg_cues:
        chunks.append((_render_vtt(seg_cues), int(seg_start)))

    return chunks


def _render_vtt(cues: list[tuple[float, float, str]]) -> str:
    lines = ["WEBVTT", ""]
    for start, end, text in cues:
        lines.append(f"{format_vtt_timestamp(start)} --> {format_vtt_timestamp(end)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)
```

### 3.2  Chunked system message

When processing a segment, append segment context to the system message so the
model knows where it is in the video:

```python
def build_chunk_system(segment_index: int, total_segments: int) -> str:
    return (
        PROMPT.rstrip()
        + f"\n\n## Segment context\n"
        + f"This is segment {segment_index + 1} of {total_segments}.\n"
        + f"Start each paragraph cleanly — do not begin mid-sentence.\n"
        + f"End each paragraph cleanly — do not leave a sentence dangling.\n"
    )
```

### 3.3  `format_chunked` coroutine

```python
async def format_chunked(
    vtt_content: str,
    frontmatter: dict,
    client: anthropic.AsyncAnthropic,
    rate_limiter: RateLimiter,
    args: argparse.Namespace,
    name: str,
    progress: Progress,
    job_task: TaskID,
) -> str:
    chunks = split_vtt_into_chunks(vtt_content, args.chunk_duration)
    total  = len(chunks)
    html_parts: list[str] = []

    for i, (chunk_vtt, _seg_start) in enumerate(chunks):
        progress.update(
            job_task,
            description=f"[cyan]{name}  chunk {i + 1}/{total}",
        )
        user_message  = build_user_message(chunk_vtt, frontmatter)
        chunk_system  = build_chunk_system(i, total)
        raw = await call_api(
            client, user_message, args.model, args.max_tokens,
            rate_limiter, name, system=chunk_system,
        )
        html_parts.append(strip_markdown_fence(raw))

    return "\n<!-- segment separator -->\n".join(html_parts)
```

---

## Phase 4 — Entity linking (people and software)

After the model returns HTML, a post-processing pass wraps the **first
occurrence** of each known person name and software package name in an
`<a href="…">` tag.

Because `<a>` elements cannot be nested, matches found inside an existing
`<a data-t="…">` element cause that element to be **split** around the match.
All resulting pieces keep the original `data-t` attribute; the matched fragment
gains an additional `href` attribute.

### 4.1  Build entity dictionaries

At startup, scan the site content directories once and build two
`name → URL` dictionaries.

```python
def build_entity_dicts(
    repo_root: Path,
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (people_dict, software_dict) mapping display name → site URL."""

    # Load software ignore list (keyed by slug)
    ignore_file = repo_root / "data" / "software-match-ignore.toml"
    ignored: set[str] = set()
    if ignore_file.exists():
        data = tomllib.loads(ignore_file.read_text(encoding="utf-8"))
        ignored = set(data.get("names", []))

    # People: title → /people/{slug}/
    people: dict[str, str] = {}
    people_dir = repo_root / "content" / "people"
    if people_dir.exists():
        for d in people_dir.iterdir():
            if not d.is_dir():
                continue
            index = d / "_index.md"
            if not index.exists():
                continue
            fm = parse_frontmatter(index.read_text(encoding="utf-8"))
            title = (fm.get("title") or "").strip()
            if title:
                people[title] = f"/people/{d.name}/"

    # Software: title → /software/{slug}/  (skip ignored slugs)
    software: dict[str, str] = {}
    software_dir = repo_root / "content" / "software"
    if software_dir.exists():
        for d in software_dir.iterdir():
            if not d.is_dir() or d.name in ignored:
                continue
            index = d / "_index.md"
            if not index.exists():
                continue
            fm = parse_frontmatter(index.read_text(encoding="utf-8"))
            # Some entries have override.title (takes precedence)
            override = (fm.get("override") or {}).get("title")
            title = (override or fm.get("title") or "").strip()
            if title:
                software[title] = f"/software/{d.name}/"

    return people, software
```

### 4.2  Inject links

The algorithm:

1. Split the HTML on `<a …>…</a>` blocks into alternating plain-text and
   anchor segments.
2. For **plain-text** segments: wrap entity matches in `<a href="…">`.
3. For **anchor** segments (`<a data-t="X">content</a>`): search `content` for
   entity matches and, if found, split the anchor into up to three pieces:
   - `<a data-t="X">text-before</a>` (omitted if empty)
   - `<a href="URL" data-t="X">matched-name</a>`
   - `<a data-t="X">text-after</a>` (omitted if empty)
4. Each entity name is linked **at most once** per document (first occurrence).
5. Entities are processed in **descending length order** so longer names take
   priority (e.g. "ggplot2" is matched before "ggplot").
6. People names are matched **case-sensitively**; software names
   **case-insensitively** (transcriptions may vary in capitalisation).

```python
def inject_links(
    html: str,
    people: dict[str, str],
    software: dict[str, str],
) -> str:
    linked: set[str] = set()

    # Combined entity list, sorted longest-first
    entities: list[tuple[str, str, bool]] = sorted(
        [(name, url, False) for name, url in people.items()] +
        [(name, url, True)  for name, url in software.items()],
        key=lambda x: -len(x[0]),
    )

    # Split into alternating [text, <a>…</a>, text, …] segments
    parts = re.split(r'(<a\b[^>]*>.*?</a>)', html, flags=re.DOTALL)

    result: list[str] = []
    for part in parts:
        m = re.match(r'<a(\b[^>]*)>(.*?)</a>', part, flags=re.DOTALL)
        if m:
            attrs, content = m.group(1), m.group(2)
            result.append(_inject_into_anchor(content, attrs, entities, linked))
        else:
            result.append(_inject_into_text(part, entities, linked))

    return "".join(result)


def _inject_into_text(
    text: str,
    entities: list[tuple[str, str, bool]],
    linked: set[str],
) -> str:
    for name, url, is_software in entities:
        if name in linked:
            continue
        flags   = re.IGNORECASE if is_software else 0
        pattern = r'\b' + re.escape(name) + r'\b'
        if re.search(pattern, text, flags=flags):
            linked.add(name)
            text = re.sub(
                pattern,
                lambda m, u=url: f'<a href="{u}">{m.group(0)}</a>',
                text, count=1, flags=flags,
            )
    return text


def _inject_into_anchor(
    content: str,
    attrs: str,
    entities: list[tuple[str, str, bool]],
    linked: set[str],
) -> str:
    """Search content for an entity match; if found, split the anchor.

    Returns one to three <a> elements.  The surrounding text pieces keep the
    original `attrs` (i.e. the data-t attribute).  The matched fragment gets
    only href="URL" — no data-t — so it acts as a navigation link, not a
    timestamp seek.

    Only one entity is matched per call (the first match among unlinked
    entities).  Any remaining text in `before` / `after` is left as plain
    anchor text; a subsequent pass through inject_links is not needed because
    entity names are each linked at most once globally.
    """
    for name, url, is_software in entities:
        if name in linked:
            continue
        flags   = re.IGNORECASE if is_software else 0
        pattern = r'\b' + re.escape(name) + r'\b'
        mo      = re.search(pattern, content, flags=flags)
        if mo:
            linked.add(name)
            before     = content[:mo.start()]
            match_text = mo.group(0)
            after      = content[mo.end():]
            pieces: list[str] = []
            if before:
                pieces.append(f'<a{attrs}>{before}</a>')
            pieces.append(f'<a href="{url}">{match_text}</a>')  # no data-t
            if after:
                pieces.append(f'<a{attrs}>{after}</a>')
            return "".join(pieces)

    # No match — return original anchor unchanged
    return f'<a{attrs}>{content}</a>'
```

**Edge cases:**
- Short software names (e.g. "R", "DT") can still match unintended tokens
  despite `\b` word boundaries.  Add such entries to `software-match-ignore.toml`
  as needed.
- The ignore list is keyed by *slug* (`d.name in ignored`), not display name.
- If two entity names overlap in the same anchor (e.g. "ggplot" and "ggplot2"),
  the longer name wins because entities are sorted by descending length.

---

## File layout

```
scripts/
  transcribe.py                  (existing — audio → VTT)
  format-transcription.py        (new      — VTT → HTML)
```

---

## Phase summary

| Phase | Deliverable | Key risk |
|-------|-------------|----------|
| **1** | `PROMPT` constant + `build_user_message()` | Prompt quality is everything — iterate with 5–10 sample videos before finalising |
| **2** | Full script skeleton (API call, backoff, progress, CLI) | Straightforward once Phase 1 is stable |
| **3** | `split_vtt_into_chunks` + `format_chunked` | Segment boundaries may split mid-sentence; test with the 4-hour SciPy video |
| **4** | `build_entity_dicts` + `inject_links` | Short software names (e.g. "R") risk false positives; add to ignore list as needed |

### Suggested test videos

| Slug | Why useful |
|------|-----------|
| `2024-10-31_mine-cetinkaya-rundel-…` | Clean single-speaker, 19 min |
| `2019-11-11_panel-growth-change-of-careers-…` | Multi-speaker panel |
| `2025-08-04_daniel-chen-shiny-for-python-…` | Very long workshop (4 h) — exercises chunking |
| Any `data-science-hangout-*` | Conversational Q&A style |

---

## Todo list

### Phase 1 — Prompt design

- [x] Finalise the `PROMPT` constant (system message) at the top of the script
  - [x] Verify the `data-t` conversion formula and examples are correct
  - [x] Verify wrong/correct examples cover all the rules
  - [x] Confirm `<h3>` heading rules (sentence casing, not at document start, not overused)
- [x] Implement `build_user_message(vtt_content, frontmatter)`
  - [x] Include `title` field
  - [x] Include `people` field (if present in frontmatter)
  - [x] Include `software` field (if present in frontmatter)
  - [x] Include `description` field, capped at 600 characters
- [x] Manually test the prompt on 4–5 sample videos before moving to Phase 2
  - [x] `2024-10-31_mine-cetinkaya-rundel-…` — single speaker
  - [x] `2019-11-11_panel-growth-change-of-careers-…` — multi-speaker panel
  - [x] A `data-science-hangout-*` video — conversational Q&A
  - [x] Check: verbatim text, correct `data-t` seconds, paragraph breaks, blockquotes, headings

### Phase 2 — Core script

- [x] Write PEP 723 script header with inline dependencies
  (`pyyaml`, `rich`, `anthropic`, `python-dotenv`, `tomli` shim)
- [x] Write imports and module-level constants
  (`MAX_RETRIES`, `BASE_BACKOFF`, `CHUNK_DURATION_S`, `LONG_VIDEO_THRESHOLD_S`)
- [x] Copy `parse_frontmatter` verbatim from `transcribe.py`
- [x] Copy `RateLimiter` class verbatim from `transcribe.py`
- [x] Copy `parse_vtt`, `format_vtt_timestamp` from `transcribe.py`
  (needed by Phase 3 VTT splitter)
- [x] Implement `strip_markdown_fence(text)`
- [x] Implement `validate_html(html)` — checks for disallowed elements and
  presence of `<p>` or `<blockquote>`
- [x] Implement `call_api(client, user_message, model, max_tokens, rate_limiter, name, system=PROMPT)`
  — exponential backoff on `RateLimitError` and 5xx errors; optional `system`
  parameter for Phase 3 chunk overrides
- [x] Implement `resolve_video_dir(name_or_path, videos_dir)`
  — exact match, then prefix match
- [x] Implement `process_video_async(...)` with skip conditions in order:
  - [x] Skip if `transcription.html` exists and `--force` not set → `"skipped"`
  - [x] Skip if `frontmatter.get("transcribe", True) is False` → `"excluded"`
  - [x] Skip if `transcription.vtt` does not exist → `"no_vtt"`
  - [x] Dispatch to `format_chunked` when `duration > LONG_VIDEO_THRESHOLD_S`
  - [x] Call `inject_links` after validation
- [x] Implement `main_async(args)` — loads env, builds entity dicts, gathers coroutines,
  prints summary (formatted / skipped / excluded / no_vtt / errors)
- [x] Implement `main()` — argparse with all CLI flags:
  `--jobs`, `--force`, `--video`, `--model`, `--max-tokens`, `--chunk-duration`
- [x] Smoke-test the script end-to-end on a single short video (`--video NAME`)

### Phase 3 — Chunked processing

- [x] Implement `_render_vtt(cues)` — serialise a list of `(start, end, text)`
  tuples back to VTT format
- [x] Implement `split_vtt_into_chunks(vtt_content, chunk_duration)`
  — group cues into segments of at most `chunk_duration` seconds, splitting
  only on cue boundaries
- [x] Implement `build_chunk_system(segment_index, total_segments)`
  — append segment-context paragraph to `PROMPT`
- [x] Implement `format_chunked(...)` — iterate over chunks, call `call_api`
  with the per-chunk system message, join results with `<!-- segment separator -->`
- [x] Test end-to-end with `2025-08-04_daniel-chen-shiny-for-python-…` (4 h video)
  - [x] Verify the number of chunks is as expected for `--chunk-duration 1800`
    (9 chunks, 8 separators at lines 86/174/284/410/510/622/738/812)
  - [x] Verify no sentence is cut across a segment boundary
  - [x] Verify the concatenated HTML validates correctly

### Phase 4 — Entity linking

- [x] Implement `build_entity_dicts(repo_root)`
  - [x] Load ignored slugs from `data/software-match-ignore.toml`
  - [x] Scan `content/people/*/` — read `title` from each `_index.md`,
    build `name → /people/{slug}/` dict
  - [x] Scan `content/software/*/` — read `title` (or `override.title`) from
    each `_index.md`, skip slugs in the ignore set,
    build `name → /software/{slug}/` dict
  - [x] Log counts to console on startup
- [x] Implement `_inject_into_text(text, entities, linked)`
  — wrap first unlinked match in `<a href="URL">`, case rules per entity type
- [x] Implement `_inject_into_anchor(content, attrs, entities, linked)`
  — split existing `<a data-t="X">` around a match; surrounding pieces keep
  `data-t`, matched fragment gets only `href`
- [x] Implement `inject_links(html, people, software)`
  — split HTML on `<a>…</a>` blocks, dispatch to the two helpers above
- [x] Test entity linking in isolation on a short HTML snippet
  - [x] Person name in plain text → wrapped correctly (verified: Hadley Wickham, Rich Iannone, Michael Chow)
  - [x] Software name in plain text → wrapped correctly, case-insensitive (verified: Quarto, dplyr, Great Tables)
  - [x] Name inside `<a data-t="…">` → anchor split, matched fragment has no `data-t` (verified: ggplot2, reticulate, RStudio)
  - [x] Ignored software slug → not linked
  - [x] Second occurrence of a name → not linked again
  - [x] Longer name takes priority over shorter prefix (e.g. "ggplot2" vs "ggplot")
- [x] Run on a full video and manually inspect the output for false positives
  (especially short software names like "R", "DT", "fs")
  — add any offenders to `data/software-match-ignore.toml`
