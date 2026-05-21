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
      className="w-full bg-white p-2.5 rounded-md text-slate-900 border border-border-subtle focus:outline-none focus:ring-2 focus:ring-field-green capitalize"
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
