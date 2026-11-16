import {test} from 'node:test';
import assert from 'node:assert/strict';
import {deserializeProfile,persistProfile,profileIssue,validCoordinates,sameLocation,type GardenProfile} from '../src/profile.ts';
import {parseLocations,searchLocations} from '../src/locationSearch.ts';
import {createGardenLayout,gardenReducer,selectedPlant,serializeGarden,deserializeGarden,simulationInput} from '../src/gardenLayout.ts';

const profile:GardenProfile={version:1,name:'Garden preview',location:{label:'Public garden, New Jersey',latitude:40.47,longitude:-74.43,source:'photon',confirmedAt:'2026-11-15T20:00:00Z'}};
test('profile round-trips a confirmed location, trims the name, and rejects incomplete/corrupt storage',()=>{
  assert.deepEqual(deserializeProfile(JSON.stringify(profile)),profile);
  assert.equal(deserializeProfile(JSON.stringify({...profile,name:'  Garden preview  '}))?.name,'Garden preview');
  for(const raw of [null,'{','null','{}',JSON.stringify({...profile,version:2}),JSON.stringify({...profile,name:' '}),JSON.stringify({...profile,location:{...profile.location,confirmedAt:''}}),JSON.stringify({...profile,location:{...profile.location,source:'invented'}})]) assert.equal(deserializeProfile(raw),null);
});
test('a profile requires real numeric coordinates in range, including valid zero coordinates',()=>{
  assert.equal(validCoordinates(0,0),true);
  assert.equal(validCoordinates(-90,180),true);
  for(const [lat,lon] of [[91,0],[0,-181],[NaN,0],[null,0],['40',-74],[0,Infinity]]) assert.equal(validCoordinates(lat,lon),false);
  assert.match(profileIssue({...profile,location:{...profile.location,latitude:91}})??'',/Choose a garden/);
});
test('storage failures do not report a successful persistent profile',()=>{
  let stored='';
  persistProfile(profile,{setItem:(_key,value)=>{stored=value;}});
  assert.deepEqual(deserializeProfile(stored),profile);
  assert.throws(()=>persistProfile(profile,{setItem:()=>{throw new Error('quota');}}),/could not save/);
  assert.throws(()=>persistProfile({...profile,name:''},{setItem:()=>assert.fail('invalid profile must not be saved')}),/Enter a name/);
});
test('address parsing follows GeoJSON longitude/latitude order and never accepts an invalid result',()=>{
  const results=parseLocations({features:[{geometry:{type:'Point',coordinates:[-74.43,40.47]},properties:{name:'Public garden',housenumber:'1',street:'Garden Lane',city:'New Brunswick',state:'New Jersey',postcode:8901,country:'United States'}},{geometry:{type:'Point',coordinates:[200,40]},properties:{name:'Invalid'}},{geometry:{type:'Point',coordinates:[null,null]},properties:{name:'Missing'}},{geometry:{type:'Polygon',coordinates:[]},properties:{name:'Not a point'}}]});
  assert.equal(results.length,1);
  assert.equal(results[0].latitude,40.47);assert.equal(results[0].longitude,-74.43);
  assert.match(results[0].label,/1 Garden Lane/);assert.equal(results[0].source,'photon');
  for(const value of [null,{},'bad',{features:'not an array'}]) assert.deepEqual(parseLocations(value),[]);
});
test('address search encodes the query, bounds results, supports cancellation and surfaces HTTP failures',async()=>{
  const original=globalThis.fetch;
  const controller=new AbortController();
  globalThis.fetch=async(url,init)=>{
    const parsed=new URL(String(url));
    assert.equal(parsed.origin,'https://photon.komoot.io');
    assert.equal(parsed.searchParams.get('q'),'A & B Garden, NJ');assert.equal(parsed.searchParams.get('limit'),'5');
    assert.equal(init?.signal,controller.signal);assert.equal(init?.credentials,'omit');
    return new Response(JSON.stringify({features:[]}));
  };
  try {
    assert.deepEqual(await searchLocations(' A & B Garden, NJ ',controller.signal),[]);
    globalThis.fetch=async()=>new Response('{}',{status:429});
    await assert.rejects(searchLocations('Garden',controller.signal),/unavailable/);
    await assert.rejects(searchLocations('a',controller.signal),/at least three/);
  } finally {globalThis.fetch=original;}
});
test('changing the shared profile location preserves every plant crop, ID, soil and dates',()=>{
  let state=createGardenLayout();
  const before=state.cells;
  state=gardenReducer(state,{type:'location',location:profile.location});
  for(const [i,cell] of state.cells.entries()) {
    const old=before[i];
    if(cell.kind==='plant'&&old.kind==='plant') {
      assert.equal(cell.plant.id,old.plant.id);
      assert.deepEqual(cell.plant.setup.soil,old.plant.setup.soil);
      assert.equal(cell.plant.setup.input.crop_name,old.plant.setup.input.crop_name);
      assert.equal(cell.plant.setup.input.planting_date,old.plant.setup.input.planting_date);
      assert.equal(cell.plant.setup.input.latitude,profile.location.latitude);
    } else assert.deepEqual(cell,old);
  }
  assert.equal(before[28].kind==='plant'&&before[28].plant.setup.input.latitude,40.5187);
  state=deserializeGarden(serializeGarden(state));
  state=gardenReducer(state,{type:'cell',index:9});
  const input=simulationInput(state.draft);
  assert.equal(selectedPlant(state)?.setup.input.longitude,profile.location.longitude);
  assert.equal(input.location_name,profile.location.label);
  assert.equal(input.latitude,profile.location.latitude);assert.equal(input.longitude,profile.location.longitude);
  assert.equal('name' in input,false);assert.equal('confirmedAt' in input,false);
});
test('location changes can be recognized without changing an existing simulation site',()=>{
  const site={latitude:40.5187,longitude:-74.4121};
  assert.equal(sameLocation(profile.location,site),false);
  assert.equal(sameLocation(profile.location,{...profile.location}),true);
  assert.deepEqual(site,{latitude:40.5187,longitude:-74.4121});
});
