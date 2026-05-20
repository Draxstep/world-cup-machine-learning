import { useEffect, useState } from 'react';
import { fetchMetrics, fetchClusters, fetchQuality } from '../api/client';
import Loader from '../components/ui/Loader';
import ErrorBanner from '../components/ui/ErrorBanner';

function MetricCard({ label, value, sub }) {
  return (
    <div className="bg-card-bg border border-border-subtle rounded-xl p-5">
      <div className="text-3xl font-bold text-gold">{value}</div>
      <div className="text-sm text-white mt-1">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  );
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [quality, setQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([fetchMetrics(), fetchQuality()])
      .then(([m, q]) => { setMetrics(m); setQuality(q); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader text="Cargando metricas..." />;

  return (
    <main className="max-w-5xl mx-auto px-6 py-12 space-y-10">
      <div>
        <h1 className="font-display text-5xl text-gold tracking-widest mb-2">DASHBOARD</h1>
        <p className="text-gray-400 text-sm">Metricas de evaluacion - Dataset FIFA 1930-2022</p>
      </div>

      <ErrorBanner message={error} />

      {metrics && (
        <>
          <section>
            <h2 className="text-lg font-semibold text-white mb-4">Random Forest - Conjunto de Prueba</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Accuracy"
                value={`${(metrics.random_forest.test_set.accuracy * 100).toFixed(1)}%`}
              />
              <MetricCard
                label="F1 Weighted"
                value={`${(metrics.random_forest.test_set.f1_weighted * 100).toFixed(1)}%`}
              />
              <MetricCard
                label="AUC-ROC"
                value={metrics.random_forest.test_set.auc_roc.toFixed(3)}
              />
              <MetricCard
                label="F1 CV (k=5)"
                value={metrics.random_forest.cross_validation.cv_f1_mean.toFixed(3)}
                sub={`+/- ${metrics.random_forest.cross_validation.cv_f1_std.toFixed(3)}`}
              />
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white mb-4">K-Means Clustering</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <MetricCard
                label="Numero de clusters (k)"
                value={metrics.clustering.k}
              />
              <MetricCard
                label="Silhouette Score"
                value={metrics.clustering.silhouette.toFixed(4)}
              />
              <MetricCard
                label="Davies-Bouldin"
                value={metrics.clustering.davies_bouldin.toFixed(4)}
              />
            </div>
          </section>
        </>
      )}

      {quality && (
        <section>
          <h2 className="text-lg font-semibold text-white mb-4">Dataset FIFA 1930-2022</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="Registros (goles)" value={quality.total_rows.toLocaleString()} />
            <MetricCard label="Partidos unicos" value={quality.matches} />
            <MetricCard label="Selecciones" value={quality.teams} />
            <MetricCard label="Penaltis" value={quality.penalties} />
          </div>
        </section>
      )}
    </main>
  );
}
