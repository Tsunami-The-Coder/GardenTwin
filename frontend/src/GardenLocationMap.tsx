import {useEffect,useRef,useState} from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type {LocationChoice} from './locationSearch';
import {coordinateLabel} from './profile';

const DEFAULT_CENTER:L.LatLngTuple = [40.5187,-74.4121];
const MAP_TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const gardenMarker = L.divIcon({className:'garden-location-marker',html:'<span aria-hidden="true"></span>',iconSize:[30,38],iconAnchor:[15,38]});

export default function GardenLocationMap({point,onPick}:{point:LocationChoice|null;onPick:(point:LocationChoice)=>void}) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map|null>(null);
  const marker = useRef<L.Marker|null>(null);
  const onPickRef = useRef(onPick);
  onPickRef.current = onPick;
  const initialPoint = useRef(point);
  const [tileError,setTileError] = useState(false);
  useEffect(()=>{
    if (!host.current) return;
    const first = initialPoint.current;
    const instance = L.map(host.current,{scrollWheelZoom:false,worldCopyJump:true}).setView(first ? [Math.max(-85,Math.min(85,first.latitude)),first.longitude] : DEFAULT_CENTER,first ? 16 : 11);
    map.current = instance;
    instance.attributionControl.setPrefix(false);
    const tiles = L.tileLayer(MAP_TILES,{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'}).addTo(instance);
    tiles.on('tileerror',()=>setTileError(true));
    const pick = (latlng:L.LatLng) => {
      const latitude = Math.max(-90,Math.min(90,latlng.lat));
      const longitude = ((latlng.lng+180)%360+360)%360-180;
      onPickRef.current({latitude,longitude,label:`Garden pin · ${coordinateLabel(latitude,longitude)}`,source:'map'});
    };
    instance.on('click',(event:L.LeafletMouseEvent)=>pick(event.latlng));
    const observer = new ResizeObserver(()=>instance.invalidateSize({pan:false}));
    observer.observe(host.current);
    return ()=>{observer.disconnect();instance.remove();map.current=null;marker.current=null;};
  },[]);
  useEffect(()=>{
    const instance = map.current;
    if (!instance) return;
    if (!point) {marker.current?.remove();marker.current=null;return;}
    const position:L.LatLngTuple = [point.latitude,point.longitude];
    if (!marker.current) {
      marker.current = L.marker(position,{icon:gardenMarker,draggable:true,title:'Garden location. Drag to adjust.',alt:'Selected garden location'}).addTo(instance);
      marker.current.on('dragend',()=>{
        const position=marker.current!.getLatLng();
        const longitude=((position.lng+180)%360+360)%360-180;
        onPickRef.current({latitude:position.lat,longitude,label:`Garden pin · ${coordinateLabel(position.lat,longitude)}`,source:'map'});
      });
    } else marker.current.setLatLng(position);
    if (point.source === 'photon' || point.source === 'coordinates') instance.setView([Math.max(-85,Math.min(85,point.latitude)),point.longitude],16,{animate:false});
  },[point]);
  return <div className="profile-map-frame"><div className="profile-map" ref={host} role="region" aria-label="Garden location map"/><p className="profile-map-hint">{tileError?'Map tiles could not load. Address search and coordinate entry are still available.':'Click the map to place your garden pin. Drag the pin to fine-tune it.'}</p></div>;
}
