import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip as ReTooltip,
  Cell, ResponsiveContainer, Legend, LabelList,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import { fetchClusters, fetchTeamProfile, fetchTeamReport } from '../api/client';
import { useTeamStats } from '../hooks/useTeamStats';
import { useTeamCatalog } from '../hooks/useTeamCatalog';
import { useRiskMap } from '../hooks/useRiskMap';
import { useFlag } from '../hooks/useFlag';
import CountryAutocomplete from '../components/ui/CountryAutocomplete';
import Loader from '../components/ui/Loader';
import ErrorBanner from '../components/ui/ErrorBanner';
import FlagBadge from '../components/ui/FlagBadge';
import InfoTip from '../components/ui/InfoTip';

function formatTeamLabel(team = '') {
  return String(team).replace(/(^\w|\s\w)/g, (match) => match.toUpperCase());
}

function probToColor(p) {
  const start = [20, 68, 48];
  const end = [185, 223, 122];
  const r = Math.round(start[0] + (end[0] - start[0]) * p);
  const g = Math.round(start[1] + (end[1] - start[1]) * p);
  const b = Math.round(start[2] + (end[2] - start[2]) * p);
  return `rgb(${r},${g},${b})`;
}

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

function SimilarTeamTag({ name }) {
  const flagUrl = useFlag(name, true);
  return (
    <span className="flex items-center gap-2 bg-base border border-border-subtle shadow-sm text-content-main font-medium text-xs px-3 py-1.5 rounded-full capitalize">
      <FlagBadge src={flagUrl} name={name} size={18} />
      {formatTeamLabel(name)}
    </span>
  );
}

function SectionCard({ title, subtitle, children }) {
  return (
    <section className="bg-surface border border-border-subtle rounded-2xl p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="text-xl font-semibold text-content-main">{title}</h2>
          {subtitle && <p className="text-sm text-content-muted mt-1">{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

function CountryFlagsByContinent({ groups, onSelectTeam }) {
  return (
    <div className="space-y-6">
      {groups.map(({ continent, teams }) => (
        <section key={continent}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-content-main">{continent}</h3>
            <span className="text-xs text-content-muted">{teams.length} selecciones</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {teams.map((team) => (
              <button
                key={team.team}
                type="button"
                onClick={() => onSelectTeam(team.team)}
                className="group flex flex-col items-center gap-2 rounded-xl border border-border-subtle bg-base p-3 text-center transition-all hover:-translate-y-0.5 hover:border-brand-primary hover:shadow-lg hover:shadow-brand-primary/10"
              >
                <FlagBadge src={team.flagUrl} name={team.label} size={40} />
                <span className="text-xs font-medium text-content-main capitalize leading-tight">
                  {team.label}
                </span>
              </button>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export default function TeamAnalysis() {
  const navigate = useNavigate();
  const { team: teamParam } = useParams();
  const selectedTeam = decodeURIComponent(teamParam || '').trim().toLowerCase();

  const { teams: statsTeams, loading: statsLoading, error: statsError } = useTeamStats();
  const teamNames = useMemo(() => statsTeams.map((item) => item.team), [statsTeams]);
  const { catalog, grouped, loading: catalogLoading } = useTeamCatalog(teamNames);
  const { data: riskMapData, loading: riskLoading, error: riskError, fetchData: fetchRiskMap } = useRiskMap();

  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [clusters, setClusters] = useState([]);
  const [knockout, setKnockout] = useState(0);
  const [home, setHome] = useState(1);
  const detailRef = useRef(null);

  const selectedCatalogItem = useMemo(
    () => catalog.find((item) => item.team === selectedTeam) || null,
    [catalog, selectedTeam]
  );

  const selectedTeamStats = useMemo(
    () => statsTeams.find((item) => item.team === selectedTeam) || null,
    [statsTeams, selectedTeam]
  );

  const clusterRow = useMemo(
    () => clusters.find((item) => Number(item.cluster) === Number(profile?.cluster)),
    [clusters, profile?.cluster]
  );

  const radarData = useMemo(() => {
    if (!profile) return [];
    const cluster = clusterRow || {};
    const clamp = (value, max) => Math.max(0, Math.min(100, (value / max) * 100));
    return [
      {
        metric: 'Goles/Partido',
        equipo: clamp(profile.avg_goals_match, 3),
        cluster: clamp(cluster.avg_goals_per_match || 0, 3),
      },
      {
        metric: 'Penaltis',
        equipo: clamp(profile.penalty_rate, 1),
        cluster: clamp(cluster.penalty_rate || 0, 1),
      },
      {
        metric: 'Autogoles',
        equipo: clamp(profile.own_goal_rate, 1),
        cluster: clamp(cluster.own_goal_rate || 0, 1),
      },
      {
        metric: 'Minuto',
        equipo: clamp(profile.mean_minute, 90),
        cluster: clamp(cluster.mean_minute || 0, 90),
      },
      {
        metric: 'Eliminatoria',
        equipo: clamp(profile.knockout_ratio, 1),
        cluster: clamp(cluster.knockout_goal_ratio || 0, 1),
      },
    ];
  }, [profile, clusterRow]);

  const deltaAvgGoals = useMemo(() => {
    if (!clusterRow || profile?.avg_goals_match == null) return null;
    return profile.avg_goals_match - (clusterRow.avg_goals_per_match || 0);
  }, [clusterRow, profile?.avg_goals_match]);

  const flagUrl = useFlag(selectedTeam, true);

  useEffect(() => {
    fetchClusters()
      .then((result) => setClusters(result))
      .catch(() => setClusters([]));
  }, []);

  useEffect(() => {
    if (!selectedTeam) {
      setProfile(null);
      setProfileError(null);
      return;
    }

    setProfileLoading(true);
    setProfileError(null);
    setKnockout(0);
    setHome(1);

    fetchTeamProfile(selectedTeam)
      .then((result) => setProfile(result))
      .catch((err) => setProfileError(err.message))
      .finally(() => setProfileLoading(false));
  }, [selectedTeam]);

  useEffect(() => {
    if (!selectedTeam) return;
    fetchRiskMap(selectedTeam, knockout, home);
  }, [selectedTeam, knockout, home, fetchRiskMap]);

  useEffect(() => {
    if (selectedTeam && detailRef.current) {
      detailRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [selectedTeam]);

  const handleSelectTeam = (teamName) => {
    navigate(`/team/${encodeURIComponent(teamName)}`);
  };

  const chartData = riskMapData?.intervals.map((interval, index) => ({
    interval,
    probabilidad: +(riskMapData.probabilities[index] * 100).toFixed(1),
    baseline: riskMapData.baseline?.probabilities?.[index] != null
      ? +(riskMapData.baseline.probabilities[index] * 100).toFixed(1)
      : null,
  })) ?? [];

  const selectedTeamLabel = selectedCatalogItem?.label || formatTeamLabel(selectedTeam);

  return (
    <main className="max-w-7xl mx-auto px-6 py-12 space-y-8">
      <section className="grid gap-6 lg:grid-cols-[1.35fr_0.85fr] items-start">
        <div className="space-y-4">
          <div>
            <h1 className="font-display text-4xl md:text-6xl text-content-main tracking-widest mb-3">
              ANALISIS TACTICO
            </h1>
            <p className="max-w-3xl text-content-muted text-sm md:text-base leading-relaxed">
              Selecciona un país por autocompletado o desde la grilla de banderas. Cuando eliges una selección,
              la página despliega de forma conjunta su perfil táctico y su mapa de riesgo.
            </p>
          </div>

          <div className="bg-surface border border-border-subtle rounded-2xl p-5 shadow-sm">
            <CountryAutocomplete
              teams={catalog}
              value={selectedCatalogItem?.label || ''}
              onSelect={handleSelectTeam}
              disabled={statsLoading || catalogLoading}
            />
            <p className="text-xs text-content-muted mt-3">
              Puedes buscar por nombre, usar la grilla de banderas o entrar directamente al país que quieras analizar.
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-brand-dark to-field-green rounded-3xl p-6 text-white shadow-xl">
          <div className="text-xs uppercase tracking-[0.2em] text-white/70 mb-3">Vista guiada</div>
          <div className="text-3xl font-display tracking-wide mb-3">Bandera primero. Detalle después.</div>
          <p className="text-sm text-white/80 leading-relaxed">
            La pantalla principal prioriza la exploración visual por continentes y el autocompletado.
            Los controles tácticos aparecen únicamente cuando ya existe un país seleccionado.
          </p>
        </div>
      </section>

      <SectionCard
        title="Seleccionar por bandera"
        subtitle="Las selecciones están agrupadas por continente y ordenadas alfabéticamente dentro de cada bloque."
      >
        {catalogLoading ? (
          <Loader text="Cargando banderas y continentes..." />
        ) : (
          <CountryFlagsByContinent groups={grouped} onSelectTeam={handleSelectTeam} />
        )}
      </SectionCard>

      {!selectedTeam ? (
        <section className="bg-surface border border-border-subtle rounded-2xl p-8 shadow-sm text-center">
          <h2 className="text-2xl font-semibold text-content-main mb-2">Selecciona un país para continuar</h2>
          <p className="text-content-muted text-sm max-w-2xl mx-auto">
            Al elegir una selección se activa la vista unificada con el perfil táctico y el mapa de riesgo.
          </p>
        </section>
      ) : (
        <div ref={detailRef} className="space-y-8">
          <section className="bg-surface border border-border-subtle rounded-3xl p-6 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="flex items-center gap-4">
                <FlagBadge src={flagUrl} name={selectedTeamLabel} size={52} />
                <div>
                  <h2 className="font-display text-3xl md:text-4xl text-content-main tracking-wide">
                    {selectedTeamLabel}
                  </h2>
                  <div className="text-xs font-medium text-content-muted mt-1">
                    {profile ? `Cluster #${profile.cluster}` : 'Cargando cluster...'}
                    {riskMapData ? ` • ${riskMapData.is_knockout ? 'Eliminatoria' : 'Grupos'}` : ''}
                    {riskMapData ? ` • ${riskMapData.is_home ? 'Local' : 'Visitante'}` : ''}
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate('/team')}
                className="self-start md:self-auto px-4 py-2 rounded-md border border-border-subtle bg-base text-content-main text-sm font-medium hover:bg-surface transition-colors"
              >
                Cambiar país
              </button>
            </div>
          </section>

          <div className="grid gap-8 xl:grid-cols-[1.05fr_0.95fr]">
            <SectionCard
              title="Perfil táctico"
              subtitle="Cluster histórico, equipos similares y métricas ofensivas representativas."
            >
              {statsError && <ErrorBanner message={statsError} />}
              {profileError && <ErrorBanner message={profileError} />}
              {profileLoading && <Loader text="Consultando perfil táctico..." />}

              {profile && !profileLoading && (
                <div className="space-y-6">
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

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <StatCard
                      label="Goles / partido"
                      value={profile.avg_goals_match.toFixed(2)}
                      tooltip="Promedio historico de goles por partido con gol registrado."
                      delta={deltaAvgGoals}
                    />
                    <StatCard
                      label="Tasa penaltis"
                      value={`${(profile.penalty_rate * 100).toFixed(1)}%`}
                      tooltip="Proporción de goles de penalti sobre el total de goles."
                    />
                    <StatCard
                      label="Minuto promedio"
                      value={profile.mean_minute.toFixed(1)}
                      tooltip="Minuto promedio de anotación en los goles del equipo."
                    />
                    <StatCard
                      label="Ratio eliminatoria"
                      value={`${(profile.knockout_ratio * 100).toFixed(1)}%`}
                      tooltip="Proporción de goles anotados en fase eliminatoria."
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
                      {profile.similar_teams.length === 0 ? (
                        <span className="text-content-muted text-sm italic">Sin equipos similares en este cluster</span>
                      ) : (
                        [...profile.similar_teams]
                          .sort((a, b) => a.localeCompare(b))
                          .map((teamName) => <SimilarTeamTag key={teamName} name={teamName} />)
                      )}
                    </div>
                  </div>
                </div>
              )}
            </SectionCard>

            <SectionCard
              title="Mapa de riesgo"
              subtitle="La fase y la localía solo aparecen cuando ya elegiste un país."
            >
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-xs text-content-muted mb-1 font-medium">Tipo de fase</label>
                  <select
                    className="w-full bg-base border border-border-subtle text-content-main p-2 rounded-md focus:outline-none focus:border-brand-primary"
                    value={knockout}
                    onChange={(event) => setKnockout(Number(event.target.value))}
                    disabled={!selectedTeam}
                  >
                    <option value={0}>Fase de grupos</option>
                    <option value={1}>Eliminatoria</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-content-muted mb-1 font-medium">Localía</label>
                  <select
                    className="w-full bg-base border border-border-subtle text-content-main p-2 rounded-md focus:outline-none focus:border-brand-primary"
                    value={home}
                    onChange={(event) => setHome(Number(event.target.value))}
                    disabled={!selectedTeam}
                  >
                    <option value={1}>Local</option>
                    <option value={0}>Visitante</option>
                  </select>
                </div>
              </div>

              <div className="mb-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="px-3 py-2 bg-brand-primary hover:bg-brand-dark text-white text-sm font-medium rounded-md transition-colors disabled:opacity-60"
                  onClick={async () => {
                    try {
                      const { blob, contentType, contentDisposition } = await fetchTeamReport({
                        team: selectedTeam,
                        format: 'pdf',
                        mode: 'heatmap',
                        is_knockout: knockout,
                        is_home: home,
                      });
                      const url = window.URL.createObjectURL(new Blob([blob], { type: contentType }));
                      const anchor = document.createElement('a');
                      anchor.href = url;
                      const filenameMatch = /filename=(?:"?)([^;\"]+)/i.exec(contentDisposition || '');
                      anchor.download = filenameMatch ? filenameMatch[1] : `${selectedTeam}_heatmap.pdf`;
                      document.body.appendChild(anchor);
                      anchor.click();
                      anchor.remove();
                      window.URL.revokeObjectURL(url);
                    } catch (err) {
                      alert(err.message || 'Error al descargar reporte del equipo');
                    }
                  }}
                  disabled={!selectedTeam}
                >
                  Descargar reporte equipo (PDF)
                </button>

                <button
                  type="button"
                  className="px-3 py-2 bg-base border border-border-subtle text-content-main text-sm font-medium rounded-md hover:bg-surface transition-colors disabled:opacity-60"
                  onClick={async () => {
                    try {
                      const { blob, contentType, contentDisposition } = await fetchTeamReport({
                        team: selectedTeam,
                        format: 'csv',
                        mode: 'heatmap',
                        is_knockout: knockout,
                        is_home: home,
                      });
                      const url = window.URL.createObjectURL(new Blob([blob], { type: contentType }));
                      const anchor = document.createElement('a');
                      anchor.href = url;
                      const filenameMatch = /filename=(?:"?)([^;\"]+)/i.exec(contentDisposition || '');
                      anchor.download = filenameMatch ? filenameMatch[1] : `${selectedTeam}_heatmap.csv`;
                      document.body.appendChild(anchor);
                      anchor.click();
                      anchor.remove();
                      window.URL.revokeObjectURL(url);
                    } catch (err) {
                      alert(err.message || 'Error al descargar CSV del equipo');
                    }
                  }}
                  disabled={!selectedTeam}
                >
                  Descargar CSV
                </button>
              </div>

              {riskError && <ErrorBanner message={riskError} />}
              {riskLoading && <Loader text="Calculando mapa de riesgo..." />}

              {riskMapData && !riskLoading && (
                <div>
                  <div className="flex items-center gap-4 mb-6 mt-2">
                    <div>
                      <h3 className="font-display text-2xl text-content-main tracking-wide mb-1">
                        {selectedTeamLabel}
                      </h3>
                      <div className="text-xs font-medium text-content-muted">
                        Cluster #{riskMapData.cluster} &nbsp;•&nbsp; {riskMapData.is_knockout ? 'Eliminatoria' : 'Grupos'} &nbsp;•&nbsp; {riskMapData.is_home ? 'Local' : 'Visitante'}
                      </div>
                    </div>
                  </div>

                  <ResponsiveContainer width="100%" height={320}>
                    <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="interval" tick={{ fill: '#64748b', fontSize: 12 }} />
                      <YAxis
                        domain={[0, 100]}
                        tickFormatter={(v) => `${v}%`}
                        tick={{ fill: '#64748b', fontSize: 12 }}
                      />
                      <ReTooltip
                        formatter={(value, name) => [
                          `${value}%`,
                          name === 'baseline' ? (riskMapData.baseline?.label || 'Promedio') : 'P(gol)',
                        ]}
                        contentStyle={{ background: '#ffffff', border: '1px solid #d8e7dc', borderRadius: 8, boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        labelStyle={{ color: '#1e293b', fontWeight: 600 }}
                      />
                      <Legend
                        iconType="line"
                        formatter={(value) => (
                          <span className="text-content-muted font-medium">
                            {value === 'baseline' ? (riskMapData.baseline?.label || 'Promedio') : 'Equipo'}
                          </span>
                        )}
                      />

                      <Bar dataKey="probabilidad" radius={[6, 6, 2, 2]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={probToColor(entry.probabilidad / 100)} />
                        ))}
                        <LabelList dataKey="probabilidad" position="top" formatter={(value) => `${value}%`} fill="#64748b" fontSize={11} />
                      </Bar>

                      <Line
                        type="monotone"
                        dataKey="baseline"
                        stroke="#0A472E"
                        strokeWidth={2}
                        dot={false}
                        strokeDasharray="4 4"
                      />
                    </ComposedChart>
                  </ResponsiveContainer>

                  <div className="mt-8 grid grid-cols-7 gap-2 text-center">
                    {riskMapData.intervals.map((interval, index) => (
                      <div key={interval} className="bg-base border border-border-subtle rounded-lg p-2 shadow-sm">
                        <div className="text-xs text-content-muted mb-1">{interval}</div>
                        <div className="text-sm font-bold" style={{ color: probToColor(riskMapData.probabilities[index]) }}>
                          {(riskMapData.probabilities[index] * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </SectionCard>
          </div>
        </div>
      )}
    </main>
  );
}
