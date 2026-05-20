import { useState } from 'react';
import { useTeams } from '../hooks/useTeams';
import { useRiskMap } from '../hooks/useRiskMap';
import TeamSelector from '../components/ui/TeamSelector';
import Loader from '../components/ui/Loader';
import ErrorBanner from '../components/ui/ErrorBanner';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer,
} from 'recharts';

function probToColor(p) {
  const r = Math.round(255 * p);
  const g = Math.round(255 * (1 - p));
  return `rgb(${r},${g},60)`;
}

export default function RiskMap() {
  const { teams, loading: teamsLoading } = useTeams();
  const { data, loading, error, fetchData } = useRiskMap();

  const [team, setTeam] = useState('');
  const [knockout, setKnockout] = useState(0);
  const [home, setHome] = useState(1);

  const handleSubmit = () => {
    if (!team) return;
    fetchData(team, knockout, home);
  };

  const chartData = data?.intervals.map((interval, i) => ({
    interval,
    probabilidad: +(data.probabilities[i] * 100).toFixed(1),
  })) ?? [];

  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="font-display text-5xl text-gold tracking-widest mb-2">MAPA DE RIESGO</h1>
      <p className="text-gray-400 mb-8 text-sm">
        Probabilidad estimada de gol por intervalo de 15 minutos - Modelo Random Forest
      </p>

      <div className="bg-card-bg border border-border-subtle rounded-2xl p-6 mb-8">
        <div className="grid md:grid-cols-3 gap-4 mb-5">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Equipo</label>
            <TeamSelector
              teams={teams}
              value={team}
              onChange={setTeam}
              disabled={teamsLoading}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Fase del torneo</label>
            <select
              value={knockout}
              onChange={(e) => setKnockout(Number(e.target.value))}
              className="w-full bg-dark-bg border border-border-subtle text-white rounded-lg px-4 py-2.5
                         focus:outline-none focus:ring-2 focus:ring-gold"
            >
              <option value={0}>Fase de grupos</option>
              <option value={1}>Eliminatoria</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Condicion</label>
            <select
              value={home}
              onChange={(e) => setHome(Number(e.target.value))}
              className="w-full bg-dark-bg border border-border-subtle text-white rounded-lg px-4 py-2.5
                         focus:outline-none focus:ring-2 focus:ring-gold"
            >
              <option value={1}>Local</option>
              <option value={0}>Visitante</option>
            </select>
          </div>
        </div>
        <button
          onClick={handleSubmit}
          disabled={!team || loading}
          className="bg-gold text-black font-semibold px-8 py-2.5 rounded-lg
                     hover:bg-yellow-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Analizando...' : 'Generar Mapa de Riesgo'}
        </button>
      </div>

      <ErrorBanner message={error} />
      {loading && <Loader text="Ejecutando modelo Random Forest..." />}

      {data && !loading && (
        <div className="bg-card-bg border border-border-subtle rounded-2xl p-6">
          <h2 className="font-display text-3xl text-white tracking-wide mb-1">
            {data.team.replace(/(^\w|\s\w)/g, (m) => m.toUpperCase())}
          </h2>
          <p className="text-xs text-gray-400 mb-6">
            Cluster asignado: <span className="text-gold font-semibold">#{data.cluster}</span>
            &nbsp;-&nbsp;
            {data.is_knockout ? 'Fase eliminatoria' : 'Fase de grupos'}
            &nbsp;-&nbsp;
            {data.is_home ? 'Local' : 'Visitante'}
          </p>

          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
              <XAxis dataKey="interval" tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <YAxis
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
                tick={{ fill: '#9ca3af', fontSize: 12 }}
              />
              <Tooltip
                formatter={(v) => [`${v}%`, 'P(gol)']}
                contentStyle={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8 }}
                labelStyle={{ color: '#f5a623', fontWeight: 600 }}
              />
              <Bar dataKey="probabilidad" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={probToColor(entry.probabilidad / 100)}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-6 grid grid-cols-7 gap-2 text-center">
            {data.intervals.map((interval, i) => (
              <div key={interval} className="bg-dark-bg rounded-lg p-2">
                <div className="text-xs text-gray-400 mb-1">{interval}</div>
                <div
                  className="text-sm font-bold"
                  style={{ color: probToColor(data.probabilities[i]) }}
                >
                  {(data.probabilities[i] * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}
