"""
main.py
=======
Pipeline principal del sistema de inteligencia táctica.
Orquesta todas las fases: carga → limpieza → features → modelos → evaluación → outputs.

Uso:
    python main.py --data data/goals.csv
    python main.py --data data/goals.csv --k 4 --no-grid-search
    python main.py --data data/goals.csv --predict-team "Brazil" --knockout 1 --home 1

Argumentos:
    --data           Ruta al archivo CSV del dataset (requerido).
    --k              Número de clústeres para K-Means (default: automático).
    --no-grid-search Desactiva el Grid Search (más rápido, para pruebas).
    --predict-team   Nombre del equipo para generar mapa de riesgo.
    --knockout       1=eliminatoria, 0=fase grupos (default: 0).
    --home           1=local, 0=visitante (default: 1).
    --output-dir     Carpeta de salida (default: outputs/).
    --models-dir     Carpeta de modelos persistidos (default: models/).
"""

import argparse
import os
import sys
import json

import pandas as pd

# ── Importar módulos del proyecto ───────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_loader        import load_dataset, generate_quality_report, print_quality_report
from preprocessor       import (
    clean_dataset, detect_outliers_report,
    build_team_profiles, build_match_intervals,
    split_supervised_dataset, scale_team_profiles,
    SUPERVISED_FEATURES, SUPERVISED_TARGET,
)
from clustering_model   import (
    find_optimal_k, plot_elbow_silhouette, train_kmeans,
    run_dbscan, plot_clusters_pca, build_cluster_summary, save_model as save_cluster,
)
from classification_model import (
    get_X_y, apply_smote, train_random_forest, train_xgboost,
    evaluate_model, cross_validate_model,
    plot_confusion_matrix, plot_roc_curve,
    plot_feature_importance, plot_learning_curves,
    save_model as save_classifier, FEATURE_COLS,
)
from risk_map import get_team_risk_map, plot_risk_heatmap, get_team_profile_summary
from report_exporter import collect_report_images, export_html_report, export_pdf_report


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pipeline ML — Sistema de Inteligencia Táctica FIFA"
    )
    parser.add_argument("--data",          type=str, required=True,
                        help="Ruta al CSV del dataset.")
    parser.add_argument("--k",             type=int, default=None,
                        help="Número de clústeres K-Means. Default: automático.")
    parser.add_argument("--no-grid-search", action="store_true",
                        help="Desactiva Grid Search (más rápido).")
    parser.add_argument("--predict-team",  type=str, default=None,
                        help="Equipo para generar mapa de riesgo al final.")
    parser.add_argument("--knockout",      type=int, default=0, choices=[0, 1],
                        help="Contexto del partido: 1=eliminatoria, 0=grupos.")
    parser.add_argument("--home",          type=int, default=1, choices=[0, 1],
                        help="Condición: 1=local, 0=visitante.")
    parser.add_argument("--output-dir",    type=str, default="outputs",
                        help="Carpeta de salida para gráficas e informes.")
    parser.add_argument("--models-dir",    type=str, default="models",
                        help="Carpeta para persistir modelos entrenados.")
    parser.add_argument("--export-html",   action="store_true",
                        help="Exporta reporte en HTML (default si no hay flags).")
    parser.add_argument("--export-pdf",    action="store_true",
                        help="Exporta reporte en PDF.")
    return parser.parse_args()


def main():
    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.models_dir, exist_ok=True)

    print("\n" + "=" * 65)
    print("  SISTEMA DE INTELIGENCIA TÁCTICA — Pipeline ML")
    print("  Dataset: FIFA World Cup All Goals 1930-2022")
    print("=" * 65)

    # ── FASE 1: CARGA Y CALIDAD ──────────────────────────────────────────────────
    print("\n[FASE 1] Carga y validación del dataset...")
    df_raw    = load_dataset(args.data)
    qr        = generate_quality_report(df_raw)
    print_quality_report(qr)

    # Guardar reporte de calidad como JSON
    report_path = os.path.join(args.output_dir, "quality_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(qr, f, ensure_ascii=False, indent=2, default=str)
    print(f"  Reporte de calidad guardado: {report_path}")

    # ── FASE 2: LIMPIEZA Y OUTLIERS ──────────────────────────────────────────────
    print("\n[FASE 2] Limpieza y detección de outliers...")
    df_clean = clean_dataset(df_raw)

    outlier_report = detect_outliers_report(df_clean)
    print("  Reporte de outliers (método IQR):")
    for col, info in outlier_report.items():
        print(f"    {col}: {info['outliers']} outliers | rango válido [{info['lower_fence']}, {info['upper_fence']}]")

    # ── FASE 3: FEATURE ENGINEERING ──────────────────────────────────────────────
    print("\n[FASE 3] Ingeniería de características...")
    team_profiles   = build_team_profiles(df_clean)
    match_intervals = build_match_intervals(df_clean)

    print(f"  Perfiles de equipo        : {team_profiles.shape[0]} equipos × {team_profiles.shape[1]} features")
    print(f"  Dataset supervisado       : {match_intervals.shape[0]} registros × {match_intervals.shape[1]} columnas")
    print(f"  Balance de clases (target): {match_intervals['target'].value_counts().to_dict()}")

    # ── FASE 4a: CLUSTERING (NO SUPERVISADO) ─────────────────────────────────────
    print("\n[FASE 4a] Modelo no supervisado — K-Means...")
    X_scaled, feat_names, scaler = scale_team_profiles(team_profiles)

    # Selección automática del k óptimo
    metrics = find_optimal_k(X_scaled, k_range=range(2, 11))
    plot_elbow_silhouette(metrics, args.output_dir)

    if args.k is None:
        # Seleccionar k con mayor Silhouette Score
        best_k = metrics["k_values"][metrics["silhouettes"].index(max(metrics["silhouettes"]))]
        print(f"  k óptimo seleccionado automáticamente: {best_k} (Silhouette={max(metrics['silhouettes']):.4f})")
    else:
        best_k = args.k
        print(f"  k indicado por el usuario: {best_k}")

    km_model  = train_kmeans(X_scaled, k=best_k)
    db_labels = run_dbscan(X_scaled)

    team_profiles, cluster_summary = build_cluster_summary(team_profiles, km_model.labels_)

    plot_clusters_pca(X_scaled, km_model.labels_, list(team_profiles.index), args.output_dir)

    # Guardar resumen de clústeres
    cluster_path = os.path.join(args.output_dir, "cluster_summary.csv")
    cluster_summary.to_csv(cluster_path)
    print(f"  Resumen de clústeres guardado: {cluster_path}")

    profiles_path = os.path.join(args.output_dir, "team_profiles_with_cluster.csv")
    team_profiles.to_csv(profiles_path)

    save_cluster(km_model, os.path.join(args.models_dir, "kmeans_model.pkl"))

    # ── FASE 4b: CLASIFICACIÓN (SUPERVISADO) ─────────────────────────────────────
    print("\n[FASE 4b] Modelo supervisado — Random Forest...")
    df_train, df_val, df_test = split_supervised_dataset(match_intervals)

    X_train, y_train = get_X_y(df_train)
    X_val,   y_val   = get_X_y(df_val)
    X_test,  y_test  = get_X_y(df_test)

    # Balanceo con SMOTE sobre entrenamiento
    X_train_res, y_train_res = apply_smote(X_train, y_train)

    # Entrenar Random Forest
    use_gs = not args.no_grid_search
    rf_model = train_random_forest(X_train_res, y_train_res, use_grid_search=use_gs)

    # Validación cruzada
    print("\n  Validación cruzada (k=5) sobre conjunto de entrenamiento:")
    cv_results = cross_validate_model(rf_model, X_train_res, y_train_res)

    # Evaluación en validación y test
    print("\n  Evaluación en conjunto de VALIDACIÓN:")
    val_metrics = evaluate_model(rf_model, X_val, y_val, model_name="RF-Validación")

    print("\n  Evaluación en conjunto de PRUEBA (test):")
    test_metrics = evaluate_model(rf_model, X_test, y_test, model_name="RF-Test")

    # Gráficas de evaluación
    plot_confusion_matrix(rf_model, X_test, y_test, "Random_Forest", args.output_dir)
    plot_roc_curve(rf_model, X_test, y_test, "Random Forest", args.output_dir)
    plot_feature_importance(rf_model, FEATURE_COLS, args.output_dir)
    plot_learning_curves(rf_model, X_train_res, y_train_res, "Random Forest", args.output_dir)

    # XGBoost comparativo
    print("\n  Entrenando XGBoost (comparativo)...")
    xgb_model = train_xgboost(X_train_res, y_train_res)
    if xgb_model is not None:
        print("\n  Evaluación XGBoost en conjunto de PRUEBA:")
        evaluate_model(xgb_model, X_test, y_test, model_name="XGBoost-Test")
        plot_confusion_matrix(xgb_model, X_test, y_test, "XGBoost", args.output_dir)
        plot_roc_curve(xgb_model, X_test, y_test, "XGBoost", args.output_dir)
        save_classifier(xgb_model, os.path.join(args.models_dir, "xgboost_model.pkl"))

    save_classifier(rf_model, os.path.join(args.models_dir, "rf_model.pkl"))

    # Guardar métricas finales como JSON
    all_metrics = {
        "clustering": {
            "k": best_k,
            "silhouette": max(metrics["silhouettes"]),
            "davies_bouldin": metrics["db_scores"][metrics["k_values"].index(best_k)],
        },
        "random_forest": {
            "cross_validation": cv_results,
            "validation_set":   val_metrics,
            "test_set":         test_metrics,
        },
    }
    metrics_path = os.path.join(args.output_dir, "metrics_report.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  Reporte de métricas guardado: {metrics_path}")

    # ── FASE 5: MAPA DE RIESGO ───────────────────────────────────────────────────
    if args.predict_team:
        print(f"\n[FASE 5] Generando mapa de riesgo para: '{args.predict_team}'...")
        risk_data = get_team_risk_map(
            team_name=args.predict_team,
            model=rf_model,
            team_profiles=team_profiles,
            is_knockout=args.knockout,
            is_home=args.home,
        )
        plot_risk_heatmap(risk_data, args.output_dir)

        profile_summary = get_team_profile_summary(args.predict_team, team_profiles)
        print(f"\n  Perfil táctico de '{args.predict_team}':")
        print(f"    Clúster asignado  : {profile_summary['cluster']}")
        print(f"    Equipos similares : {profile_summary['similar_teams']}")
        print(f"    Goles/partido     : {profile_summary['avg_goals_match']}")
        print(f"    Tasa penaltis     : {profile_summary['penalty_rate']}")
        print(f"    Minuto promedio   : {profile_summary['mean_minute']}")

    # ── FASE 6: EXPORTACION DE REPORTES ───────────────────────────────────────
    export_html = args.export_html or (not args.export_html and not args.export_pdf)
    report_images = collect_report_images(args.output_dir)

    if export_html:
        html_path = export_html_report(args.output_dir, qr, all_metrics, cluster_summary, report_images)
        print(f"\n  Reporte HTML guardado: {html_path}")

    if args.export_pdf:
        pdf_path = export_pdf_report(args.output_dir, qr, all_metrics, cluster_summary, report_images)
        print(f"  Reporte PDF guardado: {pdf_path}")

    print("\n" + "=" * 65)
    print("  Pipeline completado exitosamente.")
    print(f"  Outputs en: {os.path.abspath(args.output_dir)}")
    print(f"  Modelos en: {os.path.abspath(args.models_dir)}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
