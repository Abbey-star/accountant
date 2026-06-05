import json
from pathlib import Path

import streamlit as st

NOTEBOOK_PATH = Path(__file__).resolve().parent / "Copy_of_Welcome_To_Colab.ipynb"


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


def main():
    st.set_page_config(page_title="Notebook Viewer", layout="wide")
    st.title("Notebook Viewer")
    st.write("This Streamlit app renders the notebook contents from `Copy_of_Welcome_To_Colab.ipynb`.")

    cells, error = load_notebook(NOTEBOOK_PATH)
    if error:
        st.error(error)
        return

    if not cells:
        st.warning("No cells were found in the notebook.")
        return

    for index, cell in enumerate(cells, start=1):
        container = st.container()
        if cell["type"] == "code":
            container.subheader(f"Code cell {index}")
            container.code(cell["source"], language="python")
        else:
            container.subheader(f"Markdown cell {index}")
            container.markdown(cell["source"])


if __name__ == "__main__":
    main()
