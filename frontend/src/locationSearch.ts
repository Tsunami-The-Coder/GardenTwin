import {validCoordinates,type GardenLocation} from './profile';

export type LocationChoice = Omit<GardenLocation,'confirmedAt'>;
// Public Photon demo: deliberate searches only, bounded results, no autocomplete polling.
export const PHOTON_URL = 'https://photon.komoot.io/api/';
export function parseLocations(body: unknown): LocationChoice[] {
  if (!body || typeof body !== 'object' || !('features' in body) || !Array.isArray(body.features)) return [];
  return body.features.slice(0,5).flatMap((feature: unknown) => {
    if (!feature || typeof feature !== 'object') return [];
    const value = feature as {geometry?: {type?:string;coordinates?:unknown[]};properties?:Record<string,unknown>};
    const [longitude,latitude] = value.geometry?.coordinates ?? [];
    if (value.geometry?.type !== 'Point' || !validCoordinates(latitude,longitude)) return [];
    const p = value.properties ?? {};
    const text = (key:string) => typeof p[key] === 'string' || typeof p[key] === 'number' ? String(p[key]).trim() : '';
    const street = [text('housenumber'),text('street')].filter(Boolean).join(' ');
    const parts = [text('name'),street,text('city') || text('town') || text('village') || text('district'),text('state'),text('postcode'),text('country')];
    const label = [...new Set(parts.filter(Boolean))].join(', ').slice(0,500);
    return label ? [{label,latitude:latitude as number,longitude:longitude as number,source:'photon' as const}] : [];
  });
}
export async function searchLocations(query: string, signal: AbortSignal): Promise<LocationChoice[]> {
  if (query.trim().length < 3) throw new Error('Enter at least three characters to search.');
  const url = new URL(PHOTON_URL);
  url.searchParams.set('q',query.trim());
  url.searchParams.set('limit','5');
  url.searchParams.set('lang','en');
  const response = await fetch(url,{signal,headers:{Accept:'application/json'},credentials:'omit'});
  if (!response.ok) throw new Error('Address search is unavailable. Try again or choose a point on the map.');
  return parseLocations(await response.json());
}
