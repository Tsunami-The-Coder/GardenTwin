import {lazy,Suspense,useEffect,useRef,useState} from 'react';
import {IconCheck,IconMapPin,IconPlant2,IconSearch,IconX,IconLoader2} from '@tabler/icons-react';
import {searchLocations,type LocationChoice} from './locationSearch';
import {coordinateLabel,validCoordinates,type GardenProfile} from './profile';

const GardenLocationMap = lazy(()=>import('./GardenLocationMap'));
interface ProfileDialogProps {profile:GardenProfile|null;onSave:(profile:GardenProfile)=>string|null;onClose:()=>void}

export function ProfileDialog({profile,onSave,onClose}:ProfileDialogProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [name,setName] = useState(profile?.name ?? '');
  const [query,setQuery] = useState(profile?.location.label ?? '');
  const [point,setPoint] = useState<LocationChoice|null>(profile?.location ?? null);
  const [confirmed,setConfirmed] = useState(!!profile);
  const [results,setResults] = useState<LocationChoice[]>([]);
  const [showMap,setShowMap] = useState(false);
  const [busy,setBusy] = useState(false);
  const [searchMessage,setSearchMessage] = useState('');
  const [error,setError] = useState('');
  const [coordinates,setCoordinates] = useState({latitude:profile?String(profile.location.latitude):'',longitude:profile?String(profile.location.longitude):''});
  const request = useRef<AbortController|null>(null);
  const sequence = useRef(0);
  const timeout = useRef<ReturnType<typeof setTimeout>|null>(null);
  useEffect(()=>{
    const element = dialog.current;
    const opener = document.activeElement;
    const overflow = document.body.style.overflow;
    document.body.style.overflow='hidden';
    const cancel=(event:Event)=>{event.preventDefault();if(profile)onClose();};
    const closed=()=>{if(!profile&&element?.isConnected&&!element.open)element.showModal();};
    const trapFocus=(event:KeyboardEvent)=>{
      if(event.key!=='Tab'||!element)return;
      const controls=[...element.querySelectorAll<HTMLElement>('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"]),summary')].filter(control=>control.getClientRects().length>0);
      if(!controls.length)return;
      const current=controls.indexOf(document.activeElement as HTMLElement);
      const next=event.shiftKey?(current<=0?controls.length-1:current-1):(current+1)%controls.length;
      event.preventDefault();controls[next].focus();
    };
    element?.addEventListener('cancel',cancel);
    element?.addEventListener('close',closed);
    element?.addEventListener('keydown',trapFocus,true);
    element?.setAttribute('closedby',profile?'closerequest':'none');
    element?.showModal();
    return ()=>{
      ++sequence.current;request.current?.abort();
      if (timeout.current) clearTimeout(timeout.current);
      element?.removeEventListener('cancel',cancel);element?.removeEventListener('close',closed);element?.removeEventListener('keydown',trapFocus,true);
      element?.close();document.body.style.overflow=overflow;
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus({preventScroll:true});
    };
  },[]);
  function cancelSearch() {
    ++sequence.current;request.current?.abort();request.current=null;
    if (timeout.current) clearTimeout(timeout.current);
    setBusy(false);
  }
  function editQuery(value:string) {
    cancelSearch();setQuery(value);setPoint(null);setConfirmed(false);setResults([]);setSearchMessage('');setError('');
  }
  async function search() {
    cancelSearch();setResults([]);setSearchMessage('');setError('');
    if (query.trim().length<3) {setSearchMessage('Enter an address or place name with at least three characters.');return;}
    const current = sequence.current;
    const controller = new AbortController();request.current=controller;
    let timedOut=false;
    timeout.current=setTimeout(()=>{timedOut=true;controller.abort();},15000);
    setBusy(true);
    try {
      const choices=await searchLocations(query,controller.signal);
      if (current!==sequence.current) return;
      setResults(choices);
      setSearchMessage(choices.length?'Choose a result, then confirm your garden pin.':'No matching locations. Try adding a town or postcode, or choose a point on the map.');
    } catch (e) {
      if (current!==sequence.current) return;
      setSearchMessage(timedOut?'Address search took too long. Try again or choose a point on the map.':e instanceof Error && e.name!=='AbortError'?e.message:'Address search was interrupted. Please try again.');
    } finally {
      if (current===sequence.current) {if(timeout.current)clearTimeout(timeout.current);setBusy(false);request.current=null;}
    }
  }
  function choosePoint(value:LocationChoice) {
    cancelSearch();setPoint(value);setQuery(value.source==='photon'?value.label:'');setResults([]);setConfirmed(false);setSearchMessage('');setError('');
    if(value.source==='photon')setShowMap(false);
    setCoordinates({latitude:String(value.latitude),longitude:String(value.longitude)});
  }
  function chooseCoordinates() {
    const latitude=Number(coordinates.latitude),longitude=Number(coordinates.longitude);
    if (!coordinates.latitude.trim() || !coordinates.longitude.trim() || !validCoordinates(latitude,longitude)) {setError('Enter latitude from −90 to 90 and longitude from −180 to 180.');return;}
    choosePoint({latitude,longitude,label:`Garden pin · ${coordinateLabel(latitude,longitude)}`,source:'coordinates'});
  }
  function submit(event:React.FormEvent) {
    event.preventDefault();
    if (!point || !confirmed) {setError('Choose and confirm your garden location first.');return;}
    const issue=onSave({version:1,name:name.trim(),location:{...point,confirmedAt:new Date().toISOString()}});
    if (issue) setError(issue);
  }
  return <dialog ref={dialog} className="profile-dialog" aria-labelledby="profile-title" aria-describedby="profile-intro">
    <form className="profile-form" onSubmit={submit}>
      <div className="profile-dialog-heading"><span className="profile-sprout"><IconPlant2 size={26} stroke={1.4}/></span>{profile&&<button type="button" className="icon-button" aria-label="Close profile" onClick={onClose}><IconX size={20}/></button>}</div>
      <h2 id="profile-title">{profile?'Your garden profile':'A little about your garden.'}</h2>
      <p id="profile-intro">{profile?'Update your name or move your garden pin.':'Settle in. Save your name and garden location once.'}</p>
      <label className="profile-field"><span>Name or username</span><input autoFocus autoComplete="nickname" maxLength={60} required value={name} onChange={e=>{setName(e.target.value);setError('');}} placeholder="What should we call you?"/></label>
      <label className="profile-field" htmlFor="profile-address"><span>Garden address or place</span></label>
      <div className="profile-search-row"><input id="profile-address" value={query} maxLength={300} autoComplete="off" placeholder="Street address, town, or garden name" aria-describedby="profile-search-status" onChange={e=>editQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault();void search();}}}/><button className="outline-button" type="button" aria-label={busy?'Searching locations':'Search address'} disabled={busy} onClick={()=>void search()}>{busy?<IconLoader2 className="spin" size={17}/>:<IconSearch size={17}/>}<span>{busy?'Searching':'Search'}</span></button></div>
      <p className="profile-search-status" id="profile-search-status" role="status" aria-live="polite">{searchMessage||'Search for an address, or choose your garden directly on the map.'}</p>
      {!!results.length&&<ul className="profile-search-results" aria-label="Address results">{results.map((result,i)=><li key={`${result.latitude}-${result.longitude}-${i}`}><button type="button" onClick={()=>choosePoint(result)}><IconMapPin size={18}/><span>{result.label}</span></button></li>)}</ul>}
      <button type="button" className="profile-map-toggle" aria-expanded={showMap} aria-controls="profile-map-panel" onClick={()=>setShowMap(value=>!value)}><IconMapPin size={16}/>{showMap?'Hide map':point?'Check or adjust pin on map':'Choose on map instead'}</button>
      {showMap&&<div id="profile-map-panel"><Suspense fallback={<div className="profile-map-loading" role="status">Opening your garden map…</div>}><GardenLocationMap point={point} onPick={choosePoint}/></Suspense>
      <details className="profile-coordinate-entry"><summary>Have exact coordinates?</summary><div className="profile-coordinate-fields"><label className="profile-field"><span>Latitude</span><input type="number" step="any" min="-90" max="90" value={coordinates.latitude} onChange={e=>{setCoordinates({...coordinates,latitude:e.target.value});setConfirmed(false);setPoint(null);}}/></label><label className="profile-field"><span>Longitude</span><input type="number" step="any" min="-180" max="180" value={coordinates.longitude} onChange={e=>{setCoordinates({...coordinates,longitude:e.target.value});setConfirmed(false);setPoint(null);}}/></label><button type="button" className="outline-button" onClick={chooseCoordinates}>Use coordinates</button></div></details></div>}
      {point&&<div className="profile-chosen-location"><IconMapPin size={20}/><div><strong>{point.label}</strong><small>{coordinateLabel(point.latitude,point.longitude)} · {point.source==='photon'?'Address search result':point.source==='map'?'Map pin':'Entered coordinates'}</small></div></div>}
      <label className={`profile-confirm ${!point?'unavailable':''}`}><input type="checkbox" disabled={!point} checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/><span>This is my garden’s location.</span></label>
      {error&&<p className="profile-error" role="alert">{error}</p>}
      {profile&&<p className="profile-change-note">Location changes apply to your garden setup. Existing simulation results keep their original location.</p>}
      <button className="primary-button profile-submit" type="submit" disabled={!point||!confirmed||!name.trim()||busy}><IconCheck size={18}/>{profile?'Save profile':'Save & enter garden'}</button>
      {profile&&<button className="profile-cancel" type="button" onClick={onClose}>Cancel</button>}
      <p className="profile-privacy">No password needed. Your profile stays in this browser.<br/>Address search: <a href="https://photon.komoot.io" target="_blank" rel="noreferrer">Photon</a> · Map data: <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a></p>
    </form>
  </dialog>;
}
