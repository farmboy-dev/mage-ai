// Run against the disposable offline UI/server, not a production project.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,args:['--no-sandbox']});
 const outbound=[],errors=[],failed=[],results=[],cloudRequests=[];
 try {
  const context=await browser.newContext({serviceWorkers:'block'});
  await context.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(!['localhost','127.0.0.1'].includes(url.hostname)) {
    outbound.push(url.origin+url.pathname);await route.abort();
   }else await route.continue();
  });
  const page=await context.newPage();
  page.on('request',r=>{if(/\/api\/(clusters|compute_services|compute_clusters|compute_connections)(\/|\?|$)/.test(r.url()))cloudRequests.push(r.url());});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',async r=>{
   const path=new URL(r.url()).pathname;
   if(r.status()>=400)failed.push([r.status(),path]);
   if(path.startsWith('/api/')&&(r.headers()['content-type']||'').includes('application/json')) {
    try {const body=await r.json();if(body.error)failed.push([body.error.code,path,body.error.message]);}catch(e){}
   }
  });
  page.on('websocket',ws=>{if(!['localhost','127.0.0.1'].includes(new URL(ws.url()).hostname))outbound.push(ws.url());});
  for(const path of ['/sign-in','/settings/workspace/preferences','/overview','/compute','/pipelines','/pipelines/local_build_smoke/settings','/pipelines/local_build_smoke/edit']) {
   const response=await page.goto((process.env.MAGE_TEST_FRONTEND_URL || 'http://localhost:3001')+path,{waitUntil:'domcontentloaded',timeout:180000});
   if(response.status()!==200)throw Error(path+': '+response.status());
   if(path.endsWith('/edit')) {
    await page.locator('.monaco-editor').first().waitFor({timeout:60000});
    if(await page.getByText('Select cluster',{exact:true}).count())throw Error('Cloud cluster selector present');
    await page.getByRole('button',{name:'Compute',exact:true}).click();
    await page.getByRole('menuitem',{name:'Switch to PySpark kernel',exact:true}).waitFor({timeout:60000});
    await page.getByRole('button',{name:'Compute',exact:true}).click();
    await page.getByText('Compute unavailable',{exact:true}).waitFor({timeout:60000});
    const switches=[['Python','PySpark'],['PySpark','Python']];
    if(await page.getByRole('button',{name:'PySpark',exact:true}).isVisible())switches.unshift(['PySpark','Python']);
    for(const [from,to] of switches) {
     await page.getByRole('button',{name:from,exact:true}).click();
     const [saved]=await Promise.all([
      page.waitForResponse(r=>new URL(r.url()).pathname==='/api/pipelines/local_build_smoke'&&r.request().method()==='PUT'),
      page.getByRole('menuitem',{name:to,exact:true}).click(),
     ]);
     const body=await saved.json();
     if(body.error)throw Error(JSON.stringify(body.error));
     if(body.pipeline?.type!==(to==='PySpark'?'pyspark':'python'))throw Error('Kernel selection not saved');
     await page.getByRole('button',{name:to,exact:true}).waitFor({timeout:60000});
     await page.waitForFunction(async ({url,name})=>{
      const body=await (await fetch(url)).json();
      return body.kernels?.some(kernel=>kernel.name===name&&kernel.alive);
     },{url:new URL(saved.url()).origin+'/api/kernels',name:to==='PySpark'?'pysparkkernel':'python3'},
     {timeout:30000,polling:500});
    }

   }
   else if(path.endsWith('/settings')) {
    const select=page.locator('select').filter({has:page.locator('option[value="local_python"]')});
    await select.waitFor({timeout:60000});
    const options=await select.locator('option').evaluateAll(nodes=>nodes.map(n=>n.value).filter(Boolean));
    if(JSON.stringify(options)!==JSON.stringify(['local_python','k8s']))throw Error('Unexpected executor options: '+options);
   }
   else if(path==='/compute') {
    await page.getByText('Standalone cluster',{exact:true}).first().waitFor({timeout:60000});
    await page.getByText('Setup',{exact:true}).first().click();
    const sparkAppName='offline-ui-restored-'+Date.now();
    await page.getByPlaceholder('e.g. Sparkmage').fill(sparkAppName);
    const [saved]=await Promise.all([
     page.waitForResponse(r=>new URL(r.url()).pathname.startsWith('/api/projects/')&&r.request().method()==='PUT'),
     page.getByRole('button',{name:'Save changes',exact:true}).click(),
    ]);
    const body=await saved.json();
    if(body.error||body.project?.spark_config?.app_name!==sparkAppName)throw Error('Spark settings not saved');
    for(const tab of ['Setup','Resources','Monitoring','System']) {
     await page.getByText(tab,{exact:true}).first().click();
     await page.waitForTimeout(1000);
     if(tab==='Setup') {
      await page.getByPlaceholder('e.g. Sparkmage').scrollIntoViewIfNeeded();
      await page.screenshot({path:'/tmp/mage-restored-spark-setup.png'});
     }
     if(tab==='Resources')await page.getByRole('button',{name:'Add Spark configuration',exact:true}).waitFor();
     if(tab==='Monitoring')await page.getByText('SQLs',{exact:true}).waitFor();
     if(tab==='System')await page.getByText('Runtime',{exact:true}).waitFor();
    }
    if(await page.getByText('AWS EMR',{exact:true}).count())throw Error('EMR service present');
   }
   else if(path.includes('preferences')) {
    await page.locator('#openai_base_url').waitFor({timeout:60000});
    if(await page.locator('#help_improve_mage_toggle').count())throw Error('Telemetry toggle still present');
   }
   await page.waitForTimeout(2500);
   if(await page.locator('a[href*="cloud.mage.ai/sign-up"]').count())throw Error('Cloud signup present');
   results.push({path,status:response.status(),title:await page.title()});
   console.log('Page checked:',path);
  }
  fs.writeFileSync(process.env.MAGE_UI_AUDIT_REPORT || '/tmp/mage-ui-audit.json',JSON.stringify({results,outbound,errors,failed,cloudRequests},null,2));
  if(outbound.length||errors.length||failed.length||cloudRequests.length)throw Error(JSON.stringify({outbound,errors,failed}));
  console.log('7 pages and Monaco: PASS; external requests: 0; page errors: 0');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
