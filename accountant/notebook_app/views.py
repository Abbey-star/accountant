import json
from pathlib import Path
from django.shortcuts import render
from django.utils.html import escape
from django.utils.safestring import mark_safe

BASE_DIR = Path(__file__).resolve().parents[2]
NOTEBOOK_FILE = BASE_DIR / "Copy_of_Welcome_To_Colab.ipynb"


try:
    import markdown as md
except ImportError:
    md = None


def load_notebook(path: Path):
    if not path.exists():
        raise FileNotFoundError

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_markdown(source: str) -> str:
    if md:
        return mark_safe(md.markdown(source, extensions=["fenced_code", "nl2br"]))
    return mark_safe(f"<pre class=\"markdown-fallback\">{escape(source)}</pre>")


def summarize_cells(cells):
    summary = {"code_cells": 0, "markdown_cells": 0, "other_cells": 0}
    for cell in cells:
        if cell["type"] == "code":
            summary["code_cells"] += 1
        elif cell["type"] == "markdown":
            summary["markdown_cells"] += 1
        else:
            summary["other_cells"] += 1
    return summary


def home(request):
    notebook = {
        "name": NOTEBOOK_FILE.name,
        "cells": [],
        "summary": {"code_cells": 0, "markdown_cells": 0, "other_cells": 0},
        "error": None,
    }
    mode = request.GET.get("mode", "dashboard")

    try:
        data = load_notebook(NOTEBOOK_FILE)
        raw_cells = data.get("cells", [])

        for cell in raw_cells:
            cell_type = cell.get("cell_type", "unknown")
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            source = source.rstrip("\n")

            notebook["cells"].append({
                "type": cell_type,
                "source": source,
                "html": render_markdown(source) if cell_type == "markdown" else None,
            })

        notebook["summary"] = summarize_cells(notebook["cells"])
    except FileNotFoundError:
        notebook["error"] = f"Notebook file not found at {NOTEBOOK_FILE}"
    except json.JSONDecodeError:
        notebook["error"] = "Unable to parse the notebook JSON."

    return render(
        request,
        "notebook_app/display.html",
        {"notebook": notebook, "mode": mode},
    )
