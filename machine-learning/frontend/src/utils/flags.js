const fallbackFlags = {
  argentina: 'https://flagcdn.com/w40/ar.png',
  brazil: 'https://flagcdn.com/w40/br.png',
  chile: 'https://flagcdn.com/w40/cl.png',
  colombia: 'https://flagcdn.com/w40/co.png',
  croatia: 'https://flagcdn.com/w40/hr.png',
  ecuador: 'https://flagcdn.com/w40/ec.png',
  england: 'https://flagcdn.com/w40/gb.png',
  france: 'https://flagcdn.com/w40/fr.png',
  germany: 'https://flagcdn.com/w40/de.png',
  italy: 'https://flagcdn.com/w40/it.png',
  japan: 'https://flagcdn.com/w40/jp.png',
  mexico: 'https://flagcdn.com/w40/mx.png',
  netherlands: 'https://flagcdn.com/w40/nl.png',
  portugal: 'https://flagcdn.com/w40/pt.png',
  spain: 'https://flagcdn.com/w40/es.png',
  uruguay: 'https://flagcdn.com/w40/uy.png',
  usa: 'https://flagcdn.com/w40/us.png',
  'united states': 'https://flagcdn.com/w40/us.png',
  'south korea': 'https://flagcdn.com/w40/kr.png',
  'north korea': 'https://flagcdn.com/w40/kp.png',
  'czech republic': 'https://flagcdn.com/w40/cz.png',
  'cote d\'ivoire': 'https://flagcdn.com/w40/ci.png',
  'ivory coast': 'https://flagcdn.com/w40/ci.png',
  'west germany': 'https://flagcdn.com/w40/de.png',
  'east germany': 'https://flagcdn.com/w40/de.png',
  'soviet union': 'https://flagcdn.com/w40/ru.png',
  yugoslavia: 'https://flagcdn.com/w40/rs.png',
  'serbia and montenegro': 'https://flagcdn.com/w40/rs.png',
};

const aliases = {
  england: 'United Kingdom',
  scotland: 'United Kingdom',
  wales: 'United Kingdom',
  'northern ireland': 'United Kingdom',
  'united states': 'United States',
  usa: 'United States',
  'south korea': 'Korea (Republic of)',
  'north korea': "Korea (Democratic People's Republic of)",
  'ivory coast': "Cote d'Ivoire",
  'cote d\'ivoire': "Cote d'Ivoire",
  'czech republic': 'Czechia',
  'west germany': 'Germany',
  'east germany': 'Germany',
  'soviet union': 'Russia',
  yugoslavia: 'Serbia',
  'serbia and montenegro': 'Serbia',
};

const flagCache = new Map();

function normalizeTeamName(name) {
  return String(name || '').trim().toLowerCase();
}

export async function getFlagUrl(teamName, useApi = true) {
  const key = normalizeTeamName(teamName);
  if (flagCache.has(key)) {
    return flagCache.get(key);
  }

  if (fallbackFlags[key]) {
    flagCache.set(key, fallbackFlags[key]);
    return fallbackFlags[key];
  }

  if (!useApi) {
    flagCache.set(key, null);
    return null;
  }

  const query = aliases[key] || teamName;
  try {
    const res = await fetch(
      `https://restcountries.com/v3.1/name/${encodeURIComponent(query)}?fields=flags,name`
    );
    if (!res.ok) throw new Error('flag fetch failed');
    const data = await res.json();
    const url = data?.[0]?.flags?.png || data?.[0]?.flags?.svg || null;
    flagCache.set(key, url);
    return url;
  } catch (err) {
    flagCache.set(key, null);
    return null;
  }
}
