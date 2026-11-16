export const PROFILE_STORAGE_KEY = 'gardentwin-profile-v1';
export interface GardenLocation {
  label: string;
  latitude: number;
  longitude: number;
  source: 'photon' | 'map' | 'coordinates';
  confirmedAt: string;
}
export interface GardenProfile {version: 1; name: string; location: GardenLocation}
export function validCoordinates(latitude: unknown, longitude: unknown): boolean {
  return typeof latitude === 'number' && Number.isFinite(latitude) && latitude >= -90 && latitude <= 90 &&
    typeof longitude === 'number' && Number.isFinite(longitude) && longitude >= -180 && longitude <= 180;
}
export function profileIssue(profile: GardenProfile): string | null {
  if (typeof profile.name !== 'string' || !profile.name.trim() || profile.name.trim().length > 60) return 'Enter a name or username of up to 60 characters.';
  const point = profile.location;
  if (!point || typeof point.label !== 'string' || !point.label.trim() || point.label.length > 500 || !validCoordinates(point.latitude, point.longitude)) return 'Choose a garden address or a point on the map.';
  if (!['photon', 'map', 'coordinates'].includes(point.source) || typeof point.confirmedAt !== 'string' || !Number.isFinite(Date.parse(point.confirmedAt))) return 'Confirm your garden location before saving.';
  return null;
}
export function deserializeProfile(raw: string | null): GardenProfile | null {
  try {
    const value = raw ? JSON.parse(raw) : null;
    return value?.version === 1 && profileIssue(value) === null ? {...value,name:value.name.trim()} : null;
  } catch {return null;}
}
export function loadProfile(): GardenProfile | null {
  try {return deserializeProfile(localStorage.getItem(PROFILE_STORAGE_KEY));}
  catch {return null;}
}
export function persistProfile(profile: GardenProfile, storage: Pick<Storage,'setItem'> = localStorage): void {
  const issue = profileIssue(profile);
  if (issue) throw new Error(issue);
  try {storage.setItem(PROFILE_STORAGE_KEY, JSON.stringify({...profile,name:profile.name.trim()}));}
  catch {throw new Error('Your browser could not save this profile. Allow site storage, then try again.');}
}
export function sameLocation(a: Pick<GardenLocation,'latitude'|'longitude'>, b: Pick<GardenLocation,'latitude'|'longitude'>): boolean {
  return Math.abs(a.latitude-b.latitude) < .000001 && Math.abs(a.longitude-b.longitude) < .000001;
}
export function coordinateLabel(latitude: number, longitude: number): string {
  return `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
}
