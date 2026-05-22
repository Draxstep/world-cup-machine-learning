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
      className="w-full bg-base border border-border-subtle text-content-main p-2 rounded-md focus:outline-none focus:border-brand-primary capitalize"
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
