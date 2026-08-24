"""Sync marimo notebooks (notebooks/*.py) into jupyter-book-marimo MyST markdown
(content/*.md).

Run via `make sync-notebooks` / `make book-start`, or directly with
`uv run python scripts/sync_notebooks.py [--serve]`.

Relies on the (undocumented) output format of `marimo export md`, tested against
marimo's current CLI as of this writing. If the export format changes upstream,
the regex-based transforms in this file may need updating.
"""

import argparse
import pathlib
import re
import subprocess
import sys
import time
import tomllib

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
CONTENT_DIR = PROJECT_ROOT / "content"

# Directories under notebooks/ that should never be treated as notebook sources
# (e.g. marimo's own session/layout state).
IGNORED_DIRS = {"__marimo__", "__pycache__"}


def iter_notebooks():
    """Yield all notebook .py files under NOTEBOOKS_DIR, skipping ignored dirs."""
    for py_file in NOTEBOOKS_DIR.rglob("*.py"):
        parts = py_file.relative_to(NOTEBOOKS_DIR).parts[:-1]
        if IGNORED_DIRS.isdisjoint(parts):
            yield py_file


def run_marimo_export(notebook_path: pathlib.Path) -> str:
    cmd = ["marimo", "export", "md", str(notebook_path)]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[marimo-sync] Error exporting {notebook_path.name}:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return ""
    except FileNotFoundError:
        print(
            "[marimo-sync] 'marimo' command not found — is it installed and on PATH?",
            file=sys.stderr,
        )
        return ""


def parse_pep723_script_metadata(yaml_text: str, source: str = "") -> dict:
    """Extract and parse PEP 723 inline script metadata from indented YAML frontmatter."""
    # Normalize non-breaking spaces and line breaks
    text = yaml_text.replace("\xa0", " ")

    # Match `# /// script` ... `# ///` handling leading indentation and \r\n
    pattern = r"^\s*#\s*///\s*script\s*[\r\n]+((?:[^\n]*\n)+?)\s*#\s*///"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return {}

    script_block = match.group(1)
    toml_lines = []
    for line in script_block.splitlines():
        # Remove leading indentation and comment character '#'
        cleaned_line = re.sub(r"^\s*#\s?", "", line)
        toml_lines.append(cleaned_line)

    try:
        return tomllib.loads("\n".join(toml_lines))
    except tomllib.TOMLDecodeError as e:
        label = f" in {source}" if source else ""
        print(f"[marimo-sync] Error parsing TOML metadata{label}: {e}", file=sys.stderr)
        return {}


def format_marimo_config(pyproject_data: dict) -> str:
    """Format parsed TOML dict into a {marimo-config} MyST block."""
    requires_python = pyproject_data.get("requires-python")
    dependencies = pyproject_data.get("dependencies", [])

    # Filter out 'marimo' dependency as it's implied by jupyter-book-marimo
    filtered_deps = [
        dep for dep in dependencies
        if not re.match(r"^marimo([<>=!~]|$)", dep.strip())
    ]

    lines = ["```{marimo-config}", ":pyproject:"]
    if requires_python:
        lines.append(f'    requires-python = "{requires_python}"')
    if filtered_deps:
        lines.append("    dependencies = [")
        for dep in filtered_deps:
            lines.append(f'        "{dep}",')
        lines.append("    ]")
    lines.append("```")
    return "\n".join(lines)


def transform_md_content(md_content: str, source: str = "") -> str:
    """Transform raw marimo export md to jupyter-book-marimo MyST format."""

    # Parse YAML frontmatter (supports \r\n line endings)
    frontmatter_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)", md_content, re.DOTALL)

    header_config_block = ""
    clean_frontmatter = ""

    if frontmatter_match:
        yaml_text = frontmatter_match.group(1)
        body_text = frontmatter_match.group(2)

        # 1. Parse PEP 723 metadata into {marimo-config} block
        pyproject_data = parse_pep723_script_metadata(yaml_text, source=source)
        if pyproject_data:
            header_config_block = format_marimo_config(pyproject_data)

        # 2. Strip marimo-version and multiline header from YAML frontmatter
        cleaned_yaml_lines = []
        in_header_block = False

        for line in yaml_text.splitlines():
            if line.startswith("marimo-version:"):
                continue
            if line.startswith("header:"):
                in_header_block = True
                continue
            if in_header_block:
                # Continue skipping lines if they are indented or empty
                if re.match(r"^\s", line) or not line.strip():
                    continue
                else:
                    in_header_block = False

            cleaned_yaml_lines.append(line)

        yaml_str = "\n".join(cleaned_yaml_lines).strip()
        if yaml_str:
            clean_frontmatter = f"---\n{yaml_str}\n---"
    else:
        body_text = md_content

    # 3. Transform code cell blocks: ```python {.marimo ...} -> ```{marimo} python
    transformed_body = re.sub(
        r"```python\s*\{\.marimo(?:\s+[^}]+)?\}",
        "```{marimo} python",
        body_text,
    )

    # 4. Assemble output components in order
    sections = []
    if clean_frontmatter:
        sections.append(clean_frontmatter)
    if header_config_block:
        sections.append(header_config_block)
    sections.append(transformed_body.strip())

    return "\n\n".join(sections) + "\n"


def convert_file(src_file: pathlib.Path) -> bool:
    rel_path = src_file.relative_to(NOTEBOOKS_DIR)
    dest_file = (CONTENT_DIR / rel_path).with_suffix(".md")
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    raw_md = run_marimo_export(src_file)
    if not raw_md:
        return False

    processed_md = transform_md_content(raw_md, source=str(rel_path))
    dest_file.write_text(processed_md, encoding="utf-8")
    print(
        f"[marimo-sync] Synced: notebooks/{rel_path.as_posix()} "
        f"-> content/{dest_file.relative_to(CONTENT_DIR).as_posix()}"
    )
    return True


def sync_all() -> bool:
    """Convert every notebook. Returns False if any conversion failed."""
    print("[marimo-sync] Building notebooks...")
    all_ok = True
    for py_file in iter_notebooks():
        if not convert_file(py_file):
            all_ok = False
    return all_ok


def watch_and_serve(port: str, server_port: str):
    sync_all()

    mtimes: dict[pathlib.Path, float] = {}
    for py_file in iter_notebooks():
        mtimes[py_file] = py_file.stat().st_mtime

    jb_cmd = [
        "uv", "run", "jupyter-book", "start",
        "--port", port,
        "--server-port", server_port
    ]
    print("[marimo-sync] Launching Jupyter Book dev server...")
    try:
        jb_proc = subprocess.Popen(jb_cmd, cwd=CONTENT_DIR)
    except FileNotFoundError:
        print(
            "[marimo-sync] Could not launch Jupyter Book — is 'uv' installed and on PATH?",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        while True:
            time.sleep(0.5)
            if jb_proc.poll() is not None:
                break

            current_files = set(iter_notebooks())

            # Handle deleted notebooks: remove their generated .md and stop tracking them
            for stale_file in set(mtimes) - current_files:
                del mtimes[stale_file]
                rel_path = stale_file.relative_to(NOTEBOOKS_DIR)
                dest_file = (CONTENT_DIR / rel_path).with_suffix(".md")
                if dest_file.exists():
                    dest_file.unlink()
                    print(f"[marimo-sync] Removed: content/{dest_file.relative_to(CONTENT_DIR).as_posix()}")

            for py_file in current_files:
                try:
                    current_mtime = py_file.stat().st_mtime
                except FileNotFoundError:
                    continue

                if py_file not in mtimes or current_mtime > mtimes[py_file]:
                    mtimes[py_file] = current_mtime
                    convert_file(py_file)

    except KeyboardInterrupt:
        print("\n[marimo-sync] Shutting down server...")
    finally:
        if jb_proc.poll() is None:
            jb_proc.terminate()
            jb_proc.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="Start watcher and dev server")
    parser.add_argument("--port", default="3102", help="Jupyter Book port")
    parser.add_argument("--server-port", default="4102", help="Jupyter Book server port")
    args = parser.parse_args()

    if args.serve:
        watch_and_serve(args.port, args.server_port)
    else:
        if not sync_all():
            sys.exit(1)


if __name__ == "__main__":
    main()