import {build} from 'vite';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('..',import.meta.url));
const result=spawnSync(process.execPath,[root+'/node_modules/typescript/bin/tsc','--noEmit'],{cwd:root,stdio:'inherit'});
if(result.status!==0)process.exit(result.status??1);
await build({root});
const packaged=spawnSync(process.execPath,['scripts/prepare-sites-build.mjs'],{cwd:root,stdio:'inherit'});
process.exit(packaged.status??1);
