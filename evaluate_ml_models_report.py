"""
Standalone ML evaluation report generator for EduPlus.

This script evaluates all 5 ML models used in the system without modifying
existing training/inference pipelines:
1) Placement probability model (classifier)
2) Salary value model (regressor)
3) Job role model (classifier)
4) Company recommendation model (KNN retrieval)
5) Salary tier model (multiclass classifier)

Usage:
    python evaluate_ml_models_report.py
    python evaluate_ml_models_report.py --dataset data/campus_placement_dataset_final_academic_4000.csv
"""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

from modules.feature_engineering import FeatureEngineering
from modules.ml_models import MLModels
from modules.salary_probability import SalaryTierPredictor


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        val = float(value)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    except Exception:
        return None


def _to_python(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_python(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_python(v) for v in obj]
    if isinstance(obj, tuple):
        return [_to_python(v) for v in obj]
    if isinstance(obj, (np.floating, np.float32, np.float64)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return [_to_python(v) for v in obj.tolist()]
    return obj


def _find_first_existing_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _prepare_feature_frame(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    fe = FeatureEngineering()
    df2 = fe.create_derived_features(df)
    feature_names = fe.BASE_FEATURES + fe.DERIVED_FEATURES
    missing = [c for c in feature_names if c not in df2.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")
    return df2, feature_names


def _build_placement_target(df: pd.DataFrame) -> pd.Series:
    if "placement_status" in df.columns:
        return (df["placement_status"].astype(str).str.strip().str.lower() == "placed").astype(int)

    salary_col = _find_first_existing_column(df, ["salary_lpa", "expected_salary"])
    if salary_col:
        sal = pd.to_numeric(df[salary_col], errors="coerce").fillna(0)
        return (sal > 0).astype(int)

    raise ValueError("Could not infer placement target: missing placement_status and salary columns")


def evaluate_placement_model(df: pd.DataFrame, models: MLModels, X_scaled: np.ndarray) -> Dict[str, Any]:
    y_true = _build_placement_target(df)
    y_pred = models.placement_model.predict(X_scaled)
    y_prob = models.placement_model.predict_proba(X_scaled)[:, 1]

    metrics = {
        "samples": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }

    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    except Exception:
        metrics["roc_auc"] = None

    try:
        metrics["log_loss"] = float(log_loss(y_true, np.clip(y_prob, 1e-9, 1 - 1e-9)))
    except Exception:
        metrics["log_loss"] = None

    return metrics


def evaluate_salary_model(df: pd.DataFrame, models: MLModels, feature_names: List[str]) -> Dict[str, Any]:
    salary_col = _find_first_existing_column(df, ["salary_lpa", "expected_salary"])
    if not salary_col:
        return {"available": False, "reason": "No salary column found"}

    y_salary = pd.to_numeric(df[salary_col], errors="coerce")
    placed_mask = _build_placement_target(df) == 1
    valid_mask = placed_mask & y_salary.notna()

    if valid_mask.sum() < 5:
        return {"available": False, "reason": "Insufficient placed samples with salary labels"}

    X = df.loc[valid_mask, feature_names].copy()
    X_scaled = models.scaler.transform(X)
    y_true = y_salary.loc[valid_mask].astype(float).values
    y_pred = models.salary_model.predict(X_scaled).astype(float)

    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))

    denom = np.where(np.abs(y_true) < 1e-9, np.nan, np.abs(y_true))
    mape_vals = np.abs((y_true - y_pred) / denom)
    mape = float(np.nanmean(mape_vals) * 100.0) if np.isfinite(np.nanmean(mape_vals)) else None

    return {
        "available": True,
        "samples": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": rmse,
        "r2": float(r2_score(y_true, y_pred)),
        "mape_percent": mape,
    }


def evaluate_job_role_model(df: pd.DataFrame, models: MLModels, feature_names: List[str]) -> Dict[str, Any]:
    if models.role_encoder is None:
        return {"available": False, "reason": "role_encoder not loaded"}

    role_col = _find_first_existing_column(df, ["job_role", "predicted_job_role"])
    if not role_col:
        return {"available": False, "reason": "No job role column found"}

    role_raw = df[role_col].astype(str).str.strip()
    invalid = role_raw.str.lower().isin(["", "na", "n/a", "none", "nan", "null"])
    placed_mask = _build_placement_target(df) == 1

    known_classes = set(models.role_encoder.classes_.tolist())
    class_mask = role_raw.isin(known_classes)

    valid_mask = placed_mask & (~invalid) & class_mask
    if valid_mask.sum() < 5:
        return {
            "available": False,
            "reason": "Insufficient placed samples with known job_role labels",
        }

    X = df.loc[valid_mask, feature_names].copy()
    X_scaled = models.scaler.transform(X)

    y_true_labels = role_raw.loc[valid_mask]
    y_true = models.role_encoder.transform(y_true_labels)
    y_pred = models.jobrole_model.predict(X_scaled)

    return {
        "available": True,
        "samples": int(len(y_true)),
        "num_classes_seen": int(len(np.unique(y_true))),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def evaluate_company_recommender(df: pd.DataFrame, models: MLModels, feature_names: List[str]) -> Dict[str, Any]:
    company_col = _find_first_existing_column(df, ["company_name"])
    if not company_col:
        return {"available": False, "reason": "No company_name column found"}

    placed_mask = _build_placement_target(df) == 1
    company_raw = df[company_col].astype(str).str.strip()
    invalid = company_raw.str.lower().isin(["", "na", "n/a", "none", "nan", "null"])
    valid_mask = placed_mask & (~invalid)

    if valid_mask.sum() < 5:
        return {"available": False, "reason": "Insufficient placed samples with company labels"}

    X = df.loc[valid_mask, feature_names].copy()
    X_scaled = models.scaler.transform(X)
    y_company = company_raw.loc[valid_mask].values

    top_k = 5
    hits = 0
    reciprocal_ranks: List[float] = []

    max_neighbors = len(models.companies_list) if models.companies_list is not None else 0
    if max_neighbors == 0:
        return {"available": False, "reason": "companies_list not loaded for KNN model"}

    query_neighbors = min(top_k + 1, max_neighbors)

    for i in range(len(X_scaled)):
        distances, indices = models.knn_companies.kneighbors([X_scaled[i]], n_neighbors=query_neighbors)
        neighbor_indices = indices[0].tolist()
        neighbor_dist = distances[0].tolist()

        # Try to remove exact self-match when distance is effectively zero.
        filtered: List[int] = []
        for idx, dist in zip(neighbor_indices, neighbor_dist):
            if dist <= 1e-12 and len(filtered) == 0:
                continue
            filtered.append(idx)

        top_indices = filtered[:top_k] if filtered else neighbor_indices[:top_k]
        rec_companies = [str(models.companies_list[idx]) for idx in top_indices]

        true_company = str(y_company[i])
        if true_company in rec_companies:
            hits += 1
            rank = rec_companies.index(true_company) + 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    return {
        "available": True,
        "samples": int(len(X_scaled)),
        "top_k": top_k,
        "hit_rate_at_k": float(hits / len(X_scaled)),
        "mrr_at_k": float(np.mean(reciprocal_ranks)),
    }


def evaluate_salary_tier_model(df: pd.DataFrame, predictor: SalaryTierPredictor) -> Dict[str, Any]:
    salary_col = _find_first_existing_column(df, ["salary_lpa", "expected_salary"])
    if not salary_col:
        return {"available": False, "reason": "No salary column found"}

    working = df.copy()
    if "technical_score" not in working.columns:
        working["technical_score"] = (
            pd.to_numeric(working["dsa_score"], errors="coerce")
            + pd.to_numeric(working["project_score"], errors="coerce")
            + pd.to_numeric(working["cs_fundamentals_score"], errors="coerce")
        ) / 3.0

    if "soft_skill_score" not in working.columns:
        working["soft_skill_score"] = (
            pd.to_numeric(working["aptitude_score"], errors="coerce")
            + pd.to_numeric(working["hr_score"], errors="coerce")
        ) / 2.0

    placed_mask = _build_placement_target(working) == 1
    y_salary = pd.to_numeric(working[salary_col], errors="coerce")
    y_tier = y_salary.apply(predictor.salary_to_tier)

    valid_mask = placed_mask & y_tier.notna()
    if valid_mask.sum() < 5:
        return {"available": False, "reason": "Insufficient placed samples with salary labels"}

    X = working.loc[valid_mask, predictor.feature_names].copy()
    y_true = y_tier.loc[valid_mask].astype(int).values

    X_scaled = predictor.scaler.transform(X)
    y_pred = predictor.model.predict(X_scaled)

    metrics = {
        "available": True,
        "samples": int(len(y_true)),
        "num_classes_seen": int(len(np.unique(y_true))),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }

    try:
        y_prob = predictor.model.predict_proba(X_scaled)
        metrics["log_loss"] = float(log_loss(y_true, np.clip(y_prob, 1e-9, 1 - 1e-9), labels=list(range(7))))
    except Exception:
        metrics["log_loss"] = None

    return metrics


def _render_markdown_report(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# EduPlus ML Model Evaluation Report")
    lines.append("")
    lines.append(f"Generated at: {payload['generated_at']}")
    lines.append(f"Dataset: {payload['dataset_path']}")
    lines.append(f"Rows loaded: {payload['dataset_rows']}")
    lines.append("")

    for model_name, metrics in payload["models"].items():
        lines.append(f"## {model_name}")
        if isinstance(metrics, dict) and metrics.get("available") is False:
            reason = metrics.get("reason", "Not available")
            lines.append(f"Status: Not evaluated ({reason})")
            lines.append("")
            continue

        if isinstance(metrics, dict):
            for key, val in metrics.items():
                if isinstance(val, float):
                    lines.append(f"- {key}: {val:.6f}")
                else:
                    lines.append(f"- {key}: {val}")
        else:
            lines.append(f"- value: {metrics}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def run(dataset_path: str, output_dir: str) -> Dict[str, Any]:
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)
    if df.empty:
        raise ValueError("Dataset is empty")

    df2, feature_names = _prepare_feature_frame(df)

    models = MLModels()
    if not models.load_models():
        raise RuntimeError("Failed to load main models from models/")

    X_all = df2[feature_names].copy()
    X_all_scaled = models.scaler.transform(X_all)

    report: Dict[str, Any] = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "dataset_path": dataset_path,
        "dataset_rows": int(len(df2)),
        "models": {},
    }

    report["models"]["placement_model"] = evaluate_placement_model(df2, models, X_all_scaled)

    report["models"]["salary_model"] = evaluate_salary_model(df2, models, feature_names)

    report["models"]["job_role_model"] = evaluate_job_role_model(df2, models, feature_names)

    report["models"]["company_recommendation_model"] = evaluate_company_recommender(df2, models, feature_names)

    salary_tier = SalaryTierPredictor()
    if salary_tier.load_model():
        report["models"]["salary_tier_model"] = evaluate_salary_tier_model(df2, salary_tier)
    else:
        report["models"]["salary_tier_model"] = {
            "available": False,
            "reason": "salary tier model artifacts not found in models/",
        }

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f"ml_evaluation_report_{timestamp}.json")
    md_path = os.path.join(output_dir, f"ml_evaluation_report_{timestamp}.md")

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(_to_python(report), jf, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write(_render_markdown_report(_to_python(report)))

    report["json_report_path"] = json_path
    report["markdown_report_path"] = md_path
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate all 5 EduPlus ML models and generate report")
    parser.add_argument(
        "--dataset",
        default="data/campus_placement_dataset_final_academic_4000.csv",
        help="Path to labeled dataset used for evaluation",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/model_evaluation",
        help="Directory where report files will be saved",
    )
    args = parser.parse_args()

    summary = run(dataset_path=args.dataset, output_dir=args.output_dir)

    print("\n" + "=" * 70)
    print("EDUPLUS - ALL 5 ML MODELS EVALUATION REPORT")
    print("=" * 70)
    print(f"Dataset: {summary['dataset_path']}")
    print(f"Rows: {summary['dataset_rows']}")

    for name, metrics in summary["models"].items():
        print(f"\n{name}:")
        if isinstance(metrics, dict) and metrics.get("available") is False:
            print(f"  status: not evaluated ({metrics.get('reason', 'unknown reason')})")
            continue
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.6f}")
            else:
                print(f"  {k}: {v}")

    print(f"\nJSON report: {summary['json_report_path']}")
    print(f"Markdown report: {summary['markdown_report_path']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
