import { useState } from 'react';
import { useTeams } from '../hooks/useTeams';
import { fetchTeamProfile } from '../api/client';
import TeamSelector from '../components/ui/TeamSelector';
import Loader from '../components/ui/Loader';
import ErrorBanner from '../components/ui/ErrorBanner';

function StatCard({ label, value }) {
  return (
    <div className="bg-dark-bg rounded-xl p-4 text-center">
      <div className="text-2xl font-bold text-gold">{value}</div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}

export default function TeamProfile() {
  const { teams, loading: teamsLoading } = useTeams();
  const [team, setTeam] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
      <h1 className="font-display text-5xl text-gold tracking-widest mb-2">PERFIL TACTICO</h1>
      <p className="text-gray-400 mb-8 text-sm">
        Cluster historico K-Means y equipos con perfil ofensivo similar
      </p>

      <div className="bg-card-bg border border-border-subtle rounded-2xl p-6 mb-8 flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-xs text-gray-400 mb-1.5">Equipo</label>
          <TeamSelector teams={teams} value={team} onChange={setTeam} disabled={teamsLoading} />
        </div>
        <button
          onClick={handleFetch}
          disabled={!team || loading}
          className="bg-gold text-black font-semibold px-8 py-2.5 rounded-lg
                     hover:bg-yellow-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Cargando...' : 'Ver Perfil'}
        </button>
      </div>

      <ErrorBanner message={error} />
      {loading && <Loader text="Consultando perfil tactico..." />}

      {data && !loading && (
        <div className="bg-card-bg border border-border-subtle rounded-2xl p-6 space-y-6">
          <div>
            <h2 className="font-display text-3xl text-white tracking-wide">
              {data.team.replace(/(^\w|\s\w)/g, (m) => m.toUpperCase())}
            </h2>
            <span className="inline-block mt-2 bg-gold/20 text-gold text-xs font-semibold
                             px-3 py-1 rounded-full border border-gold/30">
              Cluster #{data.cluster}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="Goles / partido" value={data.avg_goals_match.toFixed(2)} />
            <StatCard label="Tasa penaltis" value={`${(data.penalty_rate * 100).toFixed(1)}%`} />
            <StatCard label="Minuto promedio" value={data.mean_minute.toFixed(1)} />
            <StatCard label="Ratio eliminatoria" value={`${(data.knockout_ratio * 100).toFixed(1)}%`} />
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-3">
              Equipos historicos similares (mismo cluster)
            </h3>
            <div className="flex flex-wrap gap-2">
              {data.similar_teams.length === 0 ? (
                <span className="text-gray-500 text-sm">Sin equipos similares en este cluster</span>
              ) : (
                data.similar_teams.map((t) => (
                  <span
                    key={t}
                    className="bg-dark-bg border border-border-subtle text-gray-300 text-xs
                               px-3 py-1.5 rounded-full capitalize"
                  >
                    {t.replace(/(^\w|\s\w)/g, (m) => m.toUpperCase())}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
