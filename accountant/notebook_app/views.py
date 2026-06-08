import base64
import io
import json
from pathlib import Path

from django.shortcuts import render
from django.utils.html import escape
from django.utils.safestring import mark_safe

try:
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
except ImportError:
    plt = np = pd = LinearRegression = mean_absolute_error = mean_squared_error = r2_score = None

BASE_DIR = Path(__file__).resolve().parents[2]
NOTEBOOK_FILE = BASE_DIR / "Copy_of_Welcome_To_Colab.ipynb"


def load_notebook(path: Path):
    if not path.exists():
        raise FileNotFoundError

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_markdown(source: str) -> str:
    escaped = escape(source).replace("\n", "<br>")
    return mark_safe(f"<div class=\"markdown-rendered\">{escaped}</div>")


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


def create_plot_image(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close(fig)
    return f"data:image/png;base64,{image_base64}"


def build_model_from_dataframe(df):
    if pd is None or np is None or LinearRegression is None:
        raise ImportError("Required ML libraries are missing. Install pandas, numpy, matplotlib, and scikit-learn.")

    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_columns) < 2:
        raise ValueError("Upload a CSV with at least two numeric columns.")

    feature_column = numeric_columns[0]
    target_column = numeric_columns[1]
    X = df[[feature_column]].values
    y = df[target_column].values
    model = LinearRegression().fit(X, y)
    predictions = model.predict(X)
    return {
        "model": model,
        "feature_column": feature_column,
        "target_column": target_column,
        "X": X,
        "y": y,
        "predictions": predictions,
    }


def create_prediction_graphs(data):
    graphs = []

    fig1 = plt.figure(figsize=(8, 5), facecolor="white")
    plt.scatter(data["X"], data["y"], color="#2563eb", alpha=0.7, label="Actual")
    plt.plot(data["X"], data["predictions"], color="#dc2626", linewidth=2, label="Predicted")
    plt.xlabel(data["feature_column"])
    plt.ylabel(data["target_column"])
    plt.title("Actual vs Predicted")
    plt.legend()
    graphs.append({"title": "Actual vs Predicted", "image": create_plot_image(fig1)})

    residuals = data["y"] - data["predictions"]
    fig2 = plt.figure(figsize=(8, 5), facecolor="white")
    plt.hist(residuals, bins=20, color="#10b981", edgecolor="#065f46")
    plt.title("Residual Distribution")
    plt.xlabel("Residual")
    plt.ylabel("Count")
    graphs.append({"title": "Residual Distribution", "image": create_plot_image(fig2)})

    fig3 = plt.figure(figsize=(8, 5), facecolor="white")
    plt.plot(data["y"], color="#2563eb", label="Actual")
    plt.plot(data["predictions"], color="#dc2626", linestyle="--", label="Predicted")
    plt.title("Actual and Predicted Values")
    plt.xlabel("Sample index")
    plt.ylabel(data["target_column"])
    plt.legend()
    graphs.append({"title": "Actual and Predicted Over Samples", "image": create_plot_image(fig3)})

    return graphs


def parse_input_values(raw_value):
    if not raw_value:
        return []

    entries = [entry.strip() for entry in raw_value.split(",") if entry.strip()]
    return [float(entry) for entry in entries]


def create_prediction_context(request):
    context = {
        "has_file": False,
        "file_name": None,
        "feature_column": None,
        "target_column": None,
        "metrics": None,
        "graphs": [],
        "predictions": [],
        "error": None,
    }

    data_file = request.FILES.get("data_file")
    user_inputs = request.POST.get("input_value", "").strip()
    input_values = []

    if data_file:
        try:
            df = pd.read_csv(data_file)
            context["has_file"] = True
            context["file_name"] = data_file.name
            result = build_model_from_dataframe(df)
            graphs = create_prediction_graphs(result)
            context["feature_column"] = result["feature_column"]
            context["target_column"] = result["target_column"]
            context["graphs"] = graphs
            context["metrics"] = {
                "r2": round(r2_score(result["y"], result["predictions"]), 4),
                "mae": round(mean_absolute_error(result["y"], result["predictions"]), 4),
                "mse": round(mean_squared_error(result["y"], result["predictions"]), 4),
            }
            if user_inputs:
                input_values = parse_input_values(user_inputs)
                inputs = np.array(input_values).reshape(-1, 1)
                predicted_values = result["model"].predict(inputs)
                context["predictions"] = [
                    {"input": inp, "output": round(float(pred), 4)}
                    for inp, pred in zip(input_values, predicted_values)
                ]
        except ValueError as exc:
            context["error"] = str(exc)
        except Exception as exc:
            context["error"] = f"Unable to process the uploaded file: {exc}"
    elif user_inputs:
        try:
            input_values = parse_input_values(user_inputs)
            X = np.linspace(1, 10, len(input_values) or 10).reshape(-1, 1)
            y = 2.5 * X.squeeze() + 5 + np.random.randn(len(X)) * 3
            model = LinearRegression().fit(X, y)
            if input_values:
                inputs = np.array(input_values).reshape(-1, 1)
                predicted_values = model.predict(inputs)
                context["predictions"] = [
                    {"input": inp, "output": round(float(pred), 4)}
                    for inp, pred in zip(input_values, predicted_values)
                ]
                context["has_file"] = False
                context["file_name"] = None
                context["feature_column"] = "synthetic_feature"
                context["target_column"] = "synthetic_target"
                context["metrics"] = {
                    "r2": None,
                    "mae": None,
                    "mse": None,
                }
                context["graphs"] = create_prediction_graphs({
                    "X": X,
                    "y": y,
                    "predictions": model.predict(X),
                    "feature_column": context["feature_column"],
                    "target_column": context["target_column"],
                })
        except ValueError:
            context["error"] = "Enter valid numbers separated by commas."
        except Exception as exc:
            context["error"] = f"Unable to generate predictions: {exc}"

    return context


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

    prediction_context = create_prediction_context(request) if request.method == "POST" else None

    return render(
        request,
        "notebook_app/display.html",
        {"notebook": notebook, "mode": mode, "prediction_context": prediction_context},
    )
