import {useState} from 'react';
import {IconPlant2,IconPencil,IconChevronDown,IconLoader2,IconMapPin} from '@tabler/icons-react';
import type {SimulationInput} from './contracts';
import {dateLabel,validateInput} from './api';
import {crops,simulationInput,type GardenSetupDraft,type GardenTool} from './gardenLayout';
import {coordinateLabel,type GardenProfile} from './profile';

interface GardenSetupProps {
  onRun:(input:SimulationInput)=>void; busy:boolean; collapsed:boolean; onExpand:()=>void;
  draft:GardenSetupDraft; onChange:(draft:GardenSetupDraft)=>void; tool:GardenTool;
  selectedCrop:string|null; cellLabel:string; dirty:boolean; onSave:()=>string|null; onRevert:()=>void;
  profile:GardenProfile|null; onEditProfile:()=>void;
}
export function GardenSetup({onRun,busy,collapsed,onExpand,draft,onChange,tool,selectedCrop,cellLabel,dirty,onSave,onRevert,profile,onEditProfile}:GardenSetupProps){
  const [advanced,setAdvanced]=useState(false);
  const {area,input,soil}=draft;
  const [error,setError]=useState<{draft:GardenSetupDraft;message:string}|null>(null);
  const setInput=(update:((previous:SimulationInput)=>SimulationInput))=>onChange({...draft,input:update(input)});
  const setArea=(value:string)=>onChange({...draft,area:value});
  const setSoil=(update:((previous:GardenSetupDraft['soil'])=>GardenSetupDraft['soil']))=>onChange({...draft,soil:update(soil)});
  const update=(key:keyof SimulationInput,value:string|number)=>setInput(previous=>({...previous,[key]:value}));
  function submit(event:React.FormEvent){
    event.preventDefault();
    const request=simulationInput(draft);
    const issue=validateInput(request);setError(issue?{draft,message:issue}:null);if(!issue)onRun(request);else if(!Number.isFinite(request.latitude))setAdvanced(true);
  }
  const numberInput=(label:string,key:keyof typeof soil,suffix:string)=> <label className="field" key={key}><span>{label}</span><div className="unit-input"><input type="number" step="any" min="0" required={key!=='water'} value={soil[key]} placeholder={key==='water'?'Field capacity':undefined} onChange={e=>setSoil(previous=>({...previous,[key]:e.target.value}))}/><span>{suffix}</span></div></label>;
  const locationSummary=<div className="saved-garden-location"><IconMapPin size={17}/><div><strong>{profile?.location.label??'Set your garden location'}</strong>{profile&&<small>{coordinateLabel(profile.location.latitude,profile.location.longitude)} · Confirmed</small>}<button type="button" onClick={onEditProfile}>Edit location in profile</button></div></div>;
  if(collapsed)return <section className="setup-collapsed"><h2>Your garden</h2>{locationSummary}<p>{input.crop_name} · {area} ft²</p><button className="outline-button" onClick={onExpand}><IconPencil size={16}/>Edit garden</button></section>;
  return <form className={`garden-setup ${advanced?'advanced':''}`} onSubmit={submit}>
    <h2>Garden setup</h2>
    <div className="plant-editor-context"><strong>{tool==='select'&&selectedCrop?`${cellLabel} · ${selectedCrop}`:tool==='plant'?`Placing ${input.crop_name}`:'Configure a plant'}</strong><span>{tool==='select'&&selectedCrop?(dirty?'Unsaved edits · save to update this cell.':'Saved settings · selecting never changes a plant.'):'Choose settings here, then use Plant on an empty cell.'}</span></div>
    {locationSummary}
    <div className="segmented" aria-label="Setup detail"><button type="button" aria-pressed={!advanced} className={!advanced?'selected':''} onClick={()=>setAdvanced(false)}>Basic</button><button type="button" aria-pressed={advanced} className={advanced?'selected':''} onClick={()=>setAdvanced(true)}>Advanced</button></div>
    {!advanced?<div className="basic-fields">
      <label className="field"><span>Crop</span><div className="select-wrap"><select value={input.crop_name} onChange={e=>update('crop_name',e.target.value)}>{crops.map(c=><option key={c}>{c}</option>)}</select><IconChevronDown size={16}/></div></label>
      <label className="field"><span>Soil mode</span><div className="select-wrap"><select value={input.soil_mode} onChange={e=>{update('soil_mode',e.target.value);if(e.target.value==='manual')setAdvanced(true);}}><option value="auto">Auto</option><option value="manual">Manual</option><option value="ssurgo">SSURGO required</option></select><IconChevronDown size={16}/></div></label>
      <div className="field-pair"><label className="field"><span>Planting date</span><input type="date" required value={input.planting_date} onChange={e=>setInput(previous=>({...previous,planting_date:e.target.value,start_date:e.target.value}))}/></label><label className="field"><span>Garden area</span><div className="unit-input"><input type="number" min="1" step="any" value={area} onChange={e=>setArea(e.target.value)}/><span>ft²</span></div></label></div>
    </div>:<div className="advanced-fields">
      <div className="setup-summary"><span>{input.crop_name} · {area} ft²</span><button type="button" onClick={()=>setAdvanced(false)}><IconPencil size={12}/>Edit basics</button></div>
      <h3>Simulation</h3>
      <label className="field"><span>Planting date</span><input type="date" required value={input.planting_date} onChange={e=>update('planting_date',e.target.value)}/></label>
      <div className="field-pair"><label className="field"><span>Start date</span><input type="date" required value={input.start_date} onChange={e=>update('start_date',e.target.value)}/></label><label className="field"><span>End date</span><input type="date" required value={input.end_date} onChange={e=>update('end_date',e.target.value)}/></label></div>
      <label className="field"><span>Crop coefficient</span><div className="coefficient"><input type="number" step="any" min="0.001" max="2" required value={input.crop_coefficient} onChange={e=>update('crop_coefficient',Number(e.target.value))}/><small>0 &lt; value ≤ 2</small></div></label>
      <h3>Soil settings</h3>
      <div className="segmented compact">{(['auto','manual'] as const).map(mode=><button type="button" key={mode} aria-pressed={input.soil_mode===mode} className={input.soil_mode===mode?'selected':''} onClick={()=>update('soil_mode',mode)}>{mode==='auto'?'Auto':'Manual'}</button>)}</div>
      {input.soil_mode==='manual'?<><div className="field-pair">{numberInput('Wilting point','wp','% vol')}{numberInput('Field capacity','fc','% vol')}</div><div className="field-pair">{numberInput('Saturation','sat','% vol')}{numberInput('Conductivity','conductivity','in/day')}</div><div className="field-pair">{numberInput('Root depth','depth','in')}{numberInput('Initial water','water','% vol')}</div><small className="help">Soil water thresholds use volumetric percentages.</small></>:<p className="help">USDA SSURGO lookup, with clearly labeled fallback assumptions when needed.</p>}
    </div>}
    {error?.draft===draft&&<p className="inline-error" role="alert">{error.message}</p>}
    {tool==='select'&&selectedCrop&&<div className="plant-save-actions"><button type="button" className="outline-button save-plant" disabled={!dirty} onClick={()=>{const issue=onSave();setError(issue?{draft,message:issue}:null);}}>Save plant settings</button>{dirty&&<button type="button" className="plant-revert" onClick={onRevert}>Discard edits</button>}</div>}
    <button type="submit" className="primary-button analyze" disabled={busy}>{busy?<IconLoader2 className="spin" size={21}/>:<IconPlant2 size={22}/>}<span>{busy?'Analyzing garden…':'Analyze garden'}</span></button>
    <small className="setup-note">Analyze runs the form settings; it does not save grid edits.</small>
    {!advanced&&<small className="season-caption">{dateLabel(input.start_date)} – {dateLabel(input.end_date,{month:'short',day:'numeric',year:'numeric'})} · Season view</small>}
  </form>;
}
