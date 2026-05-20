"""
classification_model.py
=======================
RF-06 | Entrenamiento del modelo supervisado con validación cruzada.
RF-07 | Evaluación: matriz de confusión, accuracy, precisión, recall, F1, AUC-ROC.

Algoritmo principal  : Random Forest (clasificación binaria).
Algoritmo comparativo: XGBoost.

Estrategia de desbalance: class_weight='balanced' + opcionalmente SMOTE.
Validación           : k-fold estratificado (k=5) + Grid Search de hiperparámetros.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_validate, learning_curve
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, ConfusionMatrixDisplay, RocCurveDisplay,
    classification_report,
)
from sklearn.preprocessing import label_binarize

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("  [aviso] XGBoost no disponible. Solo se entrenará Random Forest.")

try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False


FEATURE_COLS = [
    "interval_encoded",
    "is_knockout",
    "is_home",
    "team_goals_hist",
    "team_pen_rate",
    "team_mean_minute",
]
TARGET_COL = "target"


# ── PREPARACIÓN DE DATOS ─────────────────────────────────────────────────────────

def get_X_y(df: pd.DataFrame):
    """
    Extrae la matriz de features X y el vector objetivo y desde el DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Subconjunto (train, val o test) del dataset supervisado.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
    """
    X = df[FEATURE_COLS].values.astype(float)
    y = df[TARGET_COL].values.astype(int)
    return X, y


def apply_smote(X_train: np.ndarray, y_train: np.ndarray, random_state: int = 42):
    """
    Aplica SMOTE al conjunto de entrenamiento para balancear clases.
    Solo se aplica si imbalanced-learn está disponible.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (X_resampled, y_resampled)
    """
    if not SMOTE_AVAILABLE:
        print("  [aviso] imbalanced-learn no disponible. Usando datos sin SMOTE.")
        return X_train, y_train

    sm = SMOTE(random_state=random_state)
    X_res, y_res = sm.fit_resample(X_train, y_train)
    print(f"  [SMOTE] Antes: {len(y_train)} | Después: {len(y_res)}")
    return X_res, y_res


# ── RANDOM FOREST ─────────────────────────────────────────────────────────────────

def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    use_grid_search: bool = True,
    random_state: int = 42,
) -> RandomForestClassifier:
    """
    Entrena un clasificador Random Forest.
    Si use_grid_search=True, ajusta hiperparámetros con GridSearchCV (k=5 estratificado).

    Justificación del algoritmo:
      - Robusto ante desbalance de clases (class_weight='balanced').
      - Maneja variables categóricas codificadas y numéricas sin normalización adicional.
      - Provee importancia de características para interpretabilidad.
      - Resistente al sobreajuste mediante bagging de árboles.

    Parameters
    ----------
    X_train, y_train : np.ndarray
        Datos de entrenamiento.
    use_grid_search : bool
        Si True, realiza búsqueda de hiperparámetros.
    random_state : int
        Semilla de reproducibilidad.

    Returns
    -------
    RandomForestClassifier
        Modelo entrenado (mejor estimador si se usó Grid Search).
    """
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)

    if use_grid_search:
        param_grid = {
            "n_estimators": [100, 200],
            "max_depth":    [None, 10, 20],
            "min_samples_split": [2, 5],
            "class_weight": ["balanced"],
        }
        base_rf = RandomForestClassifier(random_state=random_state)
        gs = GridSearchCV(
            base_rf, param_grid,
            cv=cv, scoring="f1", n_jobs=-1, verbose=0,
        )
        gs.fit(X_train, y_train)
        print(f"  [RF] Mejores hiperparámetros: {gs.best_params_}")
        print(f"  [RF] Mejor F1 (CV): {gs.best_score_:.4f}")
        return gs.best_estimator_
    else:
        rf = RandomForestClassifier(
            n_estimators=200, max_depth=None,
            class_weight="balanced", random_state=random_state,
        )
        rf.fit(X_train, y_train)
        return rf


# ── XGBOOST (COMPARATIVO) ─────────────────────────────────────────────────────────

def train_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    random_state: int = 42,
):
    """
    Entrena XGBoost como modelo comparativo frente a Random Forest.
    Maneja desbalance mediante scale_pos_weight.

    Returns
    -------
    XGBClassifier o None si XGBoost no está disponible.
    """
    if not XGBOOST_AVAILABLE:
        return None

    ratio = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=ratio,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=random_state,
        verbosity=0,
    )
    xgb.fit(X_train, y_train)
    print(f"  [XGBoost] scale_pos_weight={ratio:.2f} (ajuste de desbalance)")
    return xgb


# ── EVALUACIÓN ────────────────────────────────────────────────────────────────────

def evaluate_model(
    model,
    X: np.ndarray,
    y: np.ndarray,
    model_name: str = "Modelo",
) -> dict:
    """
    Calcula todas las métricas de evaluación para un conjunto dado.

    Métricas calculadas:
      - Accuracy
      - Precisión (macro y ponderada)
      - Recall    (macro y ponderado)
      - F1-score  (macro y ponderado)
      - AUC-ROC

    Parameters
    ----------
    model : clasificador entrenado (Random Forest o XGBoost).
    X : np.ndarray
        Features del conjunto a evaluar.
    y : np.ndarray
        Etiquetas reales.
    model_name : str
        Nombre del modelo (para impresión).

    Returns
    -------
    dict
        Diccionario con todas las métricas.
    """
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None

    metrics = {
        "accuracy":         round(accuracy_score(y, y_pred), 4),
        "precision_macro":  round(precision_score(y, y_pred, average="macro", zero_division=0), 4),
        "precision_weighted": round(precision_score(y, y_pred, average="weighted", zero_division=0), 4),
        "recall_macro":     round(recall_score(y, y_pred, average="macro", zero_division=0), 4),
        "recall_weighted":  round(recall_score(y, y_pred, average="weighted", zero_division=0), 4),
        "f1_macro":         round(f1_score(y, y_pred, average="macro", zero_division=0), 4),
        "f1_weighted":      round(f1_score(y, y_pred, average="weighted", zero_division=0), 4),
        "auc_roc":          round(roc_auc_score(y, y_prob), 4) if y_prob is not None else None,
    }

    print(f"\n  ── Métricas: {model_name} ──")
    for k, v in metrics.items():
        print(f"     {k:<25}: {v}")
    print(f"\n{classification_report(y, y_pred, target_names=['Sin gol', 'Con gol'], zero_division=0)}")

    return metrics


def cross_validate_model(
    model,
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42,
) -> dict:
    """
    Aplica validación cruzada estratificada (k-fold) al modelo.

    Returns
    -------
    dict
        Medias y desviaciones estándar de accuracy y F1.
    """
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    scores = cross_validate(
        model, X, y, cv=cv,
        scoring=["accuracy", "f1_weighted", "roc_auc"],
        n_jobs=-1,
    )
    result = {
        "cv_accuracy_mean":  round(scores["test_accuracy"].mean(), 4),
        "cv_accuracy_std":   round(scores["test_accuracy"].std(), 4),
        "cv_f1_mean":        round(scores["test_f1_weighted"].mean(), 4),
        "cv_f1_std":         round(scores["test_f1_weighted"].std(), 4),
        "cv_auc_mean":       round(scores["test_roc_auc"].mean(), 4),
        "cv_auc_std":        round(scores["test_roc_auc"].std(), 4),
    }
    print(f"\n  [CV k={n_splits}] Accuracy: {result['cv_accuracy_mean']} ± {result['cv_accuracy_std']}")
    print(f"  [CV k={n_splits}] F1:       {result['cv_f1_mean']} ± {result['cv_f1_std']}")
    print(f"  [CV k={n_splits}] AUC-ROC:  {result['cv_auc_mean']} ± {result['cv_auc_std']}")
    return result


# ── GRÁFICAS ──────────────────────────────────────────────────────────────────────

def plot_confusion_matrix(
    model,
    X: np.ndarray,
    y: np.ndarray,
    model_name: str,
    output_dir: str,
) -> None:
    """Genera y guarda la matriz de confusión."""
    os.makedirs(output_dir, exist_ok=True)
    y_pred = model.predict(X)
    cm = confusion_matrix(y, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Sin gol", "Con gol"])
    fig, ax = plt.subplots(figsize=(5, 4))
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(f"Matriz de Confusión — {model_name}")
    plt.tight_layout()
    path = os.path.join(output_dir, f"confusion_matrix_{model_name.replace(' ', '_')}.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [eval] Matriz de confusión guardada en: {path}")


def plot_roc_curve(
    model,
    X: np.ndarray,
    y: np.ndarray,
    model_name: str,
    output_dir: str,
) -> None:
    """Genera y guarda la curva ROC."""
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    RocCurveDisplay.from_estimator(model, X, y, ax=ax, name=model_name)
    ax.set_title(f"Curva ROC — {model_name}")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, f"roc_curve_{model_name.replace(' ', '_')}.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [eval] Curva ROC guardada en: {path}")


def plot_feature_importance(
    model: RandomForestClassifier,
    feature_names: list,
    output_dir: str,
) -> None:
    """Genera y guarda el gráfico de importancia de características."""
    os.makedirs(output_dir, exist_ok=True)
    importances = model.feature_importances_
    idx = np.argsort(importances)[::-1]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(range(len(feature_names)), importances[idx], color="steelblue", alpha=0.8)
    ax.set_xticks(range(len(feature_names)))
    ax.set_xticklabels([feature_names[i] for i in idx], rotation=30, ha="right")
    ax.set_title("Importancia de Características — Random Forest")
    ax.set_ylabel("Importancia (Gini)")
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    path = os.path.join(output_dir, "feature_importance.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [eval] Importancia de características guardada en: {path}")


def plot_learning_curves(
    model,
    X: np.ndarray,
    y: np.ndarray,
    model_name: str,
    output_dir: str,
    random_state: int = 42,
) -> None:
    """
    Genera curvas de aprendizaje para detectar sobreajuste u underfitting.
    Compara el score de entrenamiento vs. validación cruzada en función
    del tamaño del conjunto de entrenamiento.
    """
    os.makedirs(output_dir, exist_ok=True)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    train_sizes, train_scores, val_scores = learning_curve(
        model, X, y, cv=cv, scoring="f1_weighted",
        train_sizes=np.linspace(0.1, 1.0, 8), n_jobs=-1,
    )

    train_mean = train_scores.mean(axis=1)
    train_std  = train_scores.std(axis=1)
    val_mean   = val_scores.mean(axis=1)
    val_std    = val_scores.std(axis=1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(train_sizes, train_mean, "o-", color="steelblue", label="Entrenamiento")
    ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.15, color="steelblue")
    ax.plot(train_sizes, val_mean, "s-", color="darkorange", label="Validación (CV)")
    ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.15, color="darkorange")
    ax.set_xlabel("Tamaño del conjunto de entrenamiento")
    ax.set_ylabel("F1-score ponderado")
    ax.set_title(f"Curvas de Aprendizaje — {model_name}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = os.path.join(output_dir, f"learning_curve_{model_name.replace(' ', '_')}.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [eval] Curva de aprendizaje guardada en: {path}")


# ── PERSISTENCIA ──────────────────────────────────────────────────────────────────

def save_model(model, path: str) -> None:
    """Persiste el modelo entrenado con joblib."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"  [clasificación] Modelo guardado en: {path}")


def load_model(path: str):
    """Carga un modelo clasificador persistido."""
    return joblib.load(path)
