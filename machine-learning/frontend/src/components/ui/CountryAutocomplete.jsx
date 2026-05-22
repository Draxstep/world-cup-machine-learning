import { useEffect, useMemo, useState } from 'react';

export default function CountryAutocomplete({ teams = [], value, onSelect, placeholder = 'Buscar un país...', disabled }) {
  const [query, setQuery] = useState(value || '');
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setQuery(value || '');
  }, [value]);

  const normalizedQuery = query.trim().toLowerCase();
  const options = useMemo(() => {
    if (!normalizedQuery) {
      return teams.slice(0, 10);
    }

    return teams
      .filter((team) => team.label.toLowerCase().includes(normalizedQuery))
      .slice(0, 10);
  }, [teams, normalizedQuery]);

  const handleSelect = (team) => {
    onSelect(team.team);
    setQuery(team.label);
    setOpen(false);
  };

  return (
    <div className="relative z-30">
      <label className="block text-xs text-content-muted mb-1.5 font-medium">Seleccionar equipo</label>
      <input
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          window.setTimeout(() => setOpen(false), 120);
        }}
        disabled={disabled}
        placeholder={placeholder}
        className="w-full bg-white border border-border-subtle text-content-main px-3 py-2.5 rounded-md focus:outline-none focus:border-brand-primary shadow-sm"
      />

      {open && !disabled && options.length > 0 && (
        <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-xl border border-border-subtle bg-white shadow-2xl ring-1 ring-black/5">
          {options.map((team) => (
            <button
              key={team.team}
              type="button"
              className="flex w-full items-center justify-between px-4 py-3 text-left text-sm text-content-main hover:bg-field-green/10 transition-colors"
              onMouseDown={(event) => {
                event.preventDefault();
                handleSelect(team);
              }}
            >
              <span className="font-medium">{team.label}</span>
              <span className="text-xs text-content-muted uppercase tracking-wide">{team.continent || 'Otros'}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
