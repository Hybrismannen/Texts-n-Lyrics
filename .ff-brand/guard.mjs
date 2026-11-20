#!/usr/bin/env node
/**
 * FFC-BDH Portable Anchor/Output Guard 2.0.0.
 * Vendor this exact source in downstream repos at .ff-brand/guard.mjs.
 * The FFC House, not this derivative, remains normative authority.
 * This tool is a repository source checker, not a browser/SEO/raster certification.
 */
import {readFileSync,existsSync,statSync} from 'node:fs';
import {resolve,extname} from 'node:path';
import {execFileSync} from 'node:child_process';
const root=process.cwd();
const anchorPath=resolve(root,'.ff-brand/anchor.json');
const allRooms=['BDH-R01','BDH-R02','BDH-R03','BDH-R04','BDH-R05','BDH-R06','BDH-R07','BDH-R08','BDH-R09'];
const canonicalCommit='6efbaa388e495089723f40c8bac323e50005b75e';
const paints=new Set(['#018C8B','#E36811','#8E3B00','#E5F4F1','#F9E7D8','#F8F7F5','#FFFFFF','#000000','#00D5D2','#F5A8CA']);
const forbidden=[['#018C8B','#00D5D2'],['#E36811','#F5A8CA']];
let errors=[],holds=[];
const fail=(code,msg)=>{errors.push(code+': '+msg);console.error('::error title='+code+'::'+msg)};
const hold=(code,msg)=>{holds.push(code+': '+msg);console.warn('::warning title='+code+'::'+msg)};
if(!existsSync(anchorPath)){fail('FF-BDH-ANCHOR-MISSING','Cannot resolve .ff-brand/anchor.json');finish()}
let a;try{a=JSON.parse(readFileSync(anchorPath,'utf8'))}catch(e){fail('FF-BDH-ANCHOR-INVALID',e.message);finish()}
if(a.schema!=='ff.bdh.anchor/v2'||a.house_id!=='FFC-BDH')fail('FF-BDH-ROOM-MISMATCH','Invalid anchor schema or house');
if(a.policy_version!=='2.0.0'||a.authority_commit!==canonicalCommit)fail('FF-BDH-POLICY-STALE','Pinned policy version/commit mismatch; explicit migration required');
if(!['T0','T1'].includes(a.tier))fail('FF-BDH-TIER-INVALID','Expected T0 or T1');
const rooms=Array.isArray(a.rooms)?a.rooms:[];
if(rooms.length!==new Set(rooms).size||rooms.some(r=>!allRooms.includes(r)))fail('FF-BDH-ROOM-MISMATCH','Duplicated or unknown room ID');
if(a.tier==='T0'&&rooms.length!==allRooms.length)fail('FF-BDH-ROOM-MISMATCH','T0 must bind all nine rooms');
if(a.tier==='T1'&&(rooms.length===0||rooms.length>=allRooms.length))fail('FF-BDH-ROOM-MISMATCH','T1 must declare an explicit nonempty subset');
const selected=new Set(rooms);
if(a.tier==='T1'&&!selected.has('BDH-R02')&&a.inherit_gates?.includes('BDH-HG-01'))fail('FF-BDH-TIER-OVERREACH','Cannot enforce corporate palette on an independent T1');
const args=process.argv.slice(2);
let paths=[];
if(args[0]==='--changed'&&args[1]){
 try{paths=execFileSync('git',['diff','--name-only','--diff-filter=ACMR',args[1]+'...HEAD'],{encoding:'utf8',cwd:root}).trim().split('\n').filter(Boolean)}
 catch(e){fail('FF-BDH-GIT-DIFF',e.message)}
}else if(args[0]==='--inspect'&&args[1]){paths=args.slice(1)}
else if(args[0]==='--anchor-only'){paths=[]}
else{fail('FF-BDH-ARGUMENT','Use --changed BASE_SHA, --inspect PATH or --anchor-only')}
function normal(hex){let s=hex.slice(1).toUpperCase();if(s.length===3)s=s.split('').map(x=>x+x).join('');return '#'+s}
function checkSource(file,content){
 const found=new Set();
 for(const m of content.matchAll(/#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})(?![0-9a-f])/gi)){
  const paint=normal(m[0]);if(!paints.has(paint))fail('FF-PALETTE-HARDGATE','UNAPPROVED FF COLOR — STOP OUTPUT: '+file+' @ '+m.index+' found '+m[0]);else found.add(paint);
 }
 for(const m of content.matchAll(/\brgba?\s*\(([^)]*)\)/gi)){
  const ch=m[1].split(',').map(x=>x.trim());
  if(ch.length<3||ch.length>4||ch.slice(0,3).some(x=>!/^\d{1,3}$/.test(x)||Number(x)>255)){fail('FF-PALETTE-HARDGATE','Unsupported RGB paint in '+file+': '+m[0]);continue}
  const p='#'+ch.slice(0,3).map(x=>Number(x).toString(16).padStart(2,'0')).join('').toUpperCase();
  if(!paints.has(p)||ch.length===4&&ch[3]!=='1')fail('FF-PALETTE-HARDGATE','Unapproved or translucent RGB in '+file+': '+m[0]);else found.add(p);
 }
 for(const m of content.matchAll(/\b(?:hsla?|color-mix|oklch|oklab|lab|lch|hwb)\s*\([^)]*\)/gi))fail('FF-PALETTE-HARDGATE','Unsupported mixed or alternative paint model in '+file+': '+m[0]);
 for(const pair of forbidden)if(pair.every(p=>found.has(p)))fail('FF-PALETTE-HARDGATE','Forbidden pair '+pair.join(' and ')+' in '+file);
}
const srcExt=new Set(['.css','.scss','.svg','.tsx','.jsx','.html','.htm','.vue','.astro']);
const binaryExt=new Set(['.png','.jpg','.jpeg','.webp','.gif','.pdf','.avif','.pptx','.tif','.tiff']);
for(const f of paths){
 if(f.startsWith('.ff-brand/')||f.startsWith('.github/')||f.includes('archive/')||f.includes('legacy/'))continue;
 const full=resolve(root,f);
 if(!full.startsWith(root+'/')||!existsSync(full)||!statSync(full).isFile())continue;
 const ext=extname(f).toLowerCase();
 if(selected.has('BDH-R02')&&srcExt.has(ext))checkSource(f,readFileSync(full,'utf8'));
 if(selected.has('BDH-R02')&&binaryExt.has(ext)&&!existsSync(full+'.palette-review.json'))fail('FF-PALETTE-HARDGATE','Binary visual '+f+' requires real inspected palette-review.json evidence');
 if(selected.has('BDH-R06')&&srcExt.has(ext))hold('FF-BDH-SEO-RELEASE-HOLD','New/changed web source '+f+' requires separately evidenced SEO-G01–G12 at public release; code lint cannot certify deployed indexing');
 if((selected.has('BDH-R04')||selected.has('BDH-R05'))&&srcExt.has(ext))hold('FF-BDH-UX-REVIEW-REQUIRED','Check keyboard, responsive, motion and actual interaction in '+f+'; source lint alone is insufficient');
}
if(args[0]==='--changed'){
 const outputPaths=paths.filter(f=>!f.startsWith('.ff-brand/')&&!f.startsWith('.github/')&&!f.includes('archive/')&&!f.includes('legacy/')&&['.css','.scss','.svg','.tsx','.jsx','.html','.htm','.vue','.astro','.png','.jpg','.jpeg','.webp','.gif','.pdf','.avif','.pptx'].includes(extname(f).toLowerCase()));
 if(outputPaths.length){
  const review=resolve(root,'.ff-brand/output-review.json');
  if(!existsSync(review))fail('FF-BDH-OUTPUT-REVIEW-HOLD','Output-affecting files changed but no .ff-brand/output-review.json attestation exists: '+outputPaths.join(', '));
  else try{
   const q=JSON.parse(readFileSync(review,'utf8'));
   if(!q.reviewedBy||!q.reviewedAt||!Array.isArray(q.reviewedFiles)||!Array.isArray(q.roomsChecked)||!q.evidenceRefs||outputPaths.some(f=>!q.reviewedFiles.includes(f))||rooms.some(id=>!q.roomsChecked.includes(id)))fail('FF-BDH-OUTPUT-REVIEW-HOLD','Incomplete source/render review record; include all changed visual files, bound rooms, reviewer and evidence references');
  }catch(e){fail('FF-BDH-OUTPUT-REVIEW-HOLD','Invalid review record: '+e.message)}
 }
}
if(process.env.BDH_PUBLIC_RELEASE==='true'&&selected.has('BDH-R06')){
 const proof=resolve(root,'.ff-brand/seo-release-evidence.json');
 if(!existsSync(proof))fail('FF-BDH-SEO-RELEASE-HOLD','Missing human-reviewed SEO-G01–G12 deployment evidence');
 else try{
 const p=JSON.parse(readFileSync(proof,'utf8'));
 const checks=Array.isArray(p.checks)?p.checks:[];
 const required=['SEO-G01','SEO-G02','SEO-G03','SEO-G04','SEO-G06','SEO-G07','SEO-G10','SEO-G12'];
 if(!p.deploymentUrl||!p.reviewedBy||!p.reviewedAt||required.some(id=>!checks.some(c=>c.id===id&&c.status==='PASS'&&c.evidence)))fail('FF-BDH-SEO-RELEASE-HOLD','Incomplete published-URL SEO evidence for required checks');
 }catch(e){fail('FF-BDH-SEO-RELEASE-HOLD','Cannot parse SEO release evidence: '+e.message)}
}
console.log('FF-BDH guard',a.tier,'rooms:',rooms.join(', '),'paths:',paths.length,'errors:',errors.length,'warnings:',holds.length);
finish();
function finish(){if(errors.length){for(const e of errors)console.error(e);process.exit(1)}process.exit(0)}
