import json
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
NOTEBOOK_FILES = sorted(ROOT_DIR.glob("*.ipynb"))


def load_notebook(path: Path):
    if not path.exists():
        return None, f"Notebook file not found at {path}"

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return None, "Unable to parse notebook JSON."

    cells = []
    for cell in data.get("cells", []):
        cell_type = cell.get("cell_type", "unknown")
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        cells.append({
            "type": cell_type,
            "source": source,
        })
    return cells, None


def summarize_notebook(cells):
    summary = {"code_cells": 0, "markdown_cells": 0, "other_cells": 0}
    for cell in cells:
        if cell["type"] == "code":
            summary["code_cells"] += 1
        elif cell["type"] == "markdown":
            summary["markdown_cells"] += 1
        else:
            summary["other_cells"] += 1
    return summary


def render_dashboard(notebook_path: Path, cells):
    summary = summarize_notebook(cells)

    st.title("Accountant Streamlit Interface")
    st.write(
        "This Streamlit app provides a simple notebook dashboard and an optional preview mode for `Copy_of_Welcome_To_Colab.ipynb`."
    )

    left, right = st.columns(2)
    left.metric("Notebook file", notebook_path.name)
    right.metric("Total cells", len(cells))

    col1, col2, col3 = st.columns(3)
    col1.metric("Markdown cells", summary["markdown_cells"])
    col2.metric("Code cells", summary["code_cells"])
    col3.metric("Other cells", summary["other_cells"])

    with st.expander("Notebook file details"):
        st.write(f"Path: `{notebook_path}`")
        st.write(f"Contains {len(cells)} cells.")
        st.write(
            "Use the sidebar to switch between the dashboard view and the notebook preview."
        )

    if st.checkbox("Show sample of the notebook content", value=False):
        for index, cell in enumerate(cells[:3], start=1):
            if cell["type"] == "code":
                st.code(cell["source"], language="python")
            else:
                st.markdown(cell["source"])


def render_preview(cells):
    st.header("Notebook Preview")
    for index, cell in enumerate(cells, start=1):
        container = st.container()
        if cell["type"] == "code":
            container.subheader(f"Code cell {index}")
            container.code(cell["source"], language="python")
        else:
            container.subheader(f"Markdown cell {index}")
            container.markdown(cell["source"])


def main():
    st.set_page_config(page_title="Accountant Notebook App", layout="wide")

    if not NOTEBOOK_FILES:
        st.error("No notebook files were found in the current folder.")
        return

    notebook_choice = st.sidebar.selectbox(
        "Select notebook file",
        NOTEBOOK_FILES,
        format_func=lambda path: path.name,
    )

    mode = st.sidebar.radio("View mode", ["Dashboard", "Notebook preview"])
    st.sidebar.markdown("---")
    st.sidebar.write("This app loads a local notebook file and shows a friendly Streamlit interface.")

    cells, error = load_notebook(notebook_choice)
    if error:
        st.error(error)
        return

    if mode == "Dashboard":
        render_dashboard(notebook_choice, cells)
    else:
        render_preview(cells)


if __name__ == "__main__":
    main()
