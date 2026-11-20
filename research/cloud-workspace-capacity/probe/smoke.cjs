// Synthetic fixture only: no application source, URLs, credentials, or downloads.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const root = process.cwd();
const stage = process.argv[2];
(async () => {
  assert.equal(os.tmpdir(), path.join(root, 'tmp'));
  if (stage === 'build') {
    fs.mkdirSync('dist', {recursive: true});
    fs.writeFileSync('dist/index.html', '<!doctype html><title>capacity probe</title><h1 id="result">isolated smoke</h1>');
    fs.writeFileSync(path.join(os.tmpdir(), 'node-tmp-proof.txt'), 'owned synthetic probe\n');
    console.log(JSON.stringify({status:'PASS', stage, node:process.version, tmpdir:'RUN_ROOT/tmp', build:'synthetic Node file build, not an application bundler'}));
    return;
  }
  const playwright = require(process.env.PROBE_PLAYWRIGHT_MODULE);
  const engine = stage;
  let browser;
  try {
    browser = await playwright[engine].launch({headless:true, executablePath:process.env[engine === 'chromium' ? 'PROBE_CHROMIUM' : 'PROBE_WEBKIT'], timeout:20000});
    const page = await browser.newPage();
    await page.setContent(fs.readFileSync('dist/index.html', 'utf8'));
    assert.equal(await page.locator('#result').textContent(), 'isolated smoke');
    await page.screenshot({path:path.join(root, engine + '.png')});
    // Observe library-created temp directory names while the browser is live.
    const tempEntries = fs.readdirSync(os.tmpdir()).sort();
    console.log(JSON.stringify({status:'PASS', stage, browserVersion:browser.version(), playwright:require(path.join(process.env.PROBE_PLAYWRIGHT_MODULE,'package.json')).version, tempEntries}));
  } finally { if (browser) await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
