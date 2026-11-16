import {ResponsiveContainer,LineChart,Line,CartesianGrid,XAxis,YAxis,Tooltip,ReferenceLine,BarChart,Bar} from 'recharts';
import {dateLabel} from './api';
type Point = {date:string; [key:string]:number|string|null};
export function TimeChart({data,series,unit,lines=[]}:{data:Point[];series:{key:string;name:string;color:string}[];unit:string;lines?:{value:number;name:string}[]}){
  return <div className="chart" role="img" aria-label={`${series.map(s=>s.name).join(', ')} over time, ${unit}`}>
    <ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{top:18,right:20,bottom:6,left:0}}><CartesianGrid vertical={false} stroke="#e4e2d6"/><XAxis dataKey="date" tickFormatter={d=>dateLabel(d)} minTickGap={40} tickLine={false} axisLine={false} tick={{fontSize:11,fill:'#667664'}}/><YAxis width={48} tickLine={false} axisLine={false} tick={{fontSize:11,fill:'#667664'}}/><Tooltip labelFormatter={d=>dateLabel(String(d))} contentStyle={{background:'#faf7f0',border:'1px solid #dcd7cb',borderRadius:8,fontSize:12}}/><ReferenceLine y={0} stroke="#dcd7cb"/>{lines.map(l=><ReferenceLine key={l.name} y={l.value} stroke="#9c9f80" strokeDasharray="5 5" label={{value:l.name,position:'insideTopRight',fontSize:10,fill:'#667664'}}/>)}{series.map(s=><Line key={s.key} type="monotone" dataKey={s.key} name={`${s.name} (${unit})`} stroke={s.color} strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false}/>)}</LineChart></ResponsiveContainer>
    <div className="chart-legend">{series.map(s=><span key={s.key}><i style={{background:s.color}}/>{s.name}</span>)}<span>{unit}</span></div>
  </div>;
}
export function RainChart({data}:{data:Point[]}){
  return <div className="chart" role="img" aria-label="Daily rainfall, millimeters"><ResponsiveContainer width="100%" height="100%"><BarChart data={data}><CartesianGrid vertical={false} stroke="#e4e2d6"/><XAxis dataKey="date" tickFormatter={d=>dateLabel(d)} minTickGap={40} tickLine={false} axisLine={false} tick={{fontSize:11}}/><YAxis width={40} tickLine={false} axisLine={false} tick={{fontSize:11}}/><Tooltip labelFormatter={d=>dateLabel(String(d))}/><Bar dataKey="rain" name="Rainfall (mm)" fill="#81956d" radius={[2,2,0,0]} isAnimationActive={false}/></BarChart></ResponsiveContainer></div>;
}
