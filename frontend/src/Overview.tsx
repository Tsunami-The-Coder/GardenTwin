import {useEffect,useRef,useState} from 'react';
import {IconPlant2,IconDroplet,IconPaperBag,IconCloud,IconChevronRight,IconSquare,IconTexture,IconCalendar,IconChevronLeft,IconPointer} from '@tabler/icons-react';
import type {DailyRecord,Run} from './contracts';
import {dateLabel,dateObject,format,stageLabel} from './api';
import {CropIcon,plantAssets} from './CropIcon';
import {selectedPlant,type CropName,type GardenLayoutState,type GardenTool,type GardenPlant} from './gardenLayout';
export const tabs=['Overview','Plant Growth','Soil & Water','Nutrients','Environment'] as const;
export type Tab=typeof tabs[number];
export function watering(record:DailyRecord){return record.irrigation.status==='apply'?'Water recommended':record.irrigation.status==='none'?'No irrigation needed':'Watering unavailable';}
export function fertilizer(record:DailyRecord){return record.fertilizer.status==='unknown'?'Needs soil test':record.fertilizer.status==='apply'?'Review fertilizer guidance':'No fertilizer indicated';}
const moduleIcons=[IconPlant2,IconDroplet,IconPaperBag,IconCloud];

const toolDescriptions:Record<GardenTool,string>={select:'Inspect a cell without changing it.',plant:'Place the Garden Setup crop and settings in an empty cell.',empty:'Remove a plant and keep the cell available.',exclude:'Mark a cell as outside the usable garden.'};
export function GardenGrid({layout,onTool,onCell,storageWarning}:{layout:GardenLayoutState;onTool:(tool:GardenTool)=>void;onCell:(index:number)=>void;storageWarning:string}){
  const {cells,selected,tool,draft}=layout;
  const plant=selectedPlant(layout);
  const tools=[{key:'select',label:'Select',Icon:IconPointer},{key:'plant',label:'Plant',Icon:IconPlant2},{key:'empty',label:'Empty',Icon:IconSquare},{key:'exclude',label:'Exclude',Icon:IconTexture}] as const;
  return <aside className="garden-layout"><h2>Your garden layout</h2><p>Each planted cell keeps its own settings.</p>
    <div className="segmented grid-tools" role="group" aria-label="Garden tools">{tools.map(({key,label,Icon})=><button type="button" key={key} className={tool===key?'selected':''} aria-pressed={tool===key} title={toolDescriptions[key]} onClick={()=>onTool(key)}><Icon size={17}/>{label}</button>)}</div>
    <p className="grid-tool-help" id="garden-tool-help">{tool==='plant'?<><CropIcon crop={draft.input.crop_name as CropName}/>Planting <strong>{draft.input.crop_name}</strong> · from Garden Setup</>:toolDescriptions[tool]}</p>
    <div className={`garden-grid tool-${tool}`} aria-label="Garden layout editor" aria-describedby="garden-tool-help">{cells.map((cell,i)=><button key={i} className={`garden-cell ${cell.kind} ${selected===i?'chosen':''}`} aria-label={`Row ${Math.floor(i/8)+1}, column ${i%8+1}: ${cell.kind==='plant'?cell.plant.setup.input.crop_name+' plant':cell.kind==='exclude'?'excluded':'empty'}`} aria-pressed={selected===i} title={cell.kind==='plant'?`${cell.plant.setup.input.crop_name} · planted ${cell.plant.setup.input.planting_date}`:cell.kind==='exclude'?'Excluded from garden':'Available for planting'} onClick={()=>onCell(i)}>{cell.kind==='plant'&&<CropIcon crop={cell.plant.setup.input.crop_name as CropName}/ >}{cell.kind==='exclude'&&<IconTexture size={30} stroke={.6}/>}</button>)}</div>
    <div className="grid-legend"><span><IconPlant2 size={20}/>Planted</span><span><IconSquare size={20}/>Empty</span><span><IconTexture size={20}/>Excluded</span></div>
    <div className="selected-plant">{plant?<CropIcon crop={plant.setup.input.crop_name as CropName}/>:<IconSquare size={24}/>}<span>{plant?`Selected plant · ${plant.setup.input.crop_name}`:cells[selected].kind==='exclude'?'Selected cell · Excluded':'Selected cell · Empty'}</span></div>
    {plant&&<dl className="selected-plant-details"><div><dt>Cell</dt><dd>Row {Math.floor(selected/8)+1}, column {selected%8+1}</dd></div><div><dt>Planted</dt><dd>{dateLabel(plant.setup.input.planting_date,{month:'short',day:'numeric',year:'numeric'})}</dd></div><div><dt>Soil</dt><dd>{plant.setup.input.soil_mode==='ssurgo'?'SSURGO required':plant.setup.input.soil_mode==='manual'?'Manual':'Auto'}</dd></div></dl>}
    <p className="grid-feedback" role="status" aria-live="polite">{layout.notice||(tool==='select'&&plant?'Saved settings are shown in Garden Setup.':'Choose a tool to shape your garden.')}</p>
    <small className="grid-note">{storageWarning||'Layout saved in this browser. Simulation data remains separate.'}</small>
  </aside>;
}

export function BotanicalSpecimen({record,onTab,plant}:{record:DailyRecord;onTab:(tab:Tab)=>void;plant:GardenPlant|null}){
  const crop=plant?.setup.input.crop_name as CropName|undefined;
  const asset=crop?plantAssets[crop]:undefined;
  const matchingSimulation=crop===record.crop.crop_name;
  const host=useRef<HTMLDivElement>(null);
  const canvas=useRef<HTMLCanvasElement>(null);
  const values=[`${stageLabel(record.crop.growth_stage)} · Day ${record.crop.days_after_planting}`,`${watering(record)} · ${format(record.irrigation.amount_mm)} mm`,fertilizer(record),`${format(record.weather.temperature_mean_c,0)}°C · Rain ${format(record.weather.precipitation_mm,0)} mm`];
  const moduleTabs:Tab[]=['Plant Growth','Soil & Water','Nutrients','Environment'];
  useEffect(()=>{
    const parent=host.current,element=canvas.current;if(!parent||!element)return;
    const draw=()=>{
      const box=parent.getBoundingClientRect(),ctx=element.getContext('2d');if(!ctx)return;
      const dpr=Math.max(1,window.devicePixelRatio||1);element.width=box.width*dpr;element.height=box.height*dpr;ctx.scale(dpr,dpr);ctx.clearRect(0,0,box.width,box.height);
      if(box.width<420)return;
      ctx.strokeStyle='#71872c';ctx.fillStyle='#71872c';ctx.lineWidth=1.7;ctx.lineJoin='round';
      parent.querySelectorAll<HTMLButtonElement>('.specimen-callout').forEach((node,i)=>{
        const r=node.getBoundingClientRect();const left=i<2;
        const startX=left?r.left-box.left:r.right-box.left,startY=r.bottom-box.top;
        const stemX=box.width*([.46,.44,.56,.59][i]),stemY=box.height*([.26,.60,.36,.79][i]);
        const edgeX=left?r.right-box.left-18:r.left-box.left+18;
        ctx.beginPath();ctx.moveTo(startX,startY);ctx.lineTo(edgeX,startY);ctx.lineTo(left?edgeX+22:edgeX-22,startY-16);ctx.lineTo(stemX+(left?-30:30),startY-16);ctx.lineTo(stemX,stemY);ctx.stroke();
        ctx.beginPath();ctx.arc(stemX,stemY,5.8,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#faf7f0';ctx.lineWidth=1.5;ctx.stroke();ctx.strokeStyle='#71872c';ctx.lineWidth=1.7;
      });
    };
    const observer=new ResizeObserver(draw);observer.observe(parent);draw();return()=>observer.disconnect();
  },[record]);
  return <div className="botanical-specimen" ref={host}><img className="sage-arcs" src="/garden/arcs-opaque.png" alt=""/>{asset?<img className="specimen-image" src={asset} alt={`Illustrative ${crop} plant`}/>:<div className="plant-asset-placeholder">{crop?<><CropIcon crop={crop}/><h3>{crop}</h3><p>Plant image coming later.</p></>:<><IconPlant2 size={52} stroke={1}/><h3>Select a plant</h3><p>Choose a planted cell to view it here.</p></>}</div>}<div className="layout-specimen-caption">{crop?`Viewing ${crop} · saved layout plant`:'No plant in the selected cell'}</div><canvas className="callout-lines" ref={canvas} aria-hidden="true"/>{moduleTabs.map((tab,i)=>{const Icon=moduleIcons[i];return <button className={`specimen-callout callout-${i}`} key={tab} title="Open current simulation results; layout cells are saved separately." onClick={()=>onTab(tab)}><Icon className="callout-icon" size={38} stroke={1.35}/><span><strong>{tab}</strong><small>{matchingSimulation?values[i]:'Open current simulation'}</small></span><IconChevronRight className="callout-arrow" size={20}/></button>;})}</div>;
}

export function Calendar({run,selectedDate,onSelect}:{run:Run;selectedDate:string;onSelect:(date:string)=>void}){
  const index=Math.max(0,run.records.findIndex(r=>r.date===selectedDate));
  const [offset,setOffset]=useState(()=>Math.max(0,index));
  useEffect(()=>{if(index<offset||index>offset+6)setOffset(Math.min(index,Math.max(0,run.records.length-7)));},[index,offset,run.records.length]);
  const week=run.records.slice(offset,offset+7);
  function shift(direction:number){const next=Math.max(0,Math.min(run.records.length-7,offset+direction*7));setOffset(next);onSelect(run.records[next].date);}
  return <section className="care-calendar"><div className="calendar-heading"><IconCalendar size={32} stroke={1.7}/><div><h2>Botanical Care Calendar</h2><p>{dateLabel(week[0]?.date||selectedDate)} – {dateLabel(week.at(-1)?.date||selectedDate,{month:'short',day:'numeric',year:'numeric'})} · Season view</p></div></div><div className="calendar-week"><button className="round-button" aria-label="Previous seven days" disabled={offset===0} onClick={()=>shift(-1)}><IconChevronLeft size={17}/></button>{week.map(r=><button key={r.date} className={`calendar-day ${r.date===selectedDate?'selected':''}`} aria-label={dateLabel(r.date,{weekday:'long',month:'long',day:'numeric'})} aria-pressed={r.date===selectedDate} onClick={()=>onSelect(r.date)}><small>{dateObject(r.date).toLocaleDateString('en-US',{weekday:'short'})}</small><span>{dateObject(r.date).getDate()}</span></button>)}<button className="round-button" aria-label="Next seven days" disabled={offset+7>=run.records.length} onClick={()=>shift(1)}><IconChevronRight size={17}/></button></div></section>;
}

export function CareSchedule({record,onTab}:{record:DailyRecord;onTab:(tab:Tab)=>void}){
  return <section className="care-schedule"><div className="schedule-heading"><IconCalendar size={31} stroke={1.6}/><h2>Daily Care Schedule</h2><span className="date-pill">{dateLabel(record.date,{weekday:'long',month:'long',day:'numeric'})}</span></div><div className="care-rows"><div className="care-row"><span className="care-icon"><IconDroplet size={40} stroke={1.3}/></span><div className="care-explanation"><h3>Watering</h3><p>{record.irrigation.reason}</p></div><button className="care-result" onClick={()=>onTab('Soil & Water')}>{watering(record)} · {format(record.irrigation.amount_mm)} mm<IconChevronRight size={19}/></button></div><div className="care-row fertilizer-row"><span className="care-icon"><IconPaperBag size={38} stroke={1.3}/></span><div className="care-explanation"><h3>Fertilization</h3><p>{record.nutrients.soil_test_available?record.fertilizer.reason:'Nutrient availability unknown. Run a soil test to determine fertilizer needs.'}</p></div><div className="fertilizer-result"><strong>{fertilizer(record)}</strong><button className="text-button" onClick={()=>onTab('Nutrients')}>View reasoning<IconChevronRight size={18}/></button></div></div></div></section>;
}
