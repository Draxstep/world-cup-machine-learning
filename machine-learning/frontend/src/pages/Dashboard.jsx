import { useEffect, useState } from 'react';
import { fetchMetrics, fetchClusters, fetchQuality, fetchReport, fetchTeamStats } from '../api/client';
import Loader from '../components/ui/Loader';
import ErrorBanner from '../components/ui/ErrorBanner';
import InfoTip from '../components/ui/InfoTip';
import {
  RadialBarChart, RadialBar, Legend, ResponsiveContainer,
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip as ReTooltip, Cell
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

function ClusterTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-xl border border-border-subtle bg-white p-4 shadow-xl max-w-xs">
      <div className="text-sm font-semibold text-content-main mb-2">Cluster #{point.cluster}</div>
      <div className="text-xs text-content-muted space-y-1">
        <div>Goles / partido: <span className="font-semibold text-content-main">{point.x.toFixed(2)}</span></div>
        <div>Minuto promedio: <span className="font-semibold text-content-main">{point.y.toFixed(1)}</span></div>
        <div>Partidos de muestra: <span className="font-semibold text-content-main">{point.matches_played}</span></div>
        <div>Penaltis: <span className="font-semibold text-content-main">{(point.penalty_rate * 100).toFixed(1)}%</span></div>
      </div>
      <p className="text-[11px] text-content-muted mt-3 leading-relaxed">
        Cada punto resume un cluster. Más a la derecha implica más goles por partido; más arriba, un minuto promedio mayor de anotación. El tamaño del punto refleja cuántos partidos alimentan ese cluster.
      </p>
    </div>
  );
}

function formatTeamName(name = '') {
  return String(name).replace(/(^\w|\s\w)/g, (match) => match.toUpperCase());
}

function ClusterDot({ cx, cy, payload, fill, stroke, strokeWidth, selected, onSelect }) {
  if (cx == null || cy == null) return null;

  const isActive = selected === payload.cluster;

  return (
    <circle
      cx={cx}
      cy={cy}
      r={isActive ? 10 : 7}
      fill={fill}
      stroke={stroke || (isActive ? '#0A472E' : 'transparent')}
      strokeWidth={strokeWidth || (isActive ? 2 : 0)}
      style={{ cursor: 'pointer' }}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(payload.cluster);
      }}
    />
  );
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [quality, setQuality] = useState(null);
  const [clusterSummary, setClusterSummary] = useState(null);
  const [teamStats, setTeamStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState(null);

  useEffect(() => {
    Promise.all([fetchMetrics(), fetchQuality(), fetchClusters(), fetchTeamStats()])
      .then(([m, q, c, t]) => { setMetrics(m); setQuality(q); setClusterSummary(c); setTeamStats(t); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const clusterPoints = (clusterSummary || []).map((cluster) => ({
    cluster: Number(cluster.cluster),
    x: Number(cluster.avg_goals_per_match),
    y: Number(cluster.mean_minute),
    z: Number(cluster.matches_played),
    matches_played: Number(cluster.matches_played),
    penalty_rate: Number(cluster.penalty_rate),
    knockout_goal_ratio: Number(cluster.knockout_goal_ratio),
  }));

  const clusterColors = ['#0A472E', '#199165', '#2FBF71', '#6BBF59', '#9CDB6C', '#E1B84B', '#D97706', '#B91C1C'];
  const [selectedCluster, setSelectedCluster] = useState(null);

  const teamsByCluster = (teamStats?.teams || []).reduce((accumulator, team) => {
    if (team.cluster == null) return accumulator;
    const key = Number(team.cluster);
    if (!accumulator[key]) accumulator[key] = [];
    accumulator[key].push(team);
    return accumulator;
  }, {});

  const selectedClusterTeams = selectedCluster != null ? (teamsByCluster[selectedCluster] || []) : [];

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
              setReportError(null);
              try {
                const { blob, contentType, contentDisposition } = await fetchReport('pdf');
                const url = window.URL.createObjectURL(new Blob([blob], { type: contentType }));
                const anchor = document.createElement('a');
                anchor.href = url;
                const filenameMatch = /filename=(?:"?)([^;\"]+)/i.exec(contentDisposition || '');
                anchor.download = filenameMatch ? filenameMatch[1] : 'report.pdf';
                document.body.appendChild(anchor);
                anchor.click();
                anchor.remove();
                window.URL.revokeObjectURL(url);
              } catch (err) {
                setReportError(err.message || 'Error al descargar reporte');
              } finally {
                setReportLoading(false);
              }
            }}
            disabled={reportLoading}
          >
            {reportLoading ? 'Generando reporte...' : 'Descargar reporte (PDF)'}
          </button>
        </div>
      </div>

      <ErrorBanner message={error} />
      <ErrorBanner message={reportError} />

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
                <div className="bg-surface border border-border-subtle rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="text-sm font-medium text-content-main">AUC-ROC</div>
                    <InfoTip text="Área bajo la curva ROC. Mide la capacidad del modelo para ordenar bien las clases. 0.5 es azar; 1.0 es separación perfecta." />
                  </div>
                  <div className="text-3xl font-bold text-brand-primary">{metrics.random_forest.test_set.auc_roc.toFixed(3)}</div>
                  <div className="text-xs text-content-muted mt-1">Cuanto más alto, mejor capacidad de discriminación.</div>
                </div>
                <div className="bg-surface border border-border-subtle rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="text-sm font-medium text-content-main">F1 CV (k=5)</div>
                    <InfoTip text="Promedio de F1 en validación cruzada. Sirve para ver si el modelo mantiene el rendimiento entre particiones distintas del dataset." />
                  </div>
                  <div className="text-3xl font-bold text-brand-primary">{metrics.random_forest.cross_validation.cv_f1_mean.toFixed(3)}</div>
                  <div className="text-xs text-content-muted mt-1">Desviación: +/- {metrics.random_forest.cross_validation.cv_f1_std.toFixed(3)}</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div className="bg-surface border border-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="text-sm font-medium text-content-main">Precisión</div>
                  <InfoTip text="Número de predicciones correctas sobre el total. Es útil, pero en fútbol puede ocultar problemas si las clases están desbalanceadas." />
                </div>
                <p className="text-xs text-content-muted leading-relaxed">
                  Esta métrica responde a cuántas predicciones acierta el modelo. En este proyecto se combina con F1 y AUC para evitar una lectura engañosa cuando hay clases más frecuentes que otras.
                </p>
              </div>
              <div className="bg-surface border border-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="text-sm font-medium text-content-main">F1 ponderado</div>
                  <InfoTip text="Combina precisión y recall. Cuando se pondera, las clases con más ejemplos influyen más en el promedio." />
                </div>
                <p className="text-xs text-content-muted leading-relaxed">
                  Es una forma más robusta de evaluar el modelo que la precisión sola, especialmente si hay selecciones con muchos menos casos históricos.
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-content-main mb-4">K-Means Clustering</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
              <div className="bg-surface border border-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="text-sm font-medium text-content-main">Numero de clusters (k)</div>
                  <InfoTip text="Cantidad de grupos que el algoritmo K-Means encontró en los perfiles de selecciones. Cada cluster agrupa equipos con patrones ofensivos similares." />
                </div>
                <div className="text-2xl font-semibold text-brand-primary">{metrics.clustering.k}</div>
                <div className="text-xs text-content-muted mt-1">En este dataset el modelo separa los equipos en {metrics.clustering.k} grupos de comportamiento.</div>
              </div>

              <div className="bg-surface border border-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="text-sm font-medium text-content-main">Silhouette Score</div>
                  <InfoTip text="Mide separación y cohesión de clusters. Valores cercanos a 1 indican grupos muy bien separados; cerca de 0 indica mezcla; valores negativos sugieren asignación mala." />
                </div>
                <div className="text-2xl font-semibold text-content-main">{metrics.clustering.silhouette.toFixed(4)}</div>
                <div className="text-xs text-content-muted mt-1">Más alto es mejor. Aquí sirve para leer cuán clara es la separación entre grupos.</div>
              </div>

              <div className="bg-surface border border-border-subtle rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="text-sm font-medium text-content-main">Davies-Bouldin</div>
                  <InfoTip text="Promedio de similitud entre clusters. Un valor más bajo significa que los grupos están más compactos y mejor separados." />
                </div>
                <div className="text-2xl font-semibold text-content-main">{metrics.clustering.davies_bouldin.toFixed(4)}</div>
                <div className="text-xs text-content-muted mt-1">Aquí lo importante es que baje: menor dispersión entre grupos, mejor partición.</div>
              </div>
            </div>

            <div className="mt-6 bg-surface border border-border-subtle rounded-xl p-4">
              <div className="flex items-start justify-between gap-4 mb-2">
                <div>
                  <div className="text-sm font-medium text-content-main">Visualización de clusters</div>
                  <div className="text-xs text-content-muted mt-1">Eje X = goles por partido, eje Y = minuto promedio de gol, tamaño = volumen de partidos del cluster.</div>
                </div>
                <InfoTip text="Cada punto representa un cluster completo, no un equipo individual. Sirve para comparar estilos ofensivos: clusters a la derecha anotan más; clusters hacia arriba tienden a marcar más tarde." />
              </div>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="x"
                      type="number"
                      name="Goles/partido"
                      label={{ value: 'Goles por partido', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      dataKey="y"
                      type="number"
                      name="Minuto promedio"
                      label={{ value: 'Minuto promedio', angle: -90, position: 'insideLeft' }}
                    />
                    <ZAxis dataKey="z" range={[60, 280]} />
                    <ReTooltip cursor={{ strokeDasharray: '3 3' }} content={<ClusterTooltip />} />
                    <Legend
                      wrapperStyle={{ paddingTop: 10 }}
                      formatter={() => <span className="text-content-muted font-medium">Cluster (tamaño por cantidad de partidos)</span>}
                    />
                    <Scatter
                      name="Clusters"
                      data={clusterPoints}
                      shape={(shapeProps) => (
                        <ClusterDot
                          {...shapeProps}
                          selected={selectedCluster}
                          onSelect={setSelectedCluster}
                        />
                      )}
                    />
                    {(clusterPoints || []).map((point, index) => (
                      <Cell
                        key={`cluster-${point.cluster}`}
                        fill={selectedCluster === point.cluster ? '#0A472E' : clusterColors[index % clusterColors.length]}
                        stroke={selectedCluster === point.cluster ? '#0A472E' : 'none'}
                        strokeWidth={selectedCluster === point.cluster ? 2 : 0}
                      />
                    ))}
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 bg-base border border-border-subtle rounded-xl p-4">
                <div className="flex items-center justify-between gap-4 mb-2">
                  <div className="text-sm font-medium text-content-main">
                    {selectedCluster != null ? `Equipos del Cluster #${selectedCluster}` : 'Haz click en un cluster para ver sus equipos'}
                  </div>
                  {selectedCluster != null && (
                    <button
                      type="button"
                      className="text-xs text-brand-primary hover:underline"
                      onClick={() => setSelectedCluster(null)}
                    >
                      Limpiar selección
                    </button>
                  )}
                </div>
                {selectedCluster == null ? (
                  <p className="text-xs text-content-muted leading-relaxed">
                    La lista de selecciones aparecerá aquí cuando elijas un punto del gráfico.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {selectedClusterTeams.length === 0 ? (
                      <span className="text-xs text-content-muted italic">No hay equipos asociados</span>
                    ) : (
                      [...selectedClusterTeams]
                        .sort((a, b) => formatTeamName(a.team).localeCompare(formatTeamName(b.team), 'es'))
                        .map((team) => (
                          <span key={team.team} className="px-3 py-1.5 rounded-full bg-white border border-border-subtle text-xs text-content-main font-medium">
                            {formatTeamName(team.team)}
                          </span>
                        ))
                    )}
                  </div>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 text-xs text-content-muted">
                <div className="bg-base border border-border-subtle rounded-lg p-3">Lectura rápida: a la derecha se concentran clusters con más goles por partido.</div>
                <div className="bg-base border border-border-subtle rounded-lg p-3">El tamaño del punto ayuda a distinguir clusters con más soporte histórico.</div>
                <div className="bg-base border border-border-subtle rounded-lg p-3">No representa un equipo individual, sino el promedio de un grupo de selecciones.</div>
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