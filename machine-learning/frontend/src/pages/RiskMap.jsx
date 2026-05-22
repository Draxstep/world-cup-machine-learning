import { useState } from 'react';
import { useTeams } from '../hooks/useTeams';
import { useRiskMap } from '../hooks/useRiskMap';
import TeamSelector from '../components/ui/TeamSelector';
import Loader from '../components/ui/Loader';
import ErrorBanner from '../components/ui/ErrorBanner';
import { useFlag } from '../hooks/useFlag';
import FlagBadge from '../components/ui/FlagBadge';
import { fetchTeamReport } from '../api/client';
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer, Legend, LabelList
} from 'recharts';

function probToColor(p) {
  const start = [20, 68, 48];
  const end = [185, 223, 122];
  const r = Math.round(start[0] + (end[0] - start[0]) * p);
  const g = Math.round(start[1] + (end[1] - start[1]) * p);
  const b = Math.round(start[2] + (end[2] - start[2]) * p);
  return `rgb(${r},${g},${b})`;
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

  const baseline = data?.baseline?.probabilities ?? [];
  const chartData = data?.intervals.map((interval, i) => ({
    interval,
    probabilidad: +(data.probabilities[i] * 100).toFixed(1),
    baseline: baseline[i] ? +(baseline[i] * 100).toFixed(1) : null,
  })) ?? [];

  const flagUrl = useFlag(data?.team || team, true);

  return (
    <main className="max-w-4xl mx-auto px-6 py-12">
      
      <div className="mb-4 text-sm text-content-muted">
        {data?.matches_played ? `Basado en ${data.matches_played} partidos con gol` : ''}
      </div>

      <div className="bg-surface border border-border-subtle rounded-2xl p-6 mb-8 shadow-sm">
        <div className="grid md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs text-content-muted mb-1 font-medium">Equipo</label>
            <TeamSelector
              teams={teams}
              value={team}
              onChange={setTeam}
              disabled={teamsLoading}
            />
          </div>

          <div>
            <label className="block text-xs text-content-muted mb-1 font-medium">Tipo de fase</label>
            <select
              className="w-full bg-base border border-border-subtle text-content-main p-2 rounded-md focus:outline-none focus:border-brand-primary"
              value={knockout}
              onChange={(e) => setKnockout(Number(e.target.value))}
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
              onChange={(e) => setHome(Number(e.target.value))}
            >
              <option value={1}>Local</option>
              <option value={0}>Visitante</option>
            </select>
          </div>
        </div>

        <div className="mb-6">
          <button
            className="w-full py-2 bg-brand-primary text-white font-medium rounded-md hover:bg-brand-dark transition-colors"
            onClick={handleSubmit}
            disabled={loading || teamsLoading}
          >
            {loading ? 'Analizando...' : 'Generar Mapa de Riesgo'}
          </button>
        </div>

        {data && (
          <div className="mb-4 flex gap-2">
            <button
              className="px-3 py-2 bg-brand-primary hover:bg-brand-dark text-white text-sm font-medium rounded-md transition-colors"
              onClick={async () => {
                try {
                  const { blob, contentType, contentDisposition } = await fetchTeamReport({ team: data.team, format: 'pdf', mode: 'heatmap', is_knockout: data.is_knockout ? 1 : 0, is_home: data.is_home ? 1 : 0 });
                  const url = window.URL.createObjectURL(new Blob([blob], { type: contentType }));
                  const a = document.createElement('a');
                  a.href = url;
                  const filenameMatch = /filename=(?:"?)([^;\"]+)/i.exec(contentDisposition || '')
                  a.download = filenameMatch ? filenameMatch[1] : `${data.team}_heatmap.pdf`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  window.URL.revokeObjectURL(url);
                } catch (err) {
                  alert(err.message || 'Error al descargar reporte del equipo');
                }
              }}
            >Descargar reporte equipo (PDF)</button>

            <button
              className="px-3 py-2 bg-base border border-border-subtle text-content-main text-sm font-medium rounded-md hover:bg-surface transition-colors"
              onClick={async () => {
                try {
                  const { blob, contentType, contentDisposition } = await fetchTeamReport({ team: data.team, format: 'csv', mode: 'heatmap', is_knockout: data.is_knockout ? 1 : 0, is_home: data.is_home ? 1 : 0 });
                  const url = window.URL.createObjectURL(new Blob([blob], { type: contentType }));
                  const a = document.createElement('a');
                  a.href = url;
                  const filenameMatch = /filename=(?:"?)([^;\"]+)/i.exec(contentDisposition || '')
                  a.download = filenameMatch ? filenameMatch[1] : `${data.team}_heatmap.csv`;
                  document.body.appendChild(a);
                  a.click();
                  a.remove();
                  window.URL.revokeObjectURL(url);
                } catch (err) {
                  alert(err.message || 'Error al descargar CSV del equipo');
                }
              }}
            >Descargar CSV</button>
          </div>
        )}

        <ErrorBanner message={error} />

        {data && (
          <div>
            <div className="flex items-center gap-4 mb-6 mt-4">
              <FlagBadge src={flagUrl} name={data.team} size={40} />
              <div>
                <h2 className="font-display text-3xl text-content-main tracking-wide mb-1">
                  {data.team.replace(/(^\w|\s\w)/g, (m) => m.toUpperCase())}
                </h2>
                <div className="text-xs font-medium text-content-muted">
                  Cluster #{data.cluster} &nbsp;•&nbsp; {data.is_knockout ? 'Eliminatoria' : 'Grupos'} &nbsp;•&nbsp; {data.is_home ? 'Local' : 'Visitante'}
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
                <Tooltip
                  formatter={(v, name) => [ `${v}%`, name === 'baseline' ? (data.baseline?.label || 'Promedio') : 'P(gol)' ]}
                  contentStyle={{ background: '#ffffff', border: '1px solid #d8e7dc', borderRadius: 8, boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  labelStyle={{ color: '#1e293b', fontWeight: 600 }}
                />
                <Legend iconType="line" formatter={(value) => <span className="text-content-muted font-medium">{value === 'baseline' ? (data.baseline?.label || 'Promedio') : 'Equipo'}</span>} />

                <Bar dataKey="probabilidad" radius={[6, 6, 2, 2]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={probToColor(entry.probabilidad / 100)} />
                  ))}
                  <LabelList dataKey="probabilidad" position="top" formatter={(v) => `${v}%`} fill="#64748b" fontSize={11} />
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
              {data.intervals.map((interval, i) => (
                <div key={interval} className="bg-base border border-border-subtle rounded-lg p-2 shadow-sm">
                  <div className="text-xs text-content-muted mb-1">{interval}</div>
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
      </div>
    </main>
  );
}