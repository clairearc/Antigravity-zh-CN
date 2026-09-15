// Run with PLAYWRIGHT_MODULE and CHROME_PATH pointing at local installations.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const bundle = process.argv[2];
(async () => {
  const browser = await chromium.launch({headless:true, executablePath:process.env.CHROME_PATH});
  try {
    const page = await browser.newPage();
    await page.setContent(`<body><button id="ui">Settings</button><button id="dynamic"></button>
      <div role="article" id="message">Settings <button>Run</button></div>
      <code id="code">Settings</code><textarea id="input" placeholder="Settings">Settings</textarea>
      <div contenteditable="true" id="editor">Settings</div>
      <a href="/c/example" id="title">Settings</a>
      <nav><h2><button aria-expanded="true" id="heading">Projects</button></h2>
      <button aria-expanded="true" id="project">Settings</button></nav>
      <div id="unknown">Settings for customer ABC</div><button id="proto">constructor</button></body>`);
    const source = fs.readFileSync(`${bundle}/localization.generated.js`, 'utf8');
    await page.evaluate(source);
    await page.waitForFunction(() => document.querySelector('#ui').textContent === '设置');
    assert.equal(await page.locator('#message').innerText(), 'Settings Run');
    for (const id of ['code','editor','title','project']) assert.equal(await page.locator('#'+id).innerText(), 'Settings');
    assert.equal(await page.locator('#input').inputValue(), 'Settings');
    assert.equal(await page.locator('#input').getAttribute('placeholder'), '设置');
    assert.equal(await page.locator('#heading').innerText(), '项目');
    assert.equal(await page.locator('#unknown').innerText(), 'Settings for customer ABC');
    assert.equal(await page.locator('#proto').innerText(), 'constructor');
    await page.locator('#dynamic').evaluate(e => { e.textContent='Tool Permissions'; e.setAttribute('aria-label','Settings'); });
    await page.waitForFunction(() => document.querySelector('#dynamic').getAttribute('aria-label') === '设置');
    assert.equal(await page.locator('#dynamic').innerText(), '工具权限');
    await page.locator('#dynamic').evaluate(e => { e.firstChild.nodeValue='Browser settings have moved'; e.setAttribute('title','Settings'); });
    await page.waitForFunction(() => document.querySelector('#dynamic').textContent === '浏览器设置已迁移');
    assert.equal(await page.locator('#dynamic').getAttribute('title'), '设置');
    await page.evaluate(source); // Duplicate initialization is harmless.
    assert.equal(await page.evaluate(() => globalThis.__antigravityZhCN.version), '2.13.0');
    // A mocked native menu verifies translated labels retain item identity/actions.
    const fileMenu={label:'File',submenu:{items:[],insert(i,x){this.items.splice(i,0,x);}}};
    const helpMenu={label:'Help',submenu:{items:[],insert(i,x){this.items.splice(i,0,x);}}};
    const menu={items:[fileMenu,helpMenu]};
    const exports={}; let applied=0;
    const electron={Menu:{getApplicationMenu:()=>menu,setApplicationMenu:m=>{assert.equal(m,menu);applied++;}},MenuItem:function(x){Object.assign(this,x);},shell:{openExternal:()=>{}}};
    vm.runInNewContext(fs.readFileSync(`${bundle}/app/dist/menu.js`,'utf8'),{exports,require:n=>n==='electron'?electron:n==='./utils'?{isMacOS:()=>false,createWindow:()=>{}}:{}});
    exports.setupApplicationMenu('https://localhost');
    assert.equal(fileMenu.label,'文件');
    assert.equal(fileMenu.submenu.items[0].label,'新建窗口');
    assert.equal(typeof fileMenu.submenu.items[0].click,'function');
    assert.equal(helpMenu.submenu.items[0].label,'文档');
    exports.setupApplicationMenu('https://localhost');
    assert.equal(applied,2);
    assert.equal(fileMenu.submenu.items.length,2);
    console.log('PASS: initial/dynamic/attribute translations, protected content, duplicate init, native menu callbacks');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
