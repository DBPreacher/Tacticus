/* brute.js - the best five for a Guild Raid boss, by trying every five there is.
 *
 * calc.js scores one team the way guild_raid.py does. Scoring 128 million of them that way takes an hour
 * a fight, because it works each character out from scratch every time. It doesn't have to: a character's
 * damage depends on the buffs reaching it, not on who its team-mates are, and there are only a few
 * thousand distinct buff situations in the whole pool (Kariyan sees 2,315 of them across 200,000 teams).
 * So this works each one out once and remembers it, and the search becomes mostly lookups.
 *
 * Everything it remembers is keyed on exactly what the answer depends on, so the result is identical to
 * calc.js - check() proves that on random teams before any long run starts.
 *
 * Run:  node brute.js --fight 13 [--mow Biovore] [--check] [--limit 200000]
 */
const fs = require('fs');
const path = require('path');
const c = require('./calc.js');

/* ---------------------------------------------------------------- setting a fight up */
function prep(D, fi, mowName) {
  const boss = D.bosses[fi][1];                 /* side battles cleared */
  const pool = D.chars.filter(x => x.f !== boss.ban);
  let mow = null;
  if (mowName !== 'none') {
    const m = D.mows.find(x => x.n === mowName && boss.mow[x.n] !== undefined);
    if (!m) throw new Error(mowName + ' is not allowed against this boss');
    mow = {n: m.n, b: m.b, own: boss.mow[m.n]};
  }
  return {D, boss, pool, mow, buff: mow ? mow.b : null, turns: D.turns, immune: boss.tr.includes('Immune')};
}

/* what a character's buffs come to, as a string: two teams that give it the same buffs give it the same
   damage, whoever else is in them */
function tokenKey(toks) {
  if (!toks.length) return '';
  const parts = new Array(toks.length);
  for (let i = 0; i < toks.length; i++) {
    const t = toks[i].t;
    parts[i] = toks[i].up + '' + t.k + '' + t.s + '' + (t.v === undefined ? '' : t.v)
      + '' + (t.cap === undefined ? '' : t.cap) + '' + (t.p ? t.p.d + ',' + t.p.h + ',' + t.p.t : '')
      + '' + (t.o ? (t.o.vs || '') + ',' + (t.o.notype || '') + ',' + (t.o.type || '') + ',' + (t.o.gearonly || '') : '');
  }
  return parts.sort().join('');
}

/* ---------------------------------------------------------------- the caches */
const DMG = new Map();        /* one character's damage, given its buffs */
const BIG = new Map();        /* one character's biggest hit, which is what Outrage feeds on */

/* The three things a character's damage reads off its team-mates besides their buffs. Miss one and the
   cache hands back a number from a different team - the check against calc.js catches it at once. */
function mateKey(m, mates) {
  let k = '';
  if (m.rampFlat !== undefined || m.psyCap !== undefined || m.direct)
    k += mates.map(x => x.n).sort().join(',');            /* Atlacoya's stacks, Sekhetar's extra hits */
  if (m.n === 'Laviscus')
    k += '' + mates.filter(x => x.a === 'Chaos').length;   /* his +Crit Damage per Chaos ally */
  if (m.sum)
    k += '' + (mates.some(x => x.n === 'Neurothrope' && x.crown) ? 1 : 0);   /* the Norn Crown lifts summons */
  return k;
}

function memberDamage(ctx, m, mates, toks, tk, extra, uses, high) {
  /* the key holds everything the answer depends on and nothing else */
  let key = m.n + '' + tk + '' + (high ? 1 : 0) + '' + mateKey(m, mates);
  if (m.rampFlat !== undefined) key += '' + uses.join(',');
  if (extra) {
    let any = false;
    for (let i = 0; i < extra.length; i++) if (extra[i]) { any = true; break; }
    if (any) key += '' + extra.map(x => Math.round(x)).join(',');
  }
  let v = DMG.get(key);
  if (v === undefined) {
    v = c.memberDamage(ctx.D, m, mates, ctx.boss, extra, ctx.buff, uses, high) + c.summonDamage(ctx.D, m, [m].concat(mates), ctx.boss);
    DMG.set(key, v);
  }
  return v;
}

function biggestHit(ctx, m, mates, tk, opener, turn, high) {
  const key = m.n + '' + tk + '' + (opener ? 1 : 0) + ''
    + (m.rampPct !== undefined ? turn : 0) + '' + (high ? 1 : 0) + '' + mateKey(m, mates);
  let v = BIG.get(key);
  if (v === undefined) {
    v = c.biggestHit(ctx.D, m, mates, ctx.boss, opener, turn, high);
    BIG.set(key, v);
  }
  return v;
}

/* ---------------------------------------------------------------- one team */
const EMPTY = [];

function score(ctx, team, want) {
  const D = ctx.D, turns = ctx.turns, n = team.length;
  const mates = new Array(n), toks = new Array(n), tks = new Array(n), actives = new Array(n);
  let uses = [];
  for (let i = 0; i < n; i++) {
    const rest = [];
    for (let j = 0; j < n; j++) if (j !== i) rest.push(team[j]);
    mates[i] = rest;
    toks[i] = c.buffsFor(team[i], rest, D, ctx.immune);
    tks[i] = tokenKey(toks[i]);
    actives[i] = c.activeTurns(team[i], turns);
    for (const t of actives[i]) uses.push(t);
  }
  uses.sort((a, b) => a - b);

  /* the flat Damage each character brings into this five */
  const neuro = team.find(x => x.n === 'Neurothrope');
  const extraOf = (i, on) => {
    const m = team[i];
    let out = null;
    if (m.n === 'Laviscus') {
      const pct = (m.outragePct || 0) / 100;
      out = new Array(turns);
      for (let turn = 1; turn <= turns; turn++) {
        let s = 0;
        for (let j = 0; j < n; j++) {
          if (j === i) continue;
          s += biggestHit(ctx, team[j], mates[j], tks[j], actives[j].has(turn), turn, on ? on.has(team[j].n) : false);
        }
        if (actives[i].has(turn)) s += c.abilityHit(D, m, ctx.boss);
        out[turn - 1] = pct * s;
      }
    }
    let flat = 0;
    if (neuro && m.n === 'Neurothrope') flat += neuro.parasite[0] * neuro.parasite[1];
    if (ctx.buff && ctx.buff.k === 'dmg' && c.matches(m, ctx.buff.who)) flat += m.dmg * ctx.buff.pct / 100;
    if (!out && !flat && m.rampTeam === undefined && !m.rampStack) return EMPTY;
    const res = out || new Array(turns).fill(0);
    for (let k = 0; k < turns; k++) {
      res[k] += flat;
      if (m.rampTeam !== undefined) { let u = 0; for (const x of uses) if (x < k + 1) u++; res[k] += m.rampTeam * u; }
      if (m.rampStack) res[k] += m.rampStack[0] * Math.min(k, m.rampStack[1]);
    }
    return res;
  };

  const each = new Array(n);
  for (let i = 0; i < n; i++)
    each[i] = memberDamage(ctx, team[i], mates[i], toks[i], tks[i], extraOf(i, null), uses, false);

  /* the two doing the most damage take the high ground, which changes what they do and what Laviscus is fed */
  const order = each.map((v, i) => i).sort((a, b) => each[b] - each[a]);
  const on = new Set(order.slice(0, D.high.n).map(i => team[i].n));
  for (let i = 0; i < n; i++) {
    if (!on.has(team[i].n) && team[i].n !== 'Laviscus') continue;
    each[i] = memberDamage(ctx, team[i], mates[i], toks[i], tks[i], extraOf(i, on), uses, on.has(team[i].n));
  }
  let total = ctx.mow ? ctx.mow.own : 0;
  for (let i = 0; i < n; i++) total += each[i];
  return want ? {total, each, on: [...on]} : total;
}

/* ---------------------------------------------------------------- every five there is */
function sweep(ctx, opts) {
  const pool = ctx.pool, N = pool.length, limit = opts.limit || Infinity;
  let best = -Infinity, bestTeam = null, tried = 0;
  const perChar = new Array(N).fill(-Infinity), perCharTeam = new Array(N).fill(null);
  const team = new Array(5);
  outer:
  for (let a = 0; a < N - 4; a++) {
    team[0] = pool[a];
    for (let b = a + 1; b < N - 3; b++) {
      team[1] = pool[b];
      for (let d = b + 1; d < N - 2; d++) {
        team[2] = pool[d];
        for (let e = d + 1; e < N - 1; e++) {
          team[3] = pool[e];
          for (let f = e + 1; f < N; f++) {
            team[4] = pool[f];
            const s = score(ctx, team, false);
            tried++;
            if (s > best) { best = s; bestTeam = team.slice(); }
            const ix = [a, b, d, e, f];
            for (let q = 0; q < 5; q++) if (s > perChar[ix[q]]) { perChar[ix[q]] = s; perCharTeam[ix[q]] = team.slice(); }
            if (tried >= limit) break outer;
          }
        }
      }
    }
  }
  return {best, bestTeam, tried, perChar, perCharTeam};
}

module.exports = {prep, score, sweep, tokenKey, DMG, BIG};

/* ---------------------------------------------------------------- run it */
if (require.main === module) {
  const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
  const D = c.load(JSON.parse(fs.readFileSync(arg('data', path.join(__dirname, 'calc.json')), 'utf8')));
  const fi = +arg('fight', 13);
  const ctx = prep(D, fi, arg('mow', 'Biovore'));

  if (process.argv.includes('--check')) {
    /* the fast scorer has to agree with calc.js exactly, or none of this is worth anything */
    let worst = 0, n = 0;
    for (let i = 0; i < 4000; i++) {
      const t = [], u = new Set();
      while (t.length < 5) { const j = (Math.random() * ctx.pool.length) | 0; if (!u.has(j)) { u.add(j); t.push(ctx.pool[j]); } }
      const fast = score(ctx, t, false);
      const slow = c.teamTotal(D, t, ctx.boss, ctx.mow, true).total;
      worst = Math.max(worst, Math.abs(fast - slow) / Math.max(slow, 1)); n++;
    }
    console.log('checked ' + n + ' random teams against calc.js, worst difference ' + (worst * 100).toFixed(6) + '%');
  }

  const limit = +arg('limit', 0) || 0;
  const t0 = Date.now();
  const got = sweep(ctx, {limit: limit || Infinity});
  const secs = (Date.now() - t0) / 1000;
  const C5 = n => n * (n - 1) * (n - 2) * (n - 3) * (n - 4) / 120;
  const all = C5(ctx.pool.length);
  console.log('pool ' + ctx.pool.length + ', ' + got.tried.toLocaleString() + ' of ' + all.toLocaleString()
    + ' teams in ' + secs.toFixed(1) + 's  =  ' + Math.round(got.tried / secs).toLocaleString() + ' teams/second');
  console.log('  remembered: ' + DMG.size.toLocaleString() + ' character situations, ' + BIG.size.toLocaleString() + ' biggest hits');
  console.log('  best so far: ' + Math.round(got.best).toLocaleString() + '  '
    + (got.bestTeam || []).map(x => x.n).join(', '));
  if (!limit) console.log('  (that was every team)');
  else console.log('  one core would take ' + (all / (got.tried / secs) / 3600).toFixed(1) + ' hours for this fight');
}
