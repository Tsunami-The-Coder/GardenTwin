import type {SimulationInput} from './contracts';
import {validateInput} from './api';
import type {GardenLocation} from './profile';

export const crops = ['Tomato', 'Pepper', 'Cucumber', 'Lettuce', 'Carrot', 'Bean', 'Strawberry'] as const;
export type CropName = typeof crops[number];
export type GardenTool = 'select' | 'plant' | 'empty' | 'exclude';
export interface GardenSetupDraft {
  town: string;
  address: string;
  area: string;
  input: SimulationInput;
  soil: {wp: string; fc: string; sat: string; conductivity: string; depth: string; water: string};
}
export interface GardenPlant {id: string; setup: GardenSetupDraft}
export type GardenCell = {kind: 'empty' | 'exclude'} | {kind: 'plant'; plant: GardenPlant};
export interface GardenLayoutState {
  cells: GardenCell[];
  selected: number;
  tool: GardenTool;
  draft: GardenSetupDraft;
  notice: string;
}
export const GARDEN_STORAGE_KEY = 'gardentwin-layout-v1';
export const initialInput: SimulationInput = {location_name:'Edison · Oak Tree Road',latitude:40.5187,longitude:-74.4121,crop_name:'Tomato',planting_date:'2026-05-15',start_date:'2026-05-15',end_date:'2026-08-31',crop_coefficient:1,soil_mode:'auto'};
export function defaultSetup(): GardenSetupDraft {
  return {town:'Edison',address:'Oak Tree Road',area:'108',input:{...initialInput},soil:{wp:'12',fc:'30',sat:'45',conductivity:'0.39',depth:'12',water:'30'}};
}
export function copySetup(setup: GardenSetupDraft): GardenSetupDraft {
  return {...setup,input:{...setup.input},soil:{...setup.soil}};
}
export function setupAtLocation(setup: GardenSetupDraft, location: GardenLocation): GardenSetupDraft {
  return {...copySetup(setup),town:'',address:location.label,input:{...setup.input,location_name:location.label,latitude:location.latitude,longitude:location.longitude}};
}
export function simulationInput(setup: GardenSetupDraft): SimulationInput {
  const {input,town,address,soil} = setup;
  const request: SimulationInput = {...input,location_name:[town,address].filter(Boolean).join(' · ')};
  if (input.soil_mode === 'manual') Object.assign(request, {
    wilting_point:Number(soil.wp)/100,field_capacity:Number(soil.fc)/100,saturation:Number(soil.sat)/100,
    saturated_hydraulic_conductivity_mm_day:Number(soil.conductivity)*25.4,root_depth_cm:Number(soil.depth)*2.54,
    ...(soil.water.trim() ? {initial_water_content:Number(soil.water)/100} : {}),
  });
  return request;
}
export function setupIssue(setup: GardenSetupDraft): string | null {
  if (!crops.includes(setup.input.crop_name as CropName)) return 'Choose a supported crop.';
  if (!Number.isFinite(Number(setup.area)) || Number(setup.area) < 1) return 'Garden area must be at least 1 ft².';
  if (setup.input.soil_mode === 'manual') {
    for (const [key,value] of Object.entries(setup.soil)) {
      if (key === 'water' && !value.trim()) continue;
      if (!value.trim() || !Number.isFinite(Number(value))) return 'Enter valid numbers for the manual soil settings.';
    }
  }
  return validateInput(simulationInput(setup));
}
export function selectedPlant(state: GardenLayoutState): GardenPlant | null {
  const cell = state.cells[state.selected];
  return cell?.kind === 'plant' ? cell.plant : null;
}
export function setupChanged(a: GardenSetupDraft, b: GardenSetupDraft): boolean {
  return JSON.stringify(a) !== JSON.stringify(b);
}
export function createGardenLayout(): GardenLayoutState {
  const cells: GardenCell[] = Array.from({length:56},(_,i) =>
    [9,19,28,32,43,54].includes(i) ? {kind:'plant',plant:{id:`initial-${i}`,setup:defaultSetup()}} :
    {kind:[4,5,6,7,14,15,23].includes(i) ? 'exclude' : 'empty'});
  return {cells,selected:28,tool:'select',draft:defaultSetup(),notice:''};
}
export type GardenAction =
  | {type:'tool'; tool:GardenTool}
  | {type:'draft'; draft:GardenSetupDraft}
  | {type:'cell'; index:number; plantId?:string}
  | {type:'save'}
  | {type:'revert'}
  | {type:'location'; location:GardenLocation};

export function gardenReducer(state: GardenLayoutState, action: GardenAction): GardenLayoutState {
  if (action.type === 'location') return {...state,draft:setupAtLocation(state.draft,action.location),cells:state.cells.map(cell=>cell.kind==='plant'?{...cell,plant:{...cell.plant,setup:setupAtLocation(cell.plant.setup,action.location)}}:cell)};
  if (action.type === 'tool') return {...state,tool:action.tool,notice:''};
  if (action.type === 'draft') return {...state,draft:action.draft,notice:''};
  if (action.type === 'revert') {
    const plant = selectedPlant(state);
    return plant ? {...state,draft:copySetup(plant.setup),notice:'Saved plant settings restored.'} : state;
  }
  if (action.type === 'save') {
    const plant = selectedPlant(state);
    if (!plant || state.tool !== 'select') return state;
    const issue = setupIssue(state.draft);
    if (issue) return {...state,notice:issue};
    return {...state,cells:state.cells.map((cell,i) => i === state.selected ? {kind:'plant',plant:{id:plant.id,setup:copySetup(state.draft)}} : cell),notice:`${state.draft.input.crop_name} settings saved for this cell.`};
  }
  const cell = state.cells[action.index];
  if (!cell) return state;
  if (state.tool === 'select') return {...state,selected:action.index,draft:cell.kind === 'plant' ? copySetup(cell.plant.setup) : state.draft,notice:cell.kind === 'plant' ? `${cell.plant.setup.input.crop_name} selected. Edit settings, then save explicitly.` : cell.kind === 'exclude' ? 'Excluded cell selected. Use Empty to make it available.' : 'Empty cell selected. Configure Garden Setup, then use Plant.'};
  if (state.tool === 'plant') {
    if (cell.kind !== 'empty') return {...state,notice:cell.kind === 'plant' ? 'This cell already has a plant. Use Select to edit it, or Empty before replanting.' : 'This cell is excluded. Use Empty to make it available before planting.'};
    const issue = setupIssue(state.draft);
    if (issue) return {...state,notice:issue};
    return {...state,selected:action.index,cells:state.cells.map((item,i) => i === action.index ? {kind:'plant',plant:{id:action.plantId ?? `plant-${action.index}`,setup:copySetup(state.draft)}} : item),notice:`${state.draft.input.crop_name} planted. Its settings are saved in this cell.`};
  }
  return {...state,selected:action.index,cells:state.cells.map((item,i) => i === action.index ? {kind:state.tool === 'empty' ? 'empty' : 'exclude'} : item),notice:state.tool === 'empty' ? 'Cell emptied and available for planting.' : 'Cell excluded from the usable garden.'};
}

// Store the layout only. Unsaved form edits are never promoted into saved plants.
export function serializeGarden(state: GardenLayoutState): string {
  return JSON.stringify({version:1,cells:state.cells,selected:state.selected});
}
function validSetup(value: unknown): value is GardenSetupDraft {
  if (!value || typeof value !== 'object') return false;
  const s = value as GardenSetupDraft;
  if (typeof s.town !== 'string' || typeof s.address !== 'string' || typeof s.area !== 'string' || !s.input || !s.soil) return false;
  if (!['location_name','crop_name','planting_date','start_date','end_date'].every(key => typeof s.input[key as keyof SimulationInput] === 'string')) return false;
  if (!['latitude','longitude','crop_coefficient'].every(key => typeof s.input[key as keyof SimulationInput] === 'number')) return false;
  if (!['auto','manual','ssurgo'].includes(s.input.soil_mode)) return false;
  if (!['wp','fc','sat','conductivity','depth','water'].every(key => typeof s.soil[key as keyof typeof s.soil] === 'string')) return false;
  return setupIssue(s) === null;
}
export function deserializeGarden(raw: string | null): GardenLayoutState {
  if (!raw) return createGardenLayout();
  try {
    const saved = JSON.parse(raw);
    if (saved.version !== 1 || !Array.isArray(saved.cells) || saved.cells.length !== 56 || !Number.isInteger(saved.selected) || saved.selected < 0 || saved.selected >= 56) return createGardenLayout();
    const ids = new Set<string>();
    for (const cell of saved.cells) {
      if (!cell || !['plant','empty','exclude'].includes(cell.kind)) return createGardenLayout();
      if (cell.kind === 'plant') {
        if (!cell.plant || typeof cell.plant.id !== 'string' || ids.has(cell.plant.id) || !validSetup(cell.plant.setup)) return createGardenLayout();
        ids.add(cell.plant.id);
      }
    }
    const state: GardenLayoutState = {cells:saved.cells,selected:saved.selected,tool:'select',draft:defaultSetup(),notice:''};
    const plant = selectedPlant(state);
    if (plant) state.draft = copySetup(plant.setup);
    return state;
  } catch {return createGardenLayout();}
}
export function loadGarden(): GardenLayoutState {
  try {return deserializeGarden(localStorage.getItem(GARDEN_STORAGE_KEY));}
  catch {return createGardenLayout();}
}
