'use strict';
// Invoked only by runner.py. No download, network, shared-temp fallback or cleanup.
const fs=require('fs'), path=require('path'), os=require('os');
const {chromium}=require('playwright');
(async()=>{
 const root=fs.realpathSync(process.env.TMPDIR);
 if(root!==fs.realpathSync(os.tmpdir())) throw Error('temp mismatch');
 const profile=path.join(root,'profile'); fs.mkdirSync(profile);
 const probe=path.join(root,'probe.txt');fs.writeFileSync(probe,'isolated-temp-42\n',{flag:'wx'});
 const readback=fs.readFileSync(probe,'utf8');
 if(readback!=='isolated-temp-42\n') throw Error('readback mismatch');
 console.log(JSON.stringify({phase:'temp',path:'probe.txt',readback}));
 let context;
 try {
  context=await chromium.launchPersistentContext(profile,{executablePath:process.env.PROBE_CHROMIUM,chromiumSandbox:true,headless:true,timeout:15000,args:['--disk-cache-dir='+path.join(root,'browser-cache')]});
  await context.route('**/*',r=>r.abort());
  const page=await context.newPage();
  await page.setContent('<!doctype html><h1 id="answer">isolated-temp-42</h1>');
  const actual=await page.locator('#answer').textContent();
  if(actual!=='isolated-temp-42') throw Error('DOM mismatch');
  console.log(JSON.stringify({phase:'dom',actual,profileFiles:fs.readdirSync(profile)}));
 } finally {if(context) await context.close();}
 console.log(JSON.stringify({phase:'closed'}));
})().catch(e=>{console.error(e.stack);process.exitCode=2;});
