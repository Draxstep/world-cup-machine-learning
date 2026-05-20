"""
clustering_model.py
===================
RF-04 | Entrenamiento del modelo de clustering con selección automática del k óptimo.
RF-05 | Visualización de clusters con PCA.

Algoritmo principal : K-Means (con inicialización K-Means++).
Algoritmo alternativo: DBSCAN (para detectar equipos atípicos).

Métricas de evaluación:
  - Inercia (WCSS) — método del codo.
  - Silhouette Score.
  - Índice Davies-Bouldin.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
import os

from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score


# ── K-MEANS ──────────────────────────────────────────────────────────────────────

def find_optimal_k(
    X_scaled: np.ndarray,
    k_range: range = range(2, 11),
    random_state: int = 42,
) -> dict:
    """
    Evalúa K-Means para distintos valores de k y calcula las métricas
    de selección: inercia (WCSS) y Silhouette Score.

    Parameters
    ----------
    X_scaled : np.ndarray
        Matriz de features escaladas (salida de scale_team_profiles).
    k_range : range
        Rango de valores de k a evaluar.
    random_state : int
        Semilla para reproducibilidad.

    Returns
    -------
    dict con keys 'k_values', 'inertias', 'silhouettes', 'db_scores'.
    """
    k_values   = list(k_range)
    inertias   = []
    silhouettes = []
    db_scores  = []

    for k in k_values:
        km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=random_state)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))
        db_scores.append(davies_bouldin_score(X_scaled, labels))

    return {"k_values": k_values, "inertias": inertias, "silhouettes": silhouettes, "db_scores": db_scores}


def plot_elbow_silhouette(metrics: dict, output_dir: str) -> None:
    """
    Genera y guarda la gráfica del método del codo y el Silhouette Score.

    Parameters
    ----------
    metrics : dict
        Salida de find_optimal_k().
    output_dir : str
        Carpeta donde guardar la imagen.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(metrics["k_values"], metrics["inertias"], marker="o", color="steelblue")
    axes[0].set_title("Método del Codo (WCSS)")
    axes[0].set_xlabel("Número de clústeres k")
    axes[0].set_ylabel("Inercia")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(metrics["k_values"], metrics["silhouettes"], marker="s", color="darkorange")
    axes[1].set_title("Silhouette Score por k")
    axes[1].set_xlabel("Número de clústeres k")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(output_dir, "elbow_silhouette.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [clustering] Gráfica del codo guardada en: {path}")


def train_kmeans(
    X_scaled: np.ndarray,
    k: int,
    random_state: int = 42,
) -> KMeans:
    """
    Entrena el modelo K-Means final con el k óptimo seleccionado.

    Parameters
    ----------
    X_scaled : np.ndarray
        Matriz escalada de perfiles de equipo.
    k : int
        Número de clústeres óptimo.
    random_state : int
        Semilla para reproducibilidad.

    Returns
    -------
    KMeans
        Modelo entrenado.
    """
    km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=random_state)
    km.fit(X_scaled)
    sil = silhouette_score(X_scaled, km.labels_)
    db  = davies_bouldin_score(X_scaled, km.labels_)
    print(f"  [clustering] K-Means k={k} | Silhouette: {sil:.4f} | Davies-Bouldin: {db:.4f} | Inercia: {km.inertia_:.2f}")
    return km


def run_dbscan(
    X_scaled: np.ndarray,
    eps: float = 1.5,
    min_samples: int = 2,
) -> np.ndarray:
    """
    Ejecuta DBSCAN como alternativa para detectar equipos atípicos (ruido = -1).

    Parameters
    ----------
    X_scaled : np.ndarray
        Matriz escalada de perfiles de equipo.
    eps : float
        Radio de vecindad.
    min_samples : int
        Mínimo de muestras para considerar un núcleo.

    Returns
    -------
    np.ndarray
        Etiquetas de clúster (-1 indica ruido/outlier).
    """
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(X_scaled)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise    = (labels == -1).sum()
    print(f"  [DBSCAN] Clústeres: {n_clusters} | Equipos atípicos (ruido): {n_noise}")
    return labels


# ── PCA + VISUALIZACIÓN ───────────────────────────────────────────────────────────

def plot_clusters_pca(
    X_scaled: np.ndarray,
    labels: np.ndarray,
    team_names: list,
    output_dir: str,
    filename: str = "clusters_pca.png",
) -> None:
    """
    Reduce a 2D con PCA y genera un scatter plot de los clústeres.
    Cada punto es una selección nacional, coloreado por clúster.

    Parameters
    ----------
    X_scaled : np.ndarray
        Matriz escalada.
    labels : np.ndarray
        Etiquetas de clúster asignadas.
    team_names : list
        Nombres de selecciones (mismo orden que X_scaled).
    output_dir : str
        Carpeta de salida.
    filename : str
        Nombre del archivo PNG.
    """
    os.makedirs(output_dir, exist_ok=True)
    pca = PCA(n_components=2, random_state=42)
    X_2d = pca.fit_transform(X_scaled)

    var_explained = pca.explained_variance_ratio_ * 100

    fig, ax = plt.subplots(figsize=(12, 8))
    unique_labels = sorted(set(labels))
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

    for lbl, color in zip(unique_labels, colors):
        mask = labels == lbl
        label_name = f"Clúster {lbl}" if lbl >= 0 else "Atípicos"
        ax.scatter(X_2d[mask, 0], X_2d[mask, 1], c=[color], label=label_name, s=80, alpha=0.8)

    # Anotar nombres de selecciones
    for i, name in enumerate(team_names):
        ax.annotate(name, (X_2d[i, 0], X_2d[i, 1]), fontsize=6, alpha=0.7,
                    xytext=(3, 3), textcoords="offset points")

    ax.set_xlabel(f"PC1 ({var_explained[0]:.1f}% varianza)")
    ax.set_ylabel(f"PC2 ({var_explained[1]:.1f}% varianza)")
    ax.set_title("Agrupación de selecciones — K-Means + PCA")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(output_dir, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [clustering] Gráfica PCA guardada en: {path}")


def build_cluster_summary(
    profiles: pd.DataFrame,
    labels: np.ndarray,
) -> pd.DataFrame:
    """
    Añade la etiqueta de clúster a los perfiles de equipo y genera
    un resumen por clúster con las medias de cada feature.

    Returns
    -------
    pd.DataFrame
        Perfiles con columna 'cluster', más un resumen por clúster.
    """
    profiles = profiles.copy()
    profiles["cluster"] = labels

    summary = profiles.groupby("cluster").mean(numeric_only=True).round(4)
    return profiles, summary


# ── PERSISTENCIA ─────────────────────────────────────────────────────────────────

def save_model(model, path: str) -> None:
    """Persiste el modelo K-Means en disco con joblib."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"  [clustering] Modelo guardado en: {path}")


def load_model(path: str):
    """Carga un modelo K-Means persistido."""
    return joblib.load(path)
