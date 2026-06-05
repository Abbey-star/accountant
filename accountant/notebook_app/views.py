import json
from pathlib import Path
from django.shortcuts import render

BASE_DIR = Path(__file__).resolve().parents[2]
NOTEBOOK_FILE = BASE_DIR / "Copy_of_Welcome_To_Colab.ipynb"


def home(request):
    notebook = {"name": NOTEBOOK_FILE.name, "cells": [], "error": None}
    try:
        with open(NOTEBOOK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for cell in data.get("cells", []):
            cell_type = cell.get("cell_type", "unknown")
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            notebook["cells"].append({
                "type": cell_type,
                "source": source.strip(),
            })
    except FileNotFoundError:
        notebook["error"] = f"Notebook file not found at {NOTEBOOK_FILE}"
    except json.JSONDecodeError:
        notebook["error"] = "Unable to parse the notebook JSON."
    return render(request, "notebook_app/display.html", {"notebook": notebook})
