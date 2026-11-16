import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createGardenLayout,gardenReducer,selectedPlant,copySetup,serializeGarden,deserializeGarden,simulationInput,crops,type GardenLayoutState} from '../src/gardenLayout.ts';

function pepperDraft(state:GardenLayoutState) {
  const draft=copySetup(state.draft);
  draft.input.crop_name='Pepper';
  draft.input.planting_date='2026-05-20';
  draft.input.start_date='2026-05-20';
  draft.input.crop_coefficient=1.25;
  draft.input.soil_mode='manual';
  draft.soil={wp:'10',fc:'28',sat:'46',conductivity:'0.5',depth:'15',water:'29'};
  draft.address='Pepper bed';
  return draft;
}
function plantPepper() {
  let state=createGardenLayout();
  state=gardenReducer(state,{type:'draft',draft:pepperDraft(state)});
  state=gardenReducer(state,{type:'tool',tool:'plant'});
  return gardenReducer(state,{type:'cell',index:0,plantId:'pepper-0'});
}

test('Select loads saved crop and all basic/advanced settings without changing any cell',()=>{
  let state=plantPepper();
  const before=JSON.stringify(state.cells);
  state=gardenReducer(state,{type:'tool',tool:'select'});
  state=gardenReducer(state,{type:'cell',index:28});
  assert.equal(state.draft.input.crop_name,'Tomato');
  state=gardenReducer(state,{type:'cell',index:0});
  assert.deepEqual(state.draft,pepperDraft(createGardenLayout()));
  assert.equal(JSON.stringify(state.cells),before);
  assert.equal(selectedPlant(state)?.id,'pepper-0');
});
test('each new plant snapshots the current form; later edits never change saved siblings',()=>{
  let state=plantPepper();
  const first=JSON.stringify(state.cells[0]);
  const draft=copySetup(state.draft);draft.input.crop_name='Carrot';draft.soil.depth='9';
  state=gardenReducer(state,{type:'draft',draft});
  state=gardenReducer(state,{type:'cell',index:1,plantId:'carrot-1'});
  assert.equal(JSON.stringify(state.cells[0]),first);
  assert.equal(selectedPlant(state)?.setup.input.crop_name,'Carrot');
  assert.equal(selectedPlant(state)?.setup.soil.depth,'9');
  assert.equal(state.cells[0].kind==='plant'&&state.cells[0].plant.setup.soil.depth,'15');
});
test('editing requires explicit Save and updates only the selected plant, preserving its ID',()=>{
  let state=plantPepper();
  state=gardenReducer(state,{type:'tool',tool:'select'});
  const other=JSON.stringify(state.cells[28]);
  const draft=copySetup(state.draft);draft.input.crop_name='Cucumber';draft.soil.depth='20';
  state=gardenReducer(state,{type:'draft',draft});
  assert.equal(selectedPlant(state)?.setup.input.crop_name,'Pepper');
  state=gardenReducer(state,{type:'save'});
  assert.equal(selectedPlant(state)?.setup.input.crop_name,'Cucumber');
  assert.equal(selectedPlant(state)?.setup.soil.depth,'20');
  assert.equal(selectedPlant(state)?.id,'pepper-0');
  assert.equal(JSON.stringify(state.cells[28]),other);
});
test('discard restores the saved setup and selecting an empty/excluded cell never changes it',()=>{
  let state=plantPepper();
  state=gardenReducer(state,{type:'tool',tool:'select'});
  state=gardenReducer(state,{type:'draft',draft:{...state.draft,address:'Unsaved'}});
  state=gardenReducer(state,{type:'revert'});
  assert.equal(state.draft.address,'Pepper bed');
  const before=JSON.stringify(state.cells);
  state=gardenReducer(state,{type:'cell',index:2});
  assert.equal(selectedPlant(state),null);
  state=gardenReducer(state,{type:'cell',index:4});
  assert.equal(JSON.stringify(state.cells),before);
});
test('Plant never replaces occupied or excluded cells; Empty makes either available',()=>{
  let state=plantPepper();
  const before=JSON.stringify(state.cells);
  state=gardenReducer(state,{type:'cell',index:28});
  state=gardenReducer(state,{type:'cell',index:4});
  assert.equal(JSON.stringify(state.cells),before);
  state=gardenReducer(state,{type:'tool',tool:'empty'});
  state=gardenReducer(state,{type:'cell',index:4});
  assert.deepEqual(state.cells[4],{kind:'empty'});
  state=gardenReducer(state,{type:'tool',tool:'plant'});
  state=gardenReducer(state,{type:'cell',index:4,plantId:'pepper-4'});
  assert.equal(selectedPlant(state)?.setup.input.crop_name,'Pepper');
  state=gardenReducer(state,{type:'tool',tool:'exclude'});
  state=gardenReducer(state,{type:'cell',index:4});
  assert.deepEqual(state.cells[4],{kind:'exclude'});
  state=gardenReducer(state,{type:'tool',tool:'empty'});
  state=gardenReducer(state,{type:'cell',index:0});
  assert.deepEqual(state.cells[0],{kind:'empty'});
});
test('saved cells and advanced settings survive refresh; unsaved edits do not',()=>{
  let state=plantPepper();
  state=gardenReducer(state,{type:'draft',draft:{...state.draft,address:'Unsaved address'}});
  const restored=deserializeGarden(serializeGarden(state));
  assert.deepEqual(restored.cells,state.cells);
  assert.equal(restored.selected,0);
  assert.equal(restored.tool,'select');
  assert.equal(restored.draft.address,'Pepper bed');
  assert.deepEqual(restored.draft.soil,pepperDraft(createGardenLayout()).soil);
});
test('invalid settings cannot plant or overwrite a saved plant',()=>{
  let state=plantPepper();
  const before=JSON.stringify(state.cells);
  state=gardenReducer(state,{type:'draft',draft:{...state.draft,soil:{...state.draft.soil,fc:'2'}}});
  state=gardenReducer(state,{type:'cell',index:1});
  assert.equal(JSON.stringify(state.cells),before);
  assert.match(state.notice,/wilting point/);
  state=gardenReducer(state,{type:'tool',tool:'select'});
  state=gardenReducer(state,{type:'save'});
  assert.equal(JSON.stringify(state.cells),before);
});
test('all seven supported crops can be stored independently; corrupt storage recovers safely',()=>{
  let state=createGardenLayout();
  state=gardenReducer(state,{type:'tool',tool:'plant'});
  for(const [index,crop] of crops.entries()) {
    const position=40+index;
    state=gardenReducer(state,{type:'tool',tool:'empty'});
    state=gardenReducer(state,{type:'cell',index:position});
    state=gardenReducer(state,{type:'draft',draft:{...copySetup(state.draft),input:{...state.draft.input,crop_name:crop}}});
    state=gardenReducer(state,{type:'tool',tool:'plant'});
    state=gardenReducer(state,{type:'cell',index:position,plantId:`test-${crop}`});
  }
  const restored=deserializeGarden(serializeGarden(state));
  for(const [index,crop] of crops.entries()) {
    const cell=restored.cells[40+index];
    assert.equal(cell.kind==='plant'&&cell.plant.setup.input.crop_name,crop);
  }
  for(const raw of ['{','null','{}',JSON.stringify({version:1,cells:[],selected:0})]) assert.deepEqual(deserializeGarden(raw),createGardenLayout());
  const bad=JSON.parse(serializeGarden(state));bad.cells[40].plant.setup.input.crop_name='Corn';
  assert.deepEqual(deserializeGarden(JSON.stringify(bad)),createGardenLayout());
});
test('existing Analyze request conversions remain unchanged and omit planner fields',()=>{
  const input=simulationInput(pepperDraft(createGardenLayout()));
  assert.equal(input.crop_name,'Pepper');
  assert.equal(input.wilting_point,.1);
  assert.equal(input.root_depth_cm,38.1);
  assert.equal(input.saturated_hydraulic_conductivity_mm_day,12.7);
  assert.equal(input.initial_water_content,.29);
  assert.equal(input.location_name,'Edison · Pepper bed');
  assert.equal('area' in input,false);assert.equal('cells' in input,false);
});
