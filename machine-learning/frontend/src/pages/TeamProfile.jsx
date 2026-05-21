import { useEffect, useMemo, useState } from 'react';
import { fetchTeamProfile, fetchClusters, fetchTeamReport } from '../api/client';
import { useTeamStats } from '../hooks/useTeamStats';
import { useFlag } from '../hooks/useFlag';
import TeamSelector from '../components/ui/TeamSelector';
import Loader from '../components/ui/Loader';
import ErrorBanner from '../components/ui/ErrorBanner';
import InfoTip from '../components/ui/InfoTip';
import FlagBadge from '../components/ui/FlagBadge';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';

function StatCard({ label, value, tooltip, delta }) {
  return (
    <div className="bg-base border border-border-subtle shadow-sm rounded-xl p-4 text-center">
      <div className="text-2xl font-bold text-brand-primary">{value}</div>
      <div className="text-xs text-content-muted mt-1 flex items-center justify-center gap-2 font-medium">
        <span>{label}</span>
        <InfoTip text={tooltip} />
      </div>
      {delta != null && (
        <div className={`text-[11px] mt-2 font-medium ${delta > 0 ? 'text-brand-primary' : 'text-red-500'}`}>
          {delta > 0 ? '↑' : '↓'} {Math.abs(delta).toFixed(2)} vs promedio
        </div>
      )}
    </div>
  );
}

function SimilarTeamTag({ name, useApiFlags }) {
  const flagUrl = useFlag(name, useApiFlags);
  return (
    <span className="flex items-center gap-2 bg-base border border-border-subtle shadow-sm
                     text-content-main font-medium text-xs px-3 py-1.5 rounded-full capitalize">
      <FlagBadge src={flagUrl} name={name} size={18} />
      {name.replace(/(^\w|\s\w)/g, (m) => m.toUpperCase())}
    </span>
  );
}

export default function TeamProfile() {
  const { teams: statsTeams, source, loading: statsLoading } = useTeamStats();
  const [team, setTeam] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [clusters, setClusters] = useState([]);
  const [useApiFlags, setUseApiFlags] = useState(true);

  useEffect(() => {
    fetchClusters()
      .then((result) => setClusters(result))
      .catch(() => setClusters([]));
  }, []);
  const clusterRow = useMemo(() => (
    clusters.find((c) => c.cluster === data?.cluster)
  ), [clusters, data?.cluster]);

  const selectedTeamStats = useMemo(() => (
    statsTeams.find((t) => t.team === team) || null
  ), [statsTeams, team]);

  const flagUrlForData = useFlag(data?.team || team, true);

  const deltaAvgGoals = useMemo(() => {
    if (!clusterRow || data?.avg_goals_match == null) return null;
    return data.avg_goals_match - (clusterRow.avg_goals_per_match || 0);
  }, [clusterRow, data?.avg_goals_match]);

  const radarData = useMemo(() => {
    if (!data) return [];
    const cluster = clusterRow || {};
    const clamp = (value, max) => Math.max(0, Math.min(100, (value / max) * 100));
    return [
      {
        metric: 'Goles/Partido',
        equipo: clamp(data.avg_goals_match, 3),
        cluster: clamp(cluster.avg_goals_per_match || 0, 3),
      },
      {
        metric: 'Penaltis',
        equipo: clamp(data.penalty_rate, 1),
        cluster: clamp(cluster.penalty_rate || 0, 1),
      },
      {
        metric: 'Autogoles',
        equipo: clamp(data.own_goal_rate, 1),
        cluster: clamp(cluster.own_goal_rate || 0, 1),
      },
      {
        metric: 'Minuto',
        equipo: clamp(data.mean_minute, 90),
        cluster: clamp(cluster.mean_minute || 0, 90),
      },
      {
        metric: 'Eliminatoria',
        equipo: clamp(data.knockout_ratio, 1),
        cluster: clamp(cluster.knockout_goal_ratio || 0, 1),
      },
    ];
  }, [data, clusterRow]);

  const handleFetch = async () => {
    if (!team) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTeamProfile(team);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="font-display text-5xl text-content-main tracking-widest mb-2 flex items-center gap-4">
        <span className="sr-only">Perfil tactico</span>
        PERFIL TACTICO
      </h1>
      <p className="text-content-muted mb-8 text-sm">
        Cluster historico K-Means y equipos con perfil ofensivo similar
      </p>

      <div className="bg-surface border border-border-subtle rounded-2xl p-6 mb-8 shadow-sm">
        <div className="mb-4">
          <label className="block text-xs text-content-muted mb-1.5 font-medium">Equipo</label>
          <TeamSelector teams={statsTeams.map((t) => t.team)} value={team} onChange={setTeam} disabled={statsLoading} />
        </div>
        <div className="flex items-center justify-between text-xs text-content-muted mb-4 font-medium">
          <span>Fuente flags: {source}</span>
          <label className="inline-flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useApiFlags}
              onChange={(e) => setUseApiFlags(e.target.checked)}
              className="accent-brand-primary"
            />
            Usar API externa
          </label>
        </div>
        <button
          onClick={handleFetch}
          disabled={!team || loading}
          className="w-full bg-brand-primary text-white font-semibold px-8 py-2.5 rounded-lg
                     hover:bg-brand-dark disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Cargando...' : 'Ver Perfil'}
        </button>
      </div>

      <ErrorBanner message={error} />
      {loading && <Loader text="Consultando perfil tactico..." />}

      {data && !loading && (
        <div className="bg-surface border border-border-subtle rounded-2xl p-6 space-y-6 shadow-sm">
          <div>
            <div className="flex items-center gap-4">
              <FlagBadge src={flagUrlForData} name={data.team} size={48} />
              <h2 className="font-display text-3xl text-content-main tracking-wide">
                {data.team.replace(/(^\w|\s\w)/g, (m) => m.toUpperCase())}
              </h2>
            </div>
            <span className="inline-block mt-2 bg-brand-accent/20 text-brand-dark text-xs font-semibold
                             px-3 py-1 rounded-full border border-brand-accent/30">
              Cluster #{data.cluster}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              className="px-4 py-2 bg-brand-primary hover:bg-brand-dark text-white text-sm font-medium rounded-md transition-colors"
              onClick={async () => {
                try {
                  const { blob, contentType, contentDisposition } = await fetchTeamReport({ team: data.team, format: 'pdf', mode: 'profile' });
                  const url = window.URL.createObjectURL(new Blob([blob], { type: contentType }));
                  const a = document.createElement('a');
                  a.href = url;
                  const filenameMatch = /filename=(?:"?)([^;\"]+)/i.exec(contentDisposition || '')
                  a.download = filenameMatch ? filenameMatch[1] : `${data.team}_profile.pdf`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  window.URL.revokeObjectURL(url);
                } catch (err) {
                  alert(err.message || 'Error al descargar reporte');
                }
              }}
            >Descargar PDF</button>

            <button
              className="px-4 py-2 bg-base border border-border-subtle text-content-main text-sm font-medium rounded-md hover:bg-surface transition-colors"
              onClick={async () => {
                try {
                  const { blob, contentType, contentDisposition } = await fetchTeamReport({ team: data.team, format: 'csv', mode: 'profile' });
                  const url = window.URL.createObjectURL(new Blob([blob], { type: contentType }));
                  const a = document.createElement('a');
                  a.href = url;
                  const filenameMatch = /filename=(?:"?)([^;\"]+)/i.exec(contentDisposition || '')
                  a.download = filenameMatch ? filenameMatch[1] : `${data.team}_profile.csv`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  window.URL.revokeObjectURL(url);
                } catch (err) {
                  alert(err.message || 'Error al descargar CSV');
                }
              }}
            >Descargar CSV</button>
          </div>

          {selectedTeamStats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-base border border-border-subtle p-4 rounded-xl shadow-sm">
              <div className="text-xs text-content-muted font-medium">
                <div className="mb-1">Participaciones</div>
                <div className="text-content-main text-lg font-bold">{selectedTeamStats.participations}</div>
              </div>
              <div className="text-xs text-content-muted font-medium">
                <div className="mb-1">Titulos</div>
                <div className="text-content-main text-lg font-bold">{selectedTeamStats.titles}</div>
              </div>
              <div className="text-xs text-content-muted font-medium">
                <div className="mb-1">Mejor posicion</div>
                <div className="text-content-main text-lg font-bold">{selectedTeamStats.best_finish}</div>
              </div>
              <div className="text-xs text-content-muted font-medium">
                <div className="mb-1">Ultima participacion</div>
                <div className="text-content-main text-lg font-bold">{selectedTeamStats.last_participation || 'N/D'}</div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard
              label="Goles / partido"
              value={data.avg_goals_match.toFixed(2)}
              tooltip="Promedio historico de goles por partido con gol registrado."
              delta={deltaAvgGoals}
            />
            <StatCard
              label="Tasa penaltis"
              value={`${(data.penalty_rate * 100).toFixed(1)}%`}
              tooltip="Proporcion de goles de penalti sobre el total de goles."
            />
            <StatCard
              label="Minuto promedio"
              value={data.mean_minute.toFixed(1)}
              tooltip="Minuto promedio de anotacion en los goles del equipo."
            />
            <StatCard
              label="Ratio eliminatoria"
              value={`${(data.knockout_ratio * 100).toFixed(1)}%`}
              tooltip="Proporcion de goles anotados en fase eliminatoria."
            />
          </div>

          <div className="bg-base border border-border-subtle rounded-2xl p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-content-main">Radar ofensivo vs cluster</h3>
              <span className="text-xs text-content-muted font-medium">Escala normalizada</span>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#64748b', fontSize: 11, fontWeight: 500 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} />
                <Radar name="Equipo" dataKey="equipo" stroke="#199165" fill="#199165" fillOpacity={0.4} />
                <Radar name="Cluster" dataKey="cluster" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-content-main mb-3">
              Equipos historicos similares (mismo cluster)
            </h3>
            <div className="flex flex-wrap gap-2">
              {data.similar_teams.length === 0 ? (
                <span className="text-content-muted text-sm italic">Sin equipos similares en este cluster</span>
              ) : (
                [...data.similar_teams]
                  .sort((a, b) => a.localeCompare(b))
                  .map((t) => (
                    <SimilarTeamTag key={t} name={t} useApiFlags={useApiFlags} />
                  ))
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}