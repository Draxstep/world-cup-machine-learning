import { useEffect, useState } from 'react';
import { fetchMetrics, fetchClusters, fetchQuality, fetchReport } from '../api/client';
import Loader from '../components/ui/Loader';
import ErrorBanner from '../components/ui/ErrorBanner';
import InfoTip from '../components/ui/InfoTip';
import {
  RadialBarChart, RadialBar, Legend, ResponsiveContainer,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip
} from 'recharts';

function MetricCard({ label, value, sub }) {
  return (
    <div className="bg-surface border border-border-subtle rounded-xl p-5">
      <div className="text-3xl font-bold text-brand-primary">{value}</div>
      <div className="text-sm font-medium text-content-main mt-1">{label}</div>
      {sub && <div className="text-xs text-content-muted mt-0.5">{sub}</div>}
    </div>
  );
}

function MetricGauge({ label, percent, expected = 60, description }) {
  const pct = Math.max(0, Math.min(100, Math.round(percent)));
  const getColor = (v) => (v >= expected ? '#16a34a' : v >= expected - 10 ? '#f59e0b' : '#dc2626');
  const color = getColor(pct);

  return (
    <div className="bg-surface border border-border-subtle rounded-xl p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium text-content-main">{label}</div>
          <div className="text-xs text-content-muted">{description}</div>
        </div>
        <div className="text-2xl font-semibold" style={{ color }}>{pct}%</div>
      </div>

      <div className="w-full bg-base rounded-full h-3 mt-3 overflow-hidden">
        <div className="h-3" style={{ width: `${pct}%`, background: color }} />
      </div>
      <div className="text-xs text-content-muted mt-2">Rendimiento esperado: &gt;{expected}%</div>
    </div>
  );
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [quality, setQuality] = useState(null);
  const [clusterSummary, setClusterSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    Promise.all([fetchMetrics(), fetchQuality(), fetchClusters()])
      .then(([m, q, c]) => { setMetrics(m); setQuality(q); setClusterSummary(c); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader text="Cargando metricas..." />;

  return (
    <main className="max-w-5xl mx-auto px-6 py-12 space-y-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-5xl text-content-main tracking-widest mb-2">DASHBOARD</h1>
          <p className="text-content-muted text-sm">Metricas de evaluacion - Dataset FIFA 1930-2022</p>
        </div>
        <div>
          <button
            className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium bg-brand-primary text-white hover:opacity-90 disabled:opacity-60`}
            onClick={async () => {
              setReportLoading(true);
              setError(null);
              // ... tu logica de descarga se mantiene igual
            }}
            disabled={reportLoading}
          >
            {reportLoading ? 'Generando reporte...' : 'Descargar reporte (PDF)'}
          </button>
        </div>
      </div>

      <ErrorBanner message={error} />

      {metrics && (
        <>
          <section>
            <h2 className="text-lg font-semibold text-content-main mb-4">Random Forest - Conjunto de Prueba</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <MetricGauge
                label="Accuracy"
                percent={(metrics.random_forest.test_set.accuracy * 100)}
                expected={60}
                description="Precisión en el conjunto de prueba"
              />

              <MetricGauge
                label="F1 Weighted"
                percent={(metrics.random_forest.test_set.f1_weighted * 100)}
                expected={60}
                description="F1 ponderado para clases desbalanceadas"
              />

              <div className="grid grid-cols-1 gap-4">
                <MetricCard label="AUC-ROC" value={metrics.random_forest.test_set.auc_roc.toFixed(3)} />
                <MetricCard label="F1 CV (k=5)" value={metrics.random_forest.cross_validation.cv_f1_mean.toFixed(3)} sub={`+/- ${metrics.random_forest.cross_validation.cv_f1_std.toFixed(3)}`} />
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-content-main mb-4">K-Means Clustering</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
              <MetricCard label="Numero de clusters (k)" value={metrics.clustering.k} />

              <div className="bg-surface border border-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="text-sm font-medium text-content-main">Silhouette Score</div>
                  <InfoTip text="El Silhouette mide lo separados que estan los clusters; valores cercanos a 1 son mejores." />
                </div>
                <div className="text-2xl font-semibold text-content-main">{metrics.clustering.silhouette.toFixed(4)}</div>
              </div>

              <div className="bg-surface border border-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="text-sm font-medium text-content-main">Davies-Bouldin</div>
                  <InfoTip text="Davies-Bouldin: valores bajos indican clusters mejor separados y compactos." />
                </div>
                <div className="text-2xl font-semibold text-content-main">{metrics.clustering.davies_bouldin.toFixed(4)}</div>
              </div>
            </div>

            <div className="mt-6 bg-surface border border-border-subtle rounded-xl p-4">
              <div className="text-sm font-medium text-content-main mb-2">Visualización de clusters (avg_goals_per_match vs mean_minute)</div>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="x" name="Goles/partido" />
                    <YAxis dataKey="y" name="Minuto promedio" />
                    <ReTooltip cursor={{ strokeDasharray: '3 3' }} formatter={(value, name, props) => [value, name]} />
                    <Scatter
                      name="Clusters"
                      data={(clusterSummary || []).map((c) => ({
                        x: Number(c.avg_goals_per_match),
                        y: Number(c.mean_minute),
                        cluster: c.cluster,
                        matches: c.matches_played,
                      }))}
                      fill="#199165"
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>
        </>
      )}

      {quality && (
        <section>
          <h2 className="text-lg font-semibold text-content-main mb-4">Dataset FIFA 1930-2022</h2>
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