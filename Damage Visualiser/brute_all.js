/* brute_all.js - the proven best five for every Mythic boss fight, across all the machine's cores.
 *
 * Splits each fight by its first character: the sweep enumerates teams in pool order, so handing out
 * first-character values gives slices that never overlap and together are every team. Slices are handed
 * out one at a time rather than divided up front, because they are wildly uneven - the slice starting at
 * the first character holds 5.3 million teams, the one starting at the hundredth holds a handful - and a
 * queue keeps every core busy to the end.
 *
 * Run:  node brute_all.js [--workers 24] [--out best_fives.json] [--fights 13,7]
 *
 * See INSTRUCTIONS.md, "The Calculate button" and PLAN.md, "How good is the search?".
 */
const {Worker, isMainThread, workerData, parentPort} = require('worker_threads');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DATA = path.join(__dirname, 'calc.json');
const MOW = 'Biovore';                  /* the owner's rule: the Biovore wherever it is allowed */
const FALLBACK = ['Malleus Rocket Launcher', 'Rukkatrukk', 'Plagueburst Crawler'];   /* where it isn't */

/* ---------------------------------------------------------------- a worker */
if (!isMainThread) {
  const c = require('./calc.js');
  const b = require('./brute.js');
  const D = c.load(JSON.parse(fs.readFileSync(DATA, 'utf8')));
  const ctxOf = new Map();
  parentPort.on('message', job => {
    if (job === 'stop') { process.exit(0); }
    const key = job.fi + '|' + job.mow;
    if (!ctxOf.has(key)) ctxOf.set(key, b.prep(D, job.fi, job.mow));
    const ctx = ctxOf.get(key);
    b.DMG.clear(); b.BIG.clear();       /* a slice is its own world; stale entries only slow it down */
    const t0 = Date.now();
    const got = b.sweep(ctx, {aFrom: job.aFrom, aTo: job.aTo});
    parentPort.postMessage({
      fi: job.fi, mow: job.mow, tried: got.tried, secs: (Date.now() - t0) / 1000,
      best: got.best, bestTeam: got.bestTeam ? got.bestTeam.map(x => x.n) : null,
      perChar: got.perChar.map((s, i) => (s > -Infinity ? [i, s, got.perCharTeam[i].map(x => x.n)] : null))
        .filter(Boolean),
    });
  });
  return;
}

/* ---------------------------------------------------------------- the main thread */
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const c = require('./calc.js');
const b = require('./brute.js');
const D = c.load(JSON.parse(fs.readFileSync(DATA, 'utf8')));
const nWorkers = +arg('workers', Math.max(1, (os.cpu_count ? os.cpu_count() : os.cpus().length) - 1));
const only = arg('fights', '') ? arg('fights', '').split(',').map(Number) : null;
const outPath = arg('out', path.join(__dirname, 'best_fives.json'));

/* which machine each fight gets, and how much work it is */
const jobs = [];
const plan = [];
D.bosses.forEach((both, fi) => {
  if (only && !only.includes(fi)) return;
  const boss = both[1];
  const mows = boss.mow[MOW] !== undefined ? [MOW] : FALLBACK.filter(n => boss.mow[n] !== undefined);
  const pool = D.chars.filter(x => x.f !== boss.ban).length;
  plan.push({fi, mows, pool});
  for (const mow of mows) for (let a = 0; a < pool - 4; a++) jobs.push({fi, mow, aFrom: a, aTo: a + 1});
});
const C5 = n => n * (n - 1) * (n - 2) * (n - 3) * (n - 4) / 120;
const totalTeams = plan.reduce((s, p) => s + C5(p.pool) * p.mows.length, 0);
console.log(`${plan.length} fights, ${jobs.length} slices, ${Math.round(totalTeams).toLocaleString()} teams, `
  + `${nWorkers} workers`);

const best = {};                        /* fi -> the best five found so far */
const perChar = {};                     /* fi -> character index -> [score, team] */
let done = 0, teams = 0, started = Date.now();

let live = 0;
function take(w) {
  const job = jobs.shift();
  if (!job) { w.postMessage('stop'); w.terminate(); if (--live === 0) finish(); return false; }
  w.postMessage(job);
  return true;
}

const workers = [];
for (let i = 0; i < nWorkers; i++) {
  const w = new Worker(__filename);
  w.on('message', r => {
    teams += r.tried; done++;
    const cur = best[r.fi];
    if (r.bestTeam && (!cur || r.best > cur.score)) best[r.fi] = {score: r.best, team: r.bestTeam, mow: r.mow};
    const pc = perChar[r.fi] || (perChar[r.fi] = {});
    for (const [i2, s, team] of r.perChar) if (!pc[i2] || s > pc[i2][0]) pc[i2] = [s, team, r.mow];
    if (done % 50 === 0 || !jobs.length) {
      const secs = (Date.now() - started) / 1000;
      console.log(`  ${done}/${done + jobs.length} slices, ${Math.round(teams / 1e6)}M teams, `
        + `${Math.round(teams / secs).toLocaleString()} teams/s, ${(secs / 60).toFixed(1)} min`);
    }
    take(w);
  });
  workers.push(w);
}
live = workers.length;
for (const w of workers) take(w);

function finish() {
  const secs = (Date.now() - started) / 1000;
  const chars = D.chars.map(x => x.n);
  const out = {built: new Date().toISOString(), version: D.version || null, fingerprint: D.fingerprint || null,
               setting: D.setting,
               seconds: Math.round(secs), teams, fights: {}};
  for (const p of plan) {
    const boss = D.bosses[p.fi][1];
    const pool = D.chars.filter(x => x.f !== boss.ban);
    const rank = Object.entries(perChar[p.fi] || {})
      .map(([i, v]) => ({n: pool[+i].n, score: v[0], team: v[1], mow: v[2]}))
      .sort((x, y) => y.score - x.score);
    out.fights[p.fi] = {best: best[p.fi], perChar: rank};
    console.log(`fight ${p.fi}: ${Math.round(best[p.fi].score).toLocaleString()}  `
      + `${best[p.fi].team.join(', ')}  (+ ${best[p.fi].mow})`);
  }
  fs.writeFileSync(outPath, JSON.stringify(out));
  console.log(`\n${Math.round(teams).toLocaleString()} teams in ${(secs / 60).toFixed(1)} minutes `
    + `(${Math.round(teams / secs).toLocaleString()} teams/s). Written to ${path.basename(outPath)}.`);
}
