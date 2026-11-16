import type {Run, SimulationInput, Comparison, Forecast, AIAnalysis, AIStatus} from './contracts';

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 120_000);
  try {
    const response = await fetch(`/api${path}`, { ...init, signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...init?.headers } });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = body?.detail;
      const message = typeof detail === 'string' ? detail : Array.isArray(detail)
        ? detail.map((issue: {loc?: string[]; msg: string}) => `${issue.loc?.slice(1).join('.')}: ${issue.msg}`).join('; ')
        : 'The local GardenTwin backend is unavailable. Start it on port 8000, then try again.';
      throw new ApiError(message, response.status);
    }
    if (body === null) throw new ApiError('The backend returned an unreadable response.', response.status);
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error && error.name === 'AbortError') throw new Error('The request took too long. Please try again.');
    throw new Error('Could not connect to the local GardenTwin backend on port 8000.');
  } finally { clearTimeout(timer); }
}

export const api = {
  run: (input: SimulationInput) => request<Run>('/simulation/run', {method:'POST', body:JSON.stringify(input)}),
  retrieve: (id: string) => request<Run>(`/simulation/${encodeURIComponent(id)}`),
  compare: (id: string) => request<Comparison>(`/simulation/${encodeURIComponent(id)}/intervention/irrigation`),
  forecast: (id: string) => request<Forecast>(`/simulation/${encodeURIComponent(id)}/forecast`),
  status: () => request<AIStatus>('/ai/status'),
  analyze: (id: string) => request<AIAnalysis>(`/ai/analyze/${encodeURIComponent(id)}`),
};

export function validateInput(value: SimulationInput): string | null {
  if (!value.location_name.trim()) return 'Add a garden name or location.';
  if (!Number.isFinite(value.latitude) || value.latitude < -90 || value.latitude > 90 || !Number.isFinite(value.longitude) || value.longitude < -180 || value.longitude > 180) return 'Enter valid latitude and longitude in Advanced settings.';
  if (!value.planting_date || !value.start_date || !value.end_date || value.planting_date > value.start_date || value.start_date > value.end_date) return 'Planting date must be on or before the start date, and the end date must follow the start date.';
  if ((Date.parse(value.end_date) - Date.parse(value.start_date)) / 86400000 > 365) return 'Choose a simulation of 366 days or fewer.';
  if (!(value.crop_coefficient > 0 && value.crop_coefficient <= 2)) return 'Crop coefficient must be greater than 0 and at most 2.';
  if (value.soil_mode === 'manual') {
    const {wilting_point:wp,field_capacity:fc,saturation:sat,initial_water_content:water,root_depth_cm:root,saturated_hydraulic_conductivity_mm_day:conductivity} = value;
    if (wp == null || fc == null || sat == null || !(0 <= wp && wp < fc && fc < sat)) return 'Soil values must satisfy wilting point < field capacity < saturation.';
    if (water != null && (water < wp || water > sat)) return 'Initial water must be between wilting point and saturation for this model.';
    if (root == null || root <= 0 || conductivity == null || conductivity < 0) return 'Root depth must be positive and conductivity cannot be negative.';
  }
  return null;
}

export const format = (value: number | null | undefined, digits = 1) => value == null || !Number.isFinite(value) ? 'Unavailable' : value.toLocaleString('en-US', {maximumFractionDigits:digits});
export const stageLabel = (stage: string) => stage.replaceAll('_',' ').replace(/^./, s=>s.toUpperCase());
export const dateObject = (iso: string) => new Date(`${iso}T12:00:00`);
export const dateLabel = (iso: string, options: Intl.DateTimeFormatOptions = {month:'short',day:'numeric'}) => dateObject(iso).toLocaleDateString('en-US',options);
export const biomassPercent = (base: number | null, changed: number | null) => base == null || changed == null || base <= 0 ? null : (changed-base) / base * 100;
