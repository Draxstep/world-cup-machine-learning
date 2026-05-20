/**
 * TeamSelector - combobox de equipos con busqueda.
 * Props: teams (string[]), value (string), onChange (fn)
 */
export default function TeamSelector({ teams, value, onChange, disabled }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="w-full bg-card-bg border border-border-subtle text-white rounded-lg px-4 py-2.5
                 focus:outline-none focus:ring-2 focus:ring-gold capitalize"
    >
      <option value="">- Selecciona un equipo -</option>
      {teams.map((t) => (
        <option key={t} value={t} className="capitalize">
          {t.replace(/(^\w|\s\w)/g, (m) => m.toUpperCase())}
        </option>
      ))}
    </select>
  );
}
