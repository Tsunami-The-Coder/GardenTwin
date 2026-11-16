import {useEffect, useRef, useState} from 'react';
import * as THREE from 'three';

/** A real Three.js scene using the approved photographic specimen as a textured plane.
 * It is deliberately an illustrative image, not a scanned 3D plant or a health measurement. */
export default function PlantScene({resetKey = 0}: {resetKey?: number}) {
  const host = useRef<HTMLDivElement>(null);
  const [ready,setReady] = useState(false);
  useEffect(()=>{
    const parent = host.current;
    if (!parent) return;
    let alive=true;
    let renderer: THREE.WebGLRenderer;
    try { renderer = new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'}); }
    catch { return; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
    renderer.outputColorSpace=THREE.SRGBColorSpace;
    renderer.setClearColor(0x000000,0);
    parent.appendChild(renderer.domElement);
    const scene=new THREE.Scene();
    const camera=new THREE.PerspectiveCamera(32,1,.1,100);
    camera.position.z=5.6;
    const geometry=new THREE.PlaneGeometry(1.9,2.85,12,24);
    let material: THREE.MeshBasicMaterial | undefined;
    let mesh: THREE.Mesh | undefined;
    let texture: THREE.Texture | undefined;
    const pointer=new THREE.Vector2();
    const reduce=window.matchMedia('(prefers-reduced-motion: reduce)');
    const loader=new THREE.TextureLoader();
    loader.load('/garden/tomato.png',loaded=>{
      if(!alive){loaded.dispose();return;}
      texture=loaded;texture.colorSpace=THREE.SRGBColorSpace;
      material=new THREE.MeshBasicMaterial({map:texture,transparent:true,side:THREE.DoubleSide,depthWrite:false});
      mesh=new THREE.Mesh(geometry,material);scene.add(mesh);setReady(true);
    },undefined,()=>setReady(false));
    const resize=()=>{const {width,height}=parent.getBoundingClientRect();renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();};
    const observer=new ResizeObserver(resize);observer.observe(parent);resize();
    const move=(event:PointerEvent)=>{const box=parent.getBoundingClientRect();pointer.set((event.clientX-box.left)/box.width-.5,(event.clientY-box.top)/box.height-.5);};
    const leave=()=>pointer.set(0,0);
    parent.addEventListener('pointermove',move);parent.addEventListener('pointerleave',leave);
    renderer.setAnimationLoop(time=>{
      if(mesh){const moving=!reduce.matches;mesh.rotation.y=THREE.MathUtils.lerp(mesh.rotation.y,moving?pointer.x*.22:0,.06);mesh.rotation.z=moving?Math.sin(time*.00065)*.008:0;mesh.position.x=moving?pointer.x*.04:0;}
      renderer.render(scene,camera);
    });
    return ()=>{alive=false;observer.disconnect();renderer.setAnimationLoop(null);geometry.dispose();material?.dispose();texture?.dispose();renderer.dispose();renderer.domElement.remove();parent.removeEventListener('pointermove',move);parent.removeEventListener('pointerleave',leave);};
  },[resetKey]);
  return <div className="plant-scene" ref={host} role="img" aria-label="Interactive illustrative tomato specimen">{!ready&&<img className="scene-fallback" src="/garden/tomato.png" alt="Tomato specimen"/>}</div>;
}
