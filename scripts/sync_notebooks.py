import argparse
import pathlib
import re
import subprocess
import sys
import time
import tomllib
from typing import Dict

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
CONTENT_DIR = PROJECT_ROOT / "content"


def run_marimo_export(notebook_path: pathlib.Path) -> str:
    cmd = ["marimo", "export", "md", str(notebook_path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        print(f"[marimo-sync] Error exporting {notebook_path.name}: {e}", file=sys.stderr)
        return ""


def parse_pep723_script_metadata(yaml_text: str) -> dict:
    script_block_match = re.search(r"# /// script\n((?:#.*\n)+?)# ///", yaml_text)
    if not script_block_match:
        return {}
    comment_lines = script_block_match.group(1).splitlines()
    toml_lines = [re.sub(r"^#\s?", "", line) for line in comment_lines]
    try:
        return tomllib.loads("\n".join(toml_lines))
    except Exception:
        return {}


def format_marimo_config(pyproject_data: dict) -> str:
    requires_python = pyproject_data.get("requires-python")
    dependencies = pyproject_data.get("dependencies", [])
    filtered_deps = [dep for dep in dependencies if not dep.strip().startswith("marimo")]

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


def transform_md_content(md_content: str) -> str:
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n?(.*)", md_content, re.DOTALL)
    header_config_block = ""
    clean_frontmatter = ""

    if frontmatter_match:
        yaml_text = frontmatter_match.group(1)
        body_text = frontmatter_match.group(2)

        pyproject_data = parse_pep723_script_metadata(yaml_text)
        if pyproject_data:
            header_config_block = format_marimo_config(pyproject_data)

        cleaned_yaml_lines = []
        in_header_block = False
        for line in yaml_text.splitlines():
            if line.startswith("marimo-version:"):
                continue
            if line.startswith("header:"):
                in_header_block = True
                continue
            if in_header_block:
                if line.startswith(" ") or line.startswith("\t") or not line.strip():
                    continue
                else:
                    in_header_block = False
            cleaned_yaml_lines.append(line)

        yaml_str = "\n".join(cleaned_yaml_lines).strip()
        if yaml_str:
            clean_frontmatter = f"---\n{yaml_str}\n---\n"
    else:
        body_text = md_content

    transformed_body = re.sub(
        r"```python\s*\{\.marimo(?:\s+[^}]+)?\}",
        "```{marimo} python",
        body_text,
    )

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

    processed_md = transform_md_content(raw_md)
    dest_file.write_text(processed_md, encoding="utf-8")
    print(f"[marimo-sync] Synced: notebooks/{rel_path} -> content/{dest_file.relative_to(CONTENT_DIR)}")
    return True


def sync_all():
    print("[marimo-sync] Building notebooks...")
    for py_file in NOTEBOOKS_DIR.rglob("*.py"):
        convert_file(py_file)


def watch_and_serve(port: str, server_port: str):
    sync_all()

    mtimes: Dict[pathlib.Path, float] = {}
    for py_file in NOTEBOOKS_DIR.rglob("*.py"):
        mtimes[py_file] = py_file.stat().st_mtime

    jb_cmd = [
        "uv", "run", "jupyter-book", "start",
        "--port", port,
        "--server-port", server_port
    ]
    print("[marimo-sync] Launching Jupyter Book dev server...")
    jb_proc = subprocess.Popen(jb_cmd, cwd=CONTENT_DIR)

    try:
        while True:
            time.sleep(0.5)
            if jb_proc.poll() is not None:
                break

            current_files = set(NOTEBOOKS_DIR.rglob("*.py"))
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
        sync_all()


if __name__ == "__main__":
    main()