/** Verified against GardenTwin main @77ad9da. Backend is read-only. */
export type Status = 'apply' | 'none' | 'unknown';
export type Nullable = number | null;
export interface Weather {
  date: string; source: string;
  temperature_mean_c: Nullable; temperature_min_c: Nullable; temperature_max_c: Nullable;
  precipitation_mm: Nullable; relative_humidity_pct: Nullable;
  solar_radiation_mj_m2_day: Nullable; wind_speed_2m_m_s: Nullable;
  precipitation_probability_max_pct?: Nullable;
}
export interface DailyRecord {
  date: string; weather: Weather;
  soil_water: {root_zone_water_mm: Nullable; field_capacity_mm: Nullable; wilting_point_mm: Nullable; root_depth_cm: Nullable; water_stress_index: Nullable};
  nutrients: {nitrogen_available_kg_ha: Nullable; phosphorus_available_kg_ha: Nullable; potassium_available_kg_ha: Nullable; nutrient_stress_index: Nullable; soil_test_available: boolean};
  crop: {crop_name: string; growth_stage: string; days_after_planting: number; accumulated_gdd: number; height_cm: Nullable; biomass_kg_ha: Nullable; estimated_yield_kg_ha: Nullable; health_index: Nullable};
  irrigation: {status: Status; amount_mm: Nullable; liters_per_plant: Nullable; reason: string; confidence: Nullable};
  fertilizer: {status: Status; nitrogen_kg_ha: Nullable; phosphorus_kg_ha: Nullable; potassium_kg_ha: Nullable; estimated_daily_n_demand_kg_ha: Nullable; estimated_daily_p_demand_kg_ha: Nullable; estimated_daily_k_demand_kg_ha: Nullable; product_name: string | null; product_amount_g_per_plant: Nullable; reason: string; confidence: Nullable};
  alerts: string[];
}
export interface Run {
  run_id: string; site: {site_id: string; location_name: string; latitude: number; longitude: number};
  crop_name: string; planting_date: string; start_date: string; end_date: string; records: DailyRecord[];
  soil_data_source: string; soil_map_unit_key: string | null; soil_map_unit_name: string | null;
  soil_component_name: string | null; soil_lookup_note: string | null;
  soil_properties: Record<string, number>; simulation_parameters: Record<string, number>;
}
export interface SimulationInput {
  location_name: string; latitude: number; longitude: number; crop_name: string;
  planting_date: string; start_date: string; end_date: string;
  crop_coefficient: number; soil_mode: 'auto' | 'manual' | 'ssurgo';
  wilting_point?: number; field_capacity?: number; saturation?: number;
  saturated_hydraulic_conductivity_mm_day?: number; root_depth_cm?: number; initial_water_content?: number;
}
export interface ScenarioSummary {
  days_simulated: number; total_irrigation_mm: number; mean_water_stress: Nullable;
  maximum_water_stress: Nullable; days_with_water_stress: number;
  final_crop_health_index: Nullable; final_biomass_kg_ha: Nullable;
}
export interface Comparison {
  run_id: string; method: string; baseline: ScenarioSummary; intervention: ScenarioSummary;
  difference: {mean_water_stress_reduction: Nullable; final_biomass_change_kg_ha: Nullable}; limitations: string[];
}
export interface Forecast {
  run_id: string; provider: string; forecast_days: number; simulation_continuation_available: boolean;
  continuation_note: string; weather: Weather[]; simulation_records: DailyRecord[];
}
export interface ModelStatus {
  id: string; name: string; category: string; role: string; status: string;
  configured_variables: string[]; inference_artifact_present: boolean; notes: string;
}
export interface AIStatus {models: ModelStatus[]; total: number; configuration_present: number; inference_artifacts_present: number; operational: number; important_note: string}
export interface AIAnalysis {run_id: string; location: string; crop: string; analysis_type: string; systems: Record<string, Record<string, unknown>>; artifact_errors: Record<string, string>; limitations: string[]}
