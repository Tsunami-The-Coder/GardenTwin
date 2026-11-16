import type {CropName} from './gardenLayout';

const cropSymbols: Record<CropName,string> = {Tomato:'🍅',Pepper:'🫑',Cucumber:'🥒',Lettuce:'🥬',Carrot:'🥕',Bean:'🫘',Strawberry:'🍓'};
export const plantAssets: Partial<Record<CropName,string>> = {Tomato:'/garden/tomato.png'};
export function CropIcon({crop,className=''}:{crop:CropName;className?:string}) {
  return <span className={`crop-icon ${className}`} role="img" aria-label={`${crop} icon`}>{crop === 'Tomato' ? <img src="/garden/tomato-fruit.png" alt=""/> : cropSymbols[crop]}</span>;
}
