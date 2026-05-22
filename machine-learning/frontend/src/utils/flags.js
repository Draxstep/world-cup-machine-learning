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
const metadataCache = new Map();
let countryCatalogPromise = null;
const countryCatalogCacheKey = 'world-cup-country-catalog-v1';
const countryCatalogCacheTtlMs = 1000 * 60 * 60 * 24 * 30;

function getStorage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function readCachedCatalog() {
  const storage = getStorage();
  if (!storage) return null;

  try {
    const raw = storage.getItem(countryCatalogCacheKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.cachedAt || !Array.isArray(parsed?.entries)) return null;
    if (Date.now() - parsed.cachedAt > countryCatalogCacheTtlMs) return null;
    return new Map(parsed.entries);
  } catch {
    return null;
  }
}

function writeCachedCatalog(index) {
  const storage = getStorage();
  if (!storage) return;

  try {
    storage.setItem(
      countryCatalogCacheKey,
      JSON.stringify({ cachedAt: Date.now(), entries: Array.from(index.entries()) })
    );
  } catch {
    // ignore cache quota errors
  }
}

function normalizeTeamName(name) {
  return String(name || '').trim().toLowerCase();
}

function getContinentLabel(region, subregion) {
  if (region === 'Africa') return 'Africa';
  if (region === 'Asia') return 'Asia';
  if (region === 'Europe') return 'Europa';
  if (region === 'Oceania') return 'Oceania';
  if (region !== 'Americas') return 'Otros';

  const sub = String(subregion || '').toLowerCase();
  if (sub.includes('south')) return 'Sudamerica';
  if (sub.includes('north')) return 'Norteamerica';
  if (sub.includes('central')) return 'Centroamerica';
  if (sub.includes('caribbean')) return 'Caribe';
  return 'America';
}

function buildCountryIndex(entries = []) {
  const index = new Map();

  const addKey = (key, value) => {
    const normalized = normalizeTeamName(key);
    if (normalized && !index.has(normalized)) {
      index.set(normalized, value);
    }
  };

  entries.forEach((entry) => {
    const value = {
      flagUrl: entry?.flags?.png || entry?.flags?.svg || null,
      continent: getContinentLabel(entry?.region, entry?.subregion),
    };

    addKey(entry?.name?.common, value);
    addKey(entry?.name?.official, value);
    addKey(entry?.cca2, value);
    addKey(entry?.cca3, value);
    (entry?.altSpellings || []).forEach((alias) => addKey(alias, value));
  });

  return index;
}

async function getCountryCatalog() {
  if (!countryCatalogPromise) {
    const cached = readCachedCatalog();
    if (cached) {
      countryCatalogPromise = Promise.resolve(cached);
      return countryCatalogPromise;
    }

    countryCatalogPromise = fetch(
      'https://restcountries.com/v3.1/all?fields=name,region,subregion,flags,cca2,cca3,altSpellings'
    )
      .then((res) => {
        if (!res.ok) throw new Error('country catalog fetch failed');
        return res.json();
      })
      .then((data) => {
        const index = buildCountryIndex(Array.isArray(data) ? data : []);
        writeCachedCatalog(index);
        return index;
      })
      .catch(() => new Map());
  }

  return countryCatalogPromise;
}

function resolveAlias(name) {
  const key = normalizeTeamName(name);
  return aliases[key] || name;
}

export async function getTeamMetadata(teamName, useApi = true) {
  const key = normalizeTeamName(teamName);
  if (metadataCache.has(key)) {
    return metadataCache.get(key);
  }

  const fallback = {
    flagUrl: fallbackFlags[key] || null,
    continent: null,
  };

  const catalog = await getCountryCatalog();
  const query = resolveAlias(teamName);
  const catalogEntry = catalog.get(normalizeTeamName(query)) || catalog.get(key);

  const metadata = {
    flagUrl: fallback.flagUrl || catalogEntry?.flagUrl || null,
    continent: catalogEntry?.continent || null,
  };

  if (!useApi && !fallback.flagUrl) {
    metadata.flagUrl = null;
  }

  metadataCache.set(key, metadata);
  return metadata;
}

export async function getFlagUrl(teamName, useApi = true) {
  const key = normalizeTeamName(teamName);
  if (flagCache.has(key)) {
    return flagCache.get(key);
  }

  const metadata = await getTeamMetadata(teamName, useApi);
  flagCache.set(key, metadata.flagUrl);
  return metadata.flagUrl;
}
