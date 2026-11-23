import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";


const vlogRoot = "C:\\Users\\Sirue'tto\\Desktop\\软件工程\\liuhaobin\\AlphaSprint\\vlog";
const playwrightEntry =
  "C:\\Program Files\\WindowsApps\\OpenAI.CodexPrimaryRuntime.v26-1116-1220-0_26.1116.1220.0_x64__3k8sg7r9htsxt\\dependencies\\node\\node_modules\\playwright\\index.mjs";
const outputPath = path.join(vlogRoot, "报时鸟-Alpha冲刺Vlog.mp4");
const stagingPath = path.join(vlogRoot, "报时鸟-Alpha冲刺Vlog.webm");

const { chromium } = await import(pathToFileURL(playwrightEntry).href);
await fs.mkdir(vlogRoot, {recursive: true});
await fs.rm(outputPath, {force: true});
await fs.rm(stagingPath, {force: true});

const browser = await chromium.launch({
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  headless: true,
  args: ["--autoplay-policy=no-user-gesture-required"],
});
const context = await browser.newContext({
  viewport: {width: 1280, height: 720},
  acceptDownloads: true,
});
const page = await context.newPage();
await page.goto("http://127.0.0.1:8790/vlog/vlog_stage.html", {
  waitUntil: "networkidle",
});
await page.waitForFunction(() => window.assetsReady || window.assetError);
const assetError = await page.evaluate(() => window.assetError);
if (assetError) throw new Error(assetError);

const downloadPromise = page.waitForEvent("download", {timeout: 240000});
const runPromise = page.evaluate(() => window.startVlog());
const download = await downloadPromise;
const declaredPath = await download.path();
const filename = download.suggestedFilename();
const target = filename.endsWith(".mp4") ? outputPath : stagingPath;
await download.saveAs(target);
const result = await runPromise;
const vite = await page.evaluate(() => window.vlogResult);
await browser.close();

console.log(JSON.stringify({
  downloadedPath: declaredPath,
  filename,
  target,
  result,
  vite,
}, null, 2));
