# Sistema de Inteligencia Táctica — Módulo ML
**Proyecto Final — Electiva II | UPTC 2026**
**Autores:** Oscar Mauricio González Montañez · Hector Julio Ramírez Díaz

---

## Descripción
Pipeline de Machine Learning sobre el dataset *FIFA World Cup All Goals 1930–2022*.
Este módulo cubre toda la parte de ML (limpieza, features, modelos, evaluación).
La API REST y la interfaz web son responsabilidad del compañero de equipo (toca mejorar esa descripcion xD)

---

## Estructura del proyecto
```
proyecto_ml/
├── data/
│   └── goals.csv                   # Dataset FIFA 1930-2022
├── src/
│   ├── data_loader.py              # RF-01: carga y reporte de calidad
│   ├── preprocessor.py             # RF-02/03: limpieza + feature engineering
│   ├── clustering_model.py         # RF-04/05: K-Means + visualización PCA
│   ├── classification_model.py     # RF-06/07: Random Forest + evaluación
│   └── risk_map.py                 # RF-08/09: mapa de riesgo + perfil táctico
├── models/                         # Modelos persistidos (.pkl)
├── outputs/                        # Gráficas, métricas, reportes
├── main.py                         # Orquestador del pipeline completo
├── requirements.txt
└── README.md
```

---

## Instalación
```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd proyecto_ml

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

```

---

## Ejecución

### Pipeline completo (selección automática de k)
```bash
python main.py --data data/goals.csv
```

### Con k fijo y sin Grid Search (más rápido, útil para pruebas)
```bash
python main.py --data data/goals.csv --k 4 --no-grid-search
```

### Generar mapa de riesgo para un equipo específico
```bash
python main.py --data data/goals.csv --predict-team "brazil" --knockout 1 --home 0
```

### Todos los argumentos disponibles
| Argumento | Descripción | Default |
|---|---|---|
| `--data` | Ruta al CSV del dataset | *requerido* |
| `--k` | Número de clústeres K-Means | automático |
| `--no-grid-search` | Desactiva Grid Search | False |
| `--predict-team` | Equipo para mapa de riesgo | None |
| `--knockout` | 1=eliminatoria / 0=grupos | 0 |
| `--home` | 1=local / 0=visitante | 1 |
| `--output-dir` | Carpeta de salida | `outputs/` |
| `--models-dir` | Carpeta de modelos | `models/` |

---

## Outputs generados
| Archivo | Descripción |
|---|---|
| `outputs/quality_report.json` | Reporte de calidad del dataset |
| `outputs/elbow_silhouette.png` | Método del codo + Silhouette por k |
| `outputs/clusters_pca.png` | Scatter 2D de clústeres (PCA) |
| `outputs/cluster_summary.csv` | Medias de features por clúster |
| `outputs/team_profiles_with_cluster.csv` | Perfil de cada equipo + clúster |
| `outputs/confusion_matrix_*.png` | Matrices de confusión |
| `outputs/roc_curve_*.png` | Curvas ROC |
| `outputs/feature_importance.png` | Importancia de características |
| `outputs/learning_curve_*.png` | Curvas de aprendizaje (detección overfitting) |
| `outputs/risk_map_<equipo>.png` | Mapa de riesgo temporal |
| `outputs/metrics_report.json` | Métricas finales de ambos modelos |
| `models/kmeans_model.pkl` | Modelo K-Means persistido |
| `models/rf_model.pkl` | Modelo Random Forest persistido |
| `models/xgboost_model.pkl` | Modelo XGBoost persistido |

---

## Integración con la API (compañero)
Los módulos `risk_map.py` expone dos funciones que la API puede importar directamente:
- `get_team_risk_map(team_name, model, team_profiles, ...)` → JSON con probabilidades por intervalo.
- `get_team_profile_summary(team_name, team_profiles)` → JSON con clúster y equipos similares.

Los modelos se cargan con:
```python
import joblib
rf_model      = joblib.load("models/rf_model.pkl")
team_profiles = pd.read_csv("outputs/team_profiles_with_cluster.csv", index_col="team_name")
```
