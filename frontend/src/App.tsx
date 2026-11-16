import {lazy,Suspense,useCallback,useEffect,useReducer,useState} from 'react';
import {AnimatePresence,motion,MotionConfig} from 'motion/react';
import {IconBell,IconUserCircle,IconX,IconDownload,IconSettings,IconPlant2,IconDroplet,IconPaperBag,IconCloud,IconHome,IconArrowLeft,IconAlertTriangle,IconMapPin} from '@tabler/icons-react';
import type {Run,SimulationInput} from './contracts';
import {api,ApiError,dateLabel,format} from './api';
import {GardenSetup} from './GardenSetup';
import {ProfileDialog} from './ProfileDialog';
import {loadProfile,persistProfile,sameLocation,type GardenProfile} from './profile';
import {gardenReducer,loadGarden,serializeGarden,GARDEN_STORAGE_KEY,selectedPlant,setupChanged,setupIssue,type GardenTool} from './gardenLayout';
import {BotanicalSpecimen,Calendar,CareSchedule,GardenGrid,tabs,type Tab} from './Overview';
const Growth=lazy(()=>import('./Details').then(m=>({default:m.Growth})));
const Water=lazy(()=>import('./Details').then(m=>({default:m.Water})));
const Nutrients=lazy(()=>import('./Details').then(m=>({default:m.Nutrients})));
const Environment=lazy(()=>import('./Details').then(m=>({default:m.Environment})));
import example from './data/example-run.json';
const exampleRun=example as Run;
const navIcons=[IconHome,IconPlant2,IconDroplet,IconPaperBag,IconCloud];

export function App(){
  const [profile,setProfile]=useState(loadProfile);
  const [editingProfile,setEditingProfile]=useState(false);
  const profileOpen=!profile||editingProfile;
  const [layout,dispatchLayout]=useReducer(gardenReducer,profile,savedProfile=>{const saved=loadGarden();return savedProfile?gardenReducer(saved,{type:'location',location:savedProfile.location}):saved;});
  const [storageWarning,setStorageWarning]=useState('');
  const plant=selectedPlant(layout);
  useEffect(()=>{
    try{localStorage.setItem(GARDEN_STORAGE_KEY,serializeGarden(layout));setStorageWarning('');}
    catch{setStorageWarning('Browser storage is unavailable. This layout will last only for this visit.');}
  },[layout.cells,layout.selected]);
  const [run,setRun]=useState<Run>(exampleRun);
  const [isExample,setIsExample]=useState(true);
  const [tab,setTab]=useState<Tab>('Overview');
  const [selectedDate,setSelectedDate]=useState('2026-06-28');
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const [collapsed,setCollapsed]=useState(false);
  const [popup,setPopup]=useState<'alerts'|'settings'|null>(null);
  const [savedId,setSavedId]=useState(()=>{try{return localStorage.getItem('gardentwin-run-id');}catch{return null;}});
  const record=run.records.find(r=>r.date===selectedDate)??run.records[0];
  const selectDate=useCallback((date:string)=>setSelectedDate(date),[]);
  function openProfile(){setEditingProfile(true);setPopup(null);}
  function saveProfile(next:GardenProfile){
    try{persistProfile(next);}catch(e){return e instanceof Error?e.message:'Could not save your profile.';}
    dispatchLayout({type:'location',location:next.location});setProfile(next);setEditingProfile(false);setPopup(null);setCollapsed(false);return null;
  }
  function selectTool(tool:GardenTool){dispatchLayout({type:'tool',tool});setCollapsed(false);}
  function useCell(index:number){dispatchLayout({type:'cell',index,plantId:crypto.randomUUID()});setCollapsed(false);}
  function savePlant(){const issue=setupIssue(layout.draft);if(!issue)dispatchLayout({type:'save'});return issue;}
  function changeTab(next:Tab){setTab(next);setPopup(null);window.scrollTo({top:0,behavior:'instant'});}
  function acceptRun(next:Run){
    if(!next.run_id||!Array.isArray(next.records)||!next.records.length)throw new Error('The backend returned no simulation records.');
    setRun(next);setSelectedDate(next.records[0].date);setIsExample(false);setCollapsed(true);setTab('Overview');setSavedId(next.run_id);
    try{localStorage.setItem('gardentwin-run-id',next.run_id);}catch{/* Private browsing can disable storage. */}
  }
  async function analyze(input:SimulationInput){if(!profile){openProfile();return;}input={...input,location_name:profile.location.label,latitude:profile.location.latitude,longitude:profile.location.longitude};setBusy(true);setError('');try{acceptRun(await api.run(input));}catch(e){setError(e instanceof Error?e.message:'Simulation failed.');}finally{setBusy(false);}}
  async function restore(){if(!savedId)return;setBusy(true);setError('');setPopup(null);try{acceptRun(await api.retrieve(savedId));}catch(e){if(e instanceof ApiError&&e.status===404){setError('This run is no longer available. The backend stores runs in memory; create a new simulation after a restart.');setSavedId(null);try{localStorage.removeItem('gardentwin-run-id');}catch{/* Storage is optional. */}}else setError(e instanceof Error?e.message:'Could not restore run.');}finally{setBusy(false);}}
  function resetExample(){setRun(exampleRun);setSelectedDate('2026-06-28');setIsExample(true);setCollapsed(false);setError('');setPopup(null);setTab('Overview');}
  function download(){const url=URL.createObjectURL(new Blob([JSON.stringify(run,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`gardentwin-${run.run_id}.json`;a.click();URL.revokeObjectURL(url);setPopup(null);}
  const descriptions:Record<Tab,string>={'Overview':'Your garden, at a glance.','Plant Growth':'Explore the story of your growing season.','Soil & Water':'Understand the water your garden needs.','Nutrients':'Thoughtful guidance starts with better evidence.','Environment':'The conditions around your garden.'};
  const title=<div className="page-title"><h1>{tab}<span aria-hidden="true"/></h1><p>{descriptions[tab]}</p></div>;
  return <MotionConfig reducedMotion="user"><div className="garden-app" inert={profileOpen} aria-hidden={profileOpen?true:undefined}>
    <a className="skip-link" href="#main">Skip to garden</a>
    <header className="site-header"><button className="brand" aria-label="GardenTwin overview" onClick={()=>changeTab('Overview')}><img src="/garden/wordmark.png" alt="GardenTwin"/></button><nav className="desktop-nav" aria-label="Main navigation">{tabs.map(item=><button key={item} className={item===tab?'active':''} aria-current={item===tab?'page':undefined} onClick={()=>changeTab(item)}>{item}</button>)}</nav><div className="header-actions"><button className="notification-button" aria-label="View simulation alerts" aria-expanded={popup==='alerts'} onClick={()=>setPopup(v=>v==='alerts'?null:'alerts')}><IconBell size={21} stroke={1.5}/></button><button className="profile-button" aria-label="Garden settings" aria-expanded={popup==='settings'} onClick={()=>setPopup(v=>v==='settings'?null:'settings')}><IconUserCircle size={36} stroke={1.4}/><span>{profile?.name??'Your profile'}<small>Settings</small></span></button></div>
    {popup&&<div className="header-popover"><div className="popover-heading"><h3>{popup==='alerts'?'Simulation alerts':'Garden settings'}</h3><button className="icon-button" aria-label="Close panel" onClick={()=>setPopup(null)}><IconX size={18}/></button></div>{popup==='alerts'?<><p className="help">{dateLabel(record.date,{month:'long',day:'numeric',year:'numeric'})} · selected simulation day</p>{record.alerts.length?record.alerts.map((alert,i)=><p className="alert-message" key={i}><IconAlertTriangle size={17}/>{alert}</p>):<p>No alerts for this simulation day.</p>}</>:<><button className="popover-item" onClick={openProfile}><IconUserCircle size={18}/>Edit profile &amp; location</button><button className="popover-item" onClick={()=>{setCollapsed(false);changeTab('Overview');}}><IconSettings size={18}/>Edit garden setup</button><button className="popover-item" onClick={download}><IconDownload size={18}/>Download simulation JSON</button>{savedId&&<button className="popover-item" onClick={restore}><IconArrowLeft size={18}/>Restore last backend run</button>}<button className="popover-item" onClick={resetExample}><IconPlant2 size={18}/>Explore example garden</button><p className="help">Runs are stored temporarily by the local backend. The garden grid is a visual planner.</p></>}</div>}
    </header>
    <main id="main">
      {profile&&!isExample&&!sameLocation(profile.location,run.site)&&<div className="profile-location-notice" role="status"><IconMapPin size={18}/><span>Your saved garden location differs from this simulation. Results still belong to {run.site.location_name}. Analyze garden to use the saved location.</span></div>}
      {error&&<div className="error-banner" role="alert"><IconAlertTriangle size={20}/><span>{error}</span><button className="icon-button" aria-label="Dismiss error" onClick={()=>setError('')}><IconX size={18}/></button></div>}
      <div className="overview-content" hidden={tab!=='Overview'}><section className="overview-hero"><div className="setup-column">{title}<GardenSetup onRun={analyze} busy={busy} collapsed={collapsed} onExpand={()=>setCollapsed(false)} draft={layout.draft} onChange={draft=>dispatchLayout({type:'draft',draft})} tool={layout.tool} selectedCrop={plant?.setup.input.crop_name??null} cellLabel={`Row ${Math.floor(layout.selected/8)+1}, column ${layout.selected%8+1}`} dirty={!!plant&&setupChanged(layout.draft,plant.setup)} onSave={savePlant} onRevert={()=>dispatchLayout({type:'revert'})} profile={profile} onEditProfile={openProfile}/></div><BotanicalSpecimen record={record} onTab={changeTab} plant={plant}/><GardenGrid layout={layout} onTool={selectTool} onCell={useCell} storageWarning={storageWarning}/></section><div className="care-section"><Calendar run={run} selectedDate={record.date} onSelect={selectDate}/><CareSchedule record={record} onTab={changeTab}/></div></div>{tab!=='Overview'&&<div className="detail-page"><div className="detail-title-row">{title}<div className="selected-day"><label htmlFor="detail-date">Selected simulation date</label><input id="detail-date" type="date" value={record.date} min={run.start_date} max={run.end_date} onChange={e=>{if(run.records.some(r=>r.date===e.target.value))selectDate(e.target.value);}}/></div></div><Suspense fallback={<p className="help" role="status">Opening garden details…</p>}><AnimatePresence mode="wait"><motion.div key={tab} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={{opacity:0}} transition={{duration:.2}}>{tab==='Plant Growth'?<Growth run={run} record={record} onSelect={selectDate}/>:tab==='Soil & Water'?<Water run={run} record={record} isExample={isExample}/>:tab==='Nutrients'?<Nutrients run={run} record={record}/>:<Environment run={run} record={record} isExample={isExample}/>}</motion.div></AnimatePresence></Suspense></div>}
      <footer className="data-footer"><span>{isExample?'Example garden · illustrative weather and modeled results':`${run.site.location_name} · modeled results`}</span><span>{isExample?'Connect your local backend with Analyze garden':`${dateLabel(run.start_date)} – ${dateLabel(run.end_date,{month:'short',day:'numeric',year:'numeric'})} · ${run.records.length} days`}</span><span className="run-coordinate">{format(Math.abs(run.site.latitude),4)}° {run.site.latitude>=0?'N':'S'} · {format(Math.abs(run.site.longitude),4)}° {run.site.longitude>=0?'E':'W'}</span></footer>
    </main>
    <nav className="mobile-nav" aria-label="Mobile navigation">{tabs.map((item,i)=>{const Icon=navIcons[i];return <button key={item} aria-label={item} aria-current={tab===item?'page':undefined} className={tab===item?'active':''} onClick={()=>changeTab(item)}><Icon size={23} stroke={1.5}/><span>{['Overview','Growth','Water','Nutrients','Weather'][i]}</span></button>;})}</nav>
  </div>{profileOpen&&<ProfileDialog profile={profile} onSave={saveProfile} onClose={()=>setEditingProfile(false)}/>}</MotionConfig>;
}
