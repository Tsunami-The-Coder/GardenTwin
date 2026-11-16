import {test} from 'node:test';
import assert from 'node:assert/strict';
import {api,format,biomassPercent,validateInput,ApiError} from '../src/api.ts';
import type {SimulationInput} from '../src/contracts.ts';
const input:SimulationInput={location_name:'Edison garden',latitude:40.5187,longitude:-74.4121,crop_name:'Tomato',planting_date:'2026-05-15',start_date:'2026-05-15',end_date:'2026-08-31',crop_coefficient:1,soil_mode:'auto'};
test('missing values stay unavailable and real zero remains zero',()=>{assert.equal(format(null),'Unavailable');assert.equal(format(undefined),'Unavailable');assert.equal(format(0),'0');assert.equal(format(NaN),'Unavailable');});
test('date, coordinate, and coefficient boundaries match the backend',()=>{assert.equal(validateInput(input),null);assert.match(validateInput({...input,crop_coefficient:0})??'',/greater than 0/);assert.match(validateInput({...input,latitude:91})??'',/latitude/);assert.match(validateInput({...input,planting_date:'2026-06-01'})??'',/Planting date/);assert.equal(validateInput({...input,planting_date:'2024-01-01',start_date:'2024-01-01',end_date:'2024-12-31'}),null);assert.match(validateInput({...input,planting_date:'2024-01-01',start_date:'2024-01-01',end_date:'2025-01-01'})??'',/366/);});
test('manual soil rejects impossible relationships and below-wilting initial state',()=>{const manual={...input,soil_mode:'manual' as const,wilting_point:.12,field_capacity:.30,saturation:.45,root_depth_cm:30,saturated_hydraulic_conductivity_mm_day:10};assert.equal(validateInput(manual),null);assert.match(validateInput({...manual,field_capacity:.5})??'',/Soil values/);assert.match(validateInput({...manual,initial_water_content:.05})??'',/Initial water/);});
test('comparison percentages require nonzero known baseline',()=>{assert.equal(biomassPercent(null,5),null);assert.equal(biomassPercent(0,5),null);assert.equal(biomassPercent(100,110),10);});
test('API uses POST only for creating a run; secondary routes use GET and preserve JSON errors',async()=>{
  const original=globalThis.fetch;
  const calls:{url:string;init:RequestInit|undefined}[]=[];
  globalThis.fetch=async(url,init)=>{calls.push({url:String(url),init});return new Response(JSON.stringify({run_id:'abc'}),{status:200});};
  try{await api.run(input);await api.compare('a/b');await api.forecast('abc');await api.analyze('abc');assert.equal(calls[0].url,'/api/simulation/run');assert.equal(calls[0].init?.method,'POST');assert.deepEqual(JSON.parse(String(calls[0].init?.body)),input);assert.equal(calls[1].url,'/api/simulation/a%2Fb/intervention/irrigation');assert.equal(calls[1].init?.method,undefined);assert.equal(calls[1].init?.body,undefined);assert.equal(calls[2].url,'/api/simulation/abc/forecast');assert.equal(calls[3].url,'/api/ai/analyze/abc');globalThis.fetch=async()=>new Response(JSON.stringify({detail:'Simulation not found.'}),{status:404});await assert.rejects(api.retrieve('gone'),e=>e instanceof ApiError&&e.status===404&&e.message==='Simulation not found.');}
  finally{globalThis.fetch=original;}
});
