/* calc.js - scoring a team the page's user picked, in the browser.
 *
 * This is the arithmetic half of guild_raid.py. Everything hard (reading abilities, resolving them to
 * numbers at a level and rarity) already happened in Python; what arrives here is plain numbers, and this
 * file does the same sums build_map.normal_attack and guild_raid.team_damage do. The two have to agree, so
 * calc_data.py ships 50 exact scores and check() runs them.
 *
 * Kept as its own file so it can be run under node against those vectors before it ever reaches the page.
 */
const PIERCE = {Bio: .30, Blast: .15, Bolter: .20, Chain: .20, Direct: 1, Energy: .30, Eviscerating: .50,
  Flame: .25, 'Heavy Round': .55, Las: .10, Melta: .75, Molecular: .60, Particle: .35, Physical: .01,
  Piercing: .80, Plasma: .65, Power: .40, Projectile: .15, Psychic: 1, Pulse: .20, Toxic: .70};

const sum = xs => xs.reduce((a, b) => a + b, 0);
const prod = xs => xs.reduce((a, b) => a * b, 1);
/* expected hits in a crit or block chain: it starts on hit 1 and each later hit re-rolls until one fails */
const chain = (c, n) => { let t = 0; for (let k = 1; k <= Math.max(1, Math.floor(n)); k++) t += Math.pow(c, k); return t; };

function hitValue(D, A, p, gravis) {
  let y = Math.max(D - A, D * p);
  if (gravis && p < 1) y = Math.max(y - A, y * p);
  return y;
}

/* who a buff helps: 'all', 'has:ranged', names joined by | against alliance/faction/traits, '!' to negate */
function matches(u, who) {
  if (!who || who === 'all') return true;
  const neg = who.startsWith('!');
  const names = new Set(who.replace(/^!/, '').split('|'));
  let hit;
  if (names.has('has:ranged') || names.has('no:ranged')) {
    const has = u.w.some(w => w.k === 'ranged');
    hit = (names.has('has:ranged') && has) || (names.has('no:ranged') && !has);
  } else {
    const tags = new Set([u.a, u.f, ...u.tr]);
    hit = [...names].some(n => tags.has(n));
  }
  return hit !== neg;
}

/* does one of a character's own effects apply to this attack? */
function applies(e, kind, first, boss) {
  const sc = e.s;
  const ok = sc === 'all' || sc === kind || (sc === 'after' && !first) || (sc === 'one' && first);
  if (!ok) return false;
  const tags = new Set(boss.tr);
  if (e.vs && !e.vs.some(x => tags.has(x))) return false;
  if (e.vsnot && e.vsnot.some(x => tags.has(x))) return false;
  return true;
}

function critOf(a, kind, first, boss, trig, gearx) {
  if (!a.g) return null;
  const eff = (a.pg || []).concat(gearx || []).filter(e => applies(e, kind, first, boss));
  let cc = a.g.cc + sum(eff.filter(e => e.k === 'critchance').map(e => e.v));
  let cd = a.g.cd + sum(eff.filter(e => e.k === 'critdmg').map(e => e.v));
  if (trig && a.tr.includes('ActOfFaith')) { cc += 0.10; cd *= 1.25; }
  if (trig && a.tr.includes('ThrillSeekers')) cc += 0.15;
  cd *= prod(eff.filter(e => e.k === 'critdmgpct').map(e => 1 + e.v));
  cc -= boss.ccr || 0; cd -= boss.cdr || 0;          /* what the boss takes off a crit */
  if (eff.some(e => e.k === 'alwayscrit')) cc = 1;
  return [Math.min(Math.max(cc, 0), 1), Math.max(cd, 0)];
}

function abilityHits(part, boss, crit) {
  const p = PIERCE[part.t] === undefined ? .2 : PIERCE[part.t];
  const D = Math.max(part.d, 0);
  const psychic = part.t === 'Psychic' || part.t === 'Direct';
  const gravis = boss.tr.includes('MkXGravis');
  const y = hitValue(D, boss.arm, p, gravis);
  let total = y * part.h;
  if (crit && crit[0] > 0 && part.c !== false) {
    const yc = hitValue(D + crit[1], boss.arm, p, false);
    total += chain(crit[0], part.h) * Math.max(yc - y, 0);
  }
  if (boss.bc > 0 && !psychic) total -= chain(boss.bc, part.h) * Math.min(boss.bd, y);
  return Math.max(total, 0);
}

/* one normal attack, mirroring build_map.normal_attack */
function normalAttack(a, boss, w, trig, dmgOverride, first, gearx, follow) {
  const at = a.tr, dt = boss.tr, melee = w.k === 'melee';
  const eff = (a.ps || []).filter(e => applies(e, w.k, first, boss));
  const add = k => sum(eff.filter(e => e.k === k).map(e => e.v || 0));
  const effg = a.g ? (a.pg || []).concat(gearx || []).filter(e => applies(e, w.k, first, boss)) : [];
  let n = w.h + Math.trunc(add('hits'));
  const p = Math.min(1, w.p + add('pierce') / 100);
  let D = (dmgOverride === undefined || dmgOverride === null ? a.dmg : dmgOverride) + add('flat');
  D += sum(effg.filter(e => e.k === 'dmgfromblock').map(e => e.v * a.g.bd));
  let A = Math.max(0, boss.arm - add('armignore')) * (1 - Math.min(add('armpct'), 100) / 100);
  const psychic = w.t === 'Psychic' || w.t === 'Direct';
  if (melee && dt.includes('Parry') && n > 1) n -= 1;
  if (!melee && dt.includes('Camouflage')) n = Math.max(1, n - ((trig && w.r >= 3) ? 2 : 1));
  D += add('ramp') * (n - 1) / 2;
  if (trig) {
    if (at.includes('GetStuckIn')) n += Math.floor(n / 2) * 0.3;
    if (at.includes('LetTheGalaxyBurn')) n += 0.33;
    if (at.includes('WeaverOfFate')) D *= 1.2;
    if (at.includes('ContagionsOfNurgle') && melee) A *= 0.8;
  }
  const y = hitValue(D, A, p, dt.includes('MkXGravis'));
  let m = prod(eff.filter(e => e.k === 'pct').map(e => 1 + e.v / 100));
  if (melee && dt.includes('Terrifying')) m *= 0.7;
  if (dt.includes('MartialKatah')) m *= 0.8;
  if (melee && at.includes('BeastSlayer') && (dt.includes('BigTarget') || dt.includes('Vehicle'))) m *= 1.2;
  if (w.t === 'Melta' && dt.includes('Vehicle')) m *= 1.5;
  if (trig) {
    if (at.includes('RapidAssault')) m *= 1.25;
    if (!melee && at.includes('HeavyWeapon')) m *= 1.25;
    if (melee && at.includes('CrushingStrike')) m *= 1.5;
    if (!melee && at.includes('RangedSpecialist')) m *= 1.33;
    if (at.includes('PrioritisedEfficiency')) m *= 1.25;
    if (at.includes('BlessingsOfKhorne')) m *= 1.12;
    if (dt.includes('PrioritisedEfficiency')) m *= 0.75;
    if (psychic && dt.includes('BlessingsOfKhorne')) m *= 0.68;
    if (psychic && dt.includes('ShadowInTheWarp') && at.includes('Psyker')) m *= 0.75;
  }
  const perHit = y * m;
  let total = perHit * n;
  const cr = critOf(a, w.k, first, boss, trig, gearx);
  if (cr && cr[0] > 0) {
    const perCrit = hitValue(D + cr[1], A, p, false) * m;
    total += chain(cr[0], n) * Math.max(perCrit - perHit, 0);
    for (const e of effg)                                 /* relic: extra hits when the attack crits */
      if (e.k === 'critextra') total += cr[0] * abilityHits(e.p, boss, null);
  }
  if (boss.bc > 0 && !psychic) total -= chain(boss.bc, n) * Math.min(boss.bd, perHit);
  if (trig && !psychic) {
    if (dt.includes('Daemon')) total -= chain(0.25, n) * Math.min(0.5 * boss.dmg, perHit);
    if (dt.includes('BeastSlayer')) total -= chain(0.10, n) * Math.min(boss.arm, perHit);
  }
  for (const e of eff) {
    if (e.k === 'extra') {
      const part = (e.pb && dt.includes('BigTarget')) ? e.pb : e.p;
      /* these are attacks the character performs, so the traits that lift an attack lift them too */
      total += abilityHits(part, boss, cr) * m;
    }
  }
  if (follow !== false && melee && eff.some(e => e.k === 'follow')) {
    const rw = a.w.find(x => x.k === 'ranged');           /* a melee swing that fires as well */
    if (rw) total += normalAttack(a, boss, rw, trig, dmgOverride, first, gearx, false).dmg;
  }
  return {dmg: Math.max(total, 1), w};
}

function bestAttack(a, boss, trig, dmgOverride, first, kind, gearx) {
  let best = null;
  const ws = (kind ? a.w.filter(w => w.k === kind) : a.w);
  for (const w of (ws.length ? ws : a.w)) {
    const got = normalAttack(a, boss, w, trig, dmgOverride, first, gearx, true);
    if (!best || got.dmg > best.dmg) best = got;
  }
  return best;
}


/* ---------------------------------------------------------------- the team half (guild_raid.py) */
const TEAM_REACH = {team: 4, target: 4, one: 1, 'next attack': 1, adjacent: 2, '2 hexes': 3};
const SCOPE = {normal: 'all', 'normal-melee': 'melee', 'normal-ranged': 'ranged'};
const clone = x => JSON.parse(JSON.stringify(x));

/* the Attack-side tokens a character picks up, each with how many rounds it is up for */
function buffsFor(member, mates, D, immune) {
  const toks = [], everyone = mates.concat([member]);
  for (const s of everyone) {
    for (const r of D.rows) {
      if (r.n !== s.n || r.src === 'Relic') continue;
      if (s.n === member.n && !r.self) continue;
      if (!matches(member, r.rec)) continue;
      /* Mind Control needs the Taunt to land, and a Boss is immune to Taunt */
      if (immune && r.n === 'Xybia' && r.ab === 'Mind Control') continue;
      if (s.n !== member.n) {
        const elig = everyone.filter(m => m.n !== s.n && matches(m, r.rec)).sort((x, y) => y.dmg - x.dmg);
        if (!elig.slice(0, TEAM_REACH[r.reach] === undefined ? 1 : TEAM_REACH[r.reach]).some(m => m.n === member.n)) continue;
      }
      for (const tok of r.t) {
        if (immune && tok.k === 'armour') continue;          /* a Boss's Armour can't be reduced */
        if (tok.o && tok.o.who && !matches(member, tok.o.who)) continue;
        toks.push({t: tok, up: r.up});
      }
    }
  }
  return toks;
}

/* apply those tokens: mirrors support_model.buffed */
function buffed(ally, toks, spec) {
  const a = Object.assign({}, ally, {ps: (ally.ps || []).slice(), pg: (ally.pg || []).slice()});
  spec = spec ? clone(spec) : null;
  for (const tok of toks) {
    const k = tok.k, o = tok.o || {}, v = tok.v;
    let vs = null, vsnot = null;
    if (o.vs) { const names = o.vs.replace(/^!/, '').split('|'); if (o.vs.startsWith('!')) vsnot = names; else vs = names; }
    const types = o.type ? o.type.split('|') : null;
    const notypes = o.notype ? o.notype.split('|') : [];
    const scope = SCOPE[tok.s] === undefined ? tok.s : SCOPE[tok.s];
    const weapons = a.w.filter(w => (scope === 'all' || scope === 'ability' || w.k === scope)
      && (types === null || types.includes(w.t)) && !notypes.includes(w.t));
    const kinds = [...new Set(weapons.map(w => w.k))].sort();
    const add = (kind, extra) => { for (const wk of kinds) a.ps.push(Object.assign({k: kind, s: wk, vs, vsnot}, extra)); };
    if (scope === 'ability') {
      if (k === 'pct') {
        if (spec) for (const p of spec.p) p.d *= 1 + v / 100;
        a.ps = a.ps.map(e => {
          if (e.k !== 'extra') return e;
          const n = Object.assign({}, e, {p: Object.assign({}, e.p, {d: e.p.d * (1 + v / 100)})});
          if (e.pb) n.pb = Object.assign({}, e.pb, {d: e.pb.d * (1 + v / 100)});
          return n;
        });
      } else if (k === 'hits') {
        if (spec && spec.p.length) spec.p[0].h += Math.trunc(v);
        else {
          let done = false;
          a.ps = a.ps.map(e => {
            if (done || e.k !== 'extra') return e;
            done = true;
            const n = Object.assign({}, e, {p: Object.assign({}, e.p, {h: e.p.h + Math.trunc(v)})});
            if (e.pb) n.pb = Object.assign({}, e.pb, {h: e.pb.h + Math.trunc(v)});
            return n;
          });
        }
      }
      continue;
    }
    if (k === 'hits' && tok.cap === undefined && v !== Math.trunc(v)) {
      for (const w of weapons) a.ps.push({k: 'pct', s: w.k, vs, vsnot, v: v / w.h * 100});
    } else if (['flat', 'pct', 'pierce', 'armignore', 'ramp'].includes(k) || (k === 'hits' && tok.cap === undefined)) {
      add(k, {v});
    } else if (k === 'hits') {
      for (const w of weapons) a.ps.push({k: 'extra', s: w.k, vs, vsnot,
        p: {d: Math.min(a.dmg, tok.cap), h: Math.trunc(v), t: w.t, c: true}});
    } else if (k === 'extra' || k === 'partner') {
      add('extra', {p: tok.p});
    } else if (k === 'attack') {
      const w = weapons.length ? weapons.reduce((x, y) => (y.h > x.h ? y : x)) : null;
      if (w) a.ps.push({k: 'extra', s: 'all', vs, vsnot,
        p: {d: Math.min(a.dmg * v / 100, tok.cap === undefined ? 1e9 : tok.cap), h: w.h, t: w.t, c: true}});
    } else if (k === 'follow') {
      add('follow', {});
    } else if (k === 'taken' || k === 'takenpct') {
      add(k === 'taken' ? 'flat' : 'pct', {v});
      if (tok.s === 'all') {
        const bump = x => (k === 'taken' ? x + v : x * (1 + v / 100));
        if (spec) for (const p of spec.p) p.d = bump(p.d);
        a.ps = a.ps.map(e => {
          if (e.k !== 'extra' && e.k !== 'extrahalf') return e;
          const n = Object.assign({}, e, {p: Object.assign({}, e.p, {d: bump(e.p.d)})});
          if (e.pb) n.pb = Object.assign({}, e.pb, {d: bump(e.pb.d)});
          return n;
        });
      }
    } else if (k === 'critchance' || k === 'critdmg') {
      if (!a.g) { if (o.gearonly) continue; a.g = {cc: 0, cd: 0, bc: 0, bd: 0}; }
      a.pg = a.pg.concat([{k, v: k === 'critchance' ? v / 100 : v, s: scope === 'all' ? 'all' : scope, vs, vsnot}]);
    } else if (k === 'dmgfromblock') {
      if (a.g) a.pg = a.pg.concat([{k: 'dmgfromblock', v: v / 100, s: 'all', vs, vsnot}]);
    } else if (k === 'reuse') {
      if (spec) spec.p = spec.p.concat(clone(spec.p));
    }
  }
  return {a, spec};
}

/* the boss rules that change how much damage it takes */
function hitsOf(a, w) {
  let n = w.h;
  for (const e of (a.ps || [])) if (e.k === 'hits' && (e.s === 'all' || e.s === w.k)) n += e.v;
  return Math.max(n, 1);
}

function ruleFactor(a, w, boss, member) {
  let f = 1;
  if (boss.dim) {
    const [first, pct] = boss.dim;
    const n = hitsOf(a, w);
    let keep = 0, step = 1;
    for (let i = 1; i <= Math.round(n); i++) {
      if (i <= first) keep += 1;
      else { step *= 1 - pct / 100; keep += step; }
    }
    f *= keep / n;
  }
  if (boss.psy && member.tr.includes('Psyker')) f *= 1 - boss.psy / 100;
  if (boss.ramp && w.k === 'melee') {
    const n = hitsOf(a, w);
    f *= Math.max(1 - Math.min(boss.ramp / 100 * n / 2, 0.6), 0.4);
  }
  return f;
}

/* the opener: the turn a character gets its active off (build_map.opener) */
function openerDamage(a, spec, boss, trig) {
  const gx = spec.gx || null;
  let total = 0, bonusUsed = false;
  for (let i = 0; i < spec.p.length; i++) total += abilityHits(spec.p[i], boss, critOf(a, 'ability', i === 0, boss, trig, gx));
  const normal = override => {
    if (spec.flat && !bonusUsed) override = (override === null || override === undefined ? a.dmg : override) + spec.flat;
    const first = spec.p.length === 0 && !bonusUsed;
    let dmg = bestAttack(a, boss, trig, override, first, spec.weapon, gx).dmg;
    if (spec.bonus && !bonusUsed) dmg += abilityHits(spec.bonus, boss, critOf(a, 'ability', false, boss, trig, gx));
    bonusUsed = true;
    return dmg;
  };
  if (spec.normal === 'Y' || spec.normal === 'PCT')
    total += normal(spec.normal === 'PCT' ? Math.min(a.dmg * spec.pct, spec.cap || 1e9) : null);
  if (spec.same) total += normal(null);
  return total;
}


/* ---------------------------------------------------------------- a character over the fight */
/* the turns a character gets its active off; one that grows is held back as late as it can be */
function activeTurns(c, turns) {
  const late = c.rampPct !== undefined || c.rampFlat !== undefined;
  const out = new Set();
  if (c.cd === undefined) { out.add(late ? turns : 1); return out; }
  const step = c.cd + 1;
  if (late) { for (let t = turns; t > 0; t -= step) out.add(t); }
  else { for (let t = 1; t <= turns; t += step) out.add(t); }
  return out;
}

const rampAt = (c, turn) => (c.rampPct === undefined || turn <= 1) ? 1 : 1 + c.rampPct / 100 * (turn - 1);

/* the same multiplier on the hits a passive adds, which are damage the character deals too */
function scaleParts(x, mult) {
  if (mult === 1 || !x.ps || !x.ps.length) return x;
  return Object.assign({}, x, {ps: x.ps.map(e => {
    if (e.k !== 'extra' && e.k !== 'extrahalf') return e;
    const n = Object.assign({}, e, {p: Object.assign({}, e.p, {d: e.p.d * mult})});
    if (e.pb) n.pb = Object.assign({}, e.pb, {d: e.pb.d * mult});
    return n;
  })});
}

/* the parts of an active that change with the battle: Atlacoya's stacks, Sekhetar's extra hits */
function tweakSpec(c, spec, team, boss, turn, used) {
  if (!spec || !spec.p.length) return spec;
  if (c.rampFlat === undefined && !c.direct && c.psyCap === undefined) return spec;
  const parts = spec.p.map(p => Object.assign({}, p));
  if (c.psyCap !== undefined) {
    const n = team.filter(m => m.n !== c.n && m.w.some(w => w.t === 'Psychic' || w.t === 'Direct')).length;
    for (const p of parts) p.h = Math.min(p.h + n, c.psyCap);
  }
  if (c.rampFlat !== undefined) for (const p of parts) p.d += c.rampFlat * used;
  if (c.direct) {
    const trait = c.direct[0], faction = c.direct[1];
    if (boss.tr.includes(trait) || team.some(m => m.n !== c.n && m.f === faction)) for (const p of parts) p.t = 'Direct';
  }
  return Object.assign({}, spec, {p: parts});
}

/* one character's damage over the fighting rounds: the active turn plus normal attacks */
function memberDamage(D, member, mates, boss, extra, buff, teamUses, high) {
  const turns = D.turns, trig = D.setting.trig, immune = boss.tr.includes('Immune');
  let m = member;
  if (immune && (member.ps || []).some(e => e.k === 'armignore' || e.k === 'armpct'))
    m = Object.assign({}, member, {ps: member.ps.filter(e => e.k !== 'armignore' && e.k !== 'armpct')});
  const toks = buffsFor(m, mates, D, immune);
  const spec0 = m.sp || null, all = [m].concat(mates);
  const chaos = m.n === 'Laviscus' ? mates.filter(x => x.a === 'Chaos').length : 0;
  const hg = 1 + D.high.pct / 100;
  const actives = activeTurns(m, turns);

  const attack = (live, xtra, turn) => {
    const used = teamUses.filter(u => u < turn).length;
    const spec1 = tweakSpec(m, spec0, all, boss, turn, used);
    const out = live.length ? buffed(m, live, spec1) : {a: m, spec: spec1};
    let a = out.a, spec2 = out.spec;
    let plain = (live.length && spec1) ? buffed(m, live, null).a : a;
    const ramp = (m.rampPct !== undefined && actives.has(turn)) ? rampAt(m, turn) : 1;
    if (ramp !== 1) { a = scaleParts(a, ramp); plain = scaleParts(plain, ramp); }
    const dressed = x => {
      if (xtra) x = Object.assign({}, x, {dmg: x.dmg + xtra});
      if (high) { x = Object.assign({}, x, {dmg: x.dmg * hg}); x = scaleParts(x, hg); }
      if (chaos) x = Object.assign({}, x, {pg: (x.pg || []).concat(
        [{k: 'critdmg', v: (m.chaosCrit || 0) * chaos, s: 'all', vs: null, vsnot: null}])});
      return x;
    };
    a = dressed(a); plain = dressed(plain);
    const got = bestAttack(plain, boss, trig, null, false);
    let f = ruleFactor(plain, got.w, boss, m);
    if (buff && buff.k === 'taken' && (!buff.only || buff.only === got.w.k)) f *= 1 + buff.pct / 100;
    let first = 0;
    if (spec2) {
      if (high) spec2 = Object.assign({}, spec2, {p: spec2.p.map(p => Object.assign({}, p, {d: p.d * hg}))});
      first = openerDamage(a, spec2, boss, trig) * f;
    }
    return [got.dmg * f, first];
  };

  /* the turns fall into blocks: as each short buff runs out, work the attack out again */
  const grows = m.rampPct !== undefined || m.rampFlat !== undefined;
  const ups = [...new Set(toks.map(x => Math.min(x.up, turns)).concat([turns]))].sort((a, b) => a - b);
  const xs = Array.isArray(extra) ? extra : new Array(turns).fill(extra || 0);
  let total = 0, done = 0;
  const seen = new Map();
  for (const up of ups) {
    const live = toks.filter(x => x.up > done).map(x => x.t);
    for (let turn = done + 1; turn <= up; turn++) {
      const x = xs[Math.min(turn, xs.length) - 1];
      const key = done + '|' + Math.round(x) + '|' + (grows ? turn : 0);
      if (!seen.has(key)) seen.set(key, attack(live, x, turn));
      const nm = seen.get(key)[0], fs = seen.get(key)[1];
      total += (fs && actives.has(turn)) ? Math.max(fs, nm) : nm;
    }
    done = up;
  }
  return total;
}

/* this character's biggest single non-Psychic hit - what Laviscus's Outrage feeds on */
const _BIG = new Map();

function biggestHit(D, member, mates, boss, opener, turn, high) {
  const key = [member.n, mates.map(x => x.n).sort().join(','), opener ? 1 : 0, boss.id,
               member.rampPct !== undefined ? turn : 0, high ? 1 : 0].join('|');
  if (_BIG.has(key)) return _BIG.get(key);
  const v = _biggestHit(D, member, mates, boss, opener, turn, high);
  _BIG.set(key, v);
  return v;
}

function _biggestHit(D, member, mates, boss, opener, turn, high) {
  const trig = D.setting.trig, immune = boss.tr.includes('Immune');
  const toks = buffsFor(member, mates, D, immune).map(x => x.t);
  let spec = opener ? (member.sp || null) : null;
  if (spec) spec = tweakSpec(member, spec, [member].concat(mates), boss, turn, mates.length);
  const out = toks.length ? buffed(member, toks, spec) : {a: member, spec: spec};
  let a = out.a, spec2 = out.spec;
  const hg = high ? 1 + D.high.pct / 100 : 1;
  const mult = (member.rampPct !== undefined ? rampAt(member, turn) : 1) * hg;
  if (mult !== 1) {
    a = scaleParts(a, mult);
    if (high) a = Object.assign({}, a, {dmg: a.dmg * hg});
    if (spec2) spec2 = Object.assign({}, spec2, {p: spec2.p.map(p => Object.assign({}, p, {d: p.d * mult}))});
  }
  let best = 0;
  const crit = (a.g || {}).cc || 0;
  /* the weapon attack on its own: the hits a passive adds come in their own attack, weighed below */
  const plain = Object.assign({}, a, {ps: (a.ps || []).filter(e => e.k !== 'extra' && e.k !== 'extrahalf')});
  for (const w of plain.w) {
    if (w.t === 'Psychic') continue;
    const n = Math.max(hitsOf(plain, w), 1);
    let avg = bestAttack(plain, boss, trig, null, false, w.k).dmg / n;
    if (crit) {                    /* across an attack's hits the biggest is usually a crit */
      const hot = bestAttack(Object.assign({}, plain, {g: Object.assign({}, plain.g, {cc: 1})}),
                             boss, trig, null, false, w.k).dmg / n;
      const p = 1 - Math.pow(1 - crit, n);
      avg = p * hot + (1 - p) * avg;
    }
    best = Math.max(best, avg);
  }
  const parts = (a.ps || []).filter(e => e.k === 'extra' || e.k === 'extrahalf')
    .map(e => (e.pb && boss.tr.includes('BigTarget')) ? e.pb : e.p);
  if (spec2) for (const p of spec2.p) parts.push(p);
  const cr = critOf(a, 'ability', false, boss, trig);
  for (const p of parts) {
    if (p.t === 'Psychic') continue;
    best = Math.max(best, abilityHits(p, boss, cr) / Math.max(p.h, 1));
  }
  return best;
}

/* the biggest hit of a character's own active, for the turn it uses it */
function abilityHit(D, member, boss) {
  if (!member.sp) return 0;
  let best = 0;
  const cr = critOf(member, 'ability', false, boss, D.setting.trig);
  for (const p of member.sp.p) if (p.t !== 'Psychic') best = Math.max(best, abilityHits(p, boss, cr) / Math.max(p.h, 1));
  return best;
}

/* Laviscus: 120% of the sum of his team-mates' biggest hits, on each turn */
function outrage(D, member, team, boss, high) {
  const mates = team.filter(x => x.n !== member.n), pct = (member.outragePct || 0) / 100, out = [];
  const mine = activeTurns(member, D.turns);
  for (let turn = 1; turn <= D.turns; turn++) {
    let s = 0;
    for (const m of mates)
      s += biggestHit(D, m, team.filter(x => x.n !== m.n), boss,
                      activeTurns(m, D.turns).has(turn), turn, high.has(m.n));
    if (mine.has(turn)) s += abilityHit(D, member, boss);   /* Euphoric Strikes feeds it before he swings */
    out.push(pct * s);
  }
  return out;
}

/* the flat Damage a character brings into this team on each turn */
function memberExtra(D, m, team, boss, buff, high, teamUses) {
  const out = (m.n === 'Laviscus') ? outrage(D, m, team, boss, high) : new Array(D.turns).fill(0);
  let flat = 0;
  const neuro = team.find(x => x.n === 'Neurothrope');
  if (neuro) {
    if (m.n === 'Neurothrope') flat += neuro.parasite[0] * neuro.parasite[1];
    else if (m.tr.includes('Psyker') && neuro.crown) flat += neuro.crown;
  }
  if (buff && buff.k === 'dmg' && matches(m, buff.who)) flat += m.dmg * buff.pct / 100;
  const res = out.map(x => x + flat);
  if (m.rampTeam !== undefined)                      /* a stack for every active the team has used */
    for (let i = 0; i < res.length; i++) res[i] += m.rampTeam * teamUses.filter(u => u < i + 1).length;
  if (m.rampStack)                                   /* a stack a turn, up to the ability's cap */
    for (let i = 0; i < res.length; i++) res[i] += m.rampStack[0] * Math.min(i, m.rampStack[1]);
  return res;
}

/* what a character's summons add over the fight */
function summonDamage(D, m, team, boss) {
  if (!m.sum) return 0;
  const neuro = team.find(x => x.n === 'Neurothrope');
  const bonus = (neuro && neuro.crown) ? neuro.crown : 0;    /* the Crown names friendly Summons */
  let total = 0;
  for (const s of m.sum) {
    const rounds = Math.max(D.turns - (s.src === 'ability' ? 1 : 0), 0);
    let best = 0;
    for (const w of s.w) best = Math.max(best, abilityHits({d: s.d + bonus, h: w.h, t: w.t, c: false}, boss, null));
    total += s.n * best * rounds;
  }
  return total;
}

/* ---------------------------------------------------------------- the team */
const EMPTY = new Set();

function teamTotal(D, team, boss, mow, high) {
  const buff = mow ? mow.b : null;
  let uses = [];
  for (const m of team) uses = uses.concat([...activeTurns(m, D.turns)]);
  uses.sort((a, b) => a - b);
  const each = {}, args = {};
  for (const m of team) {
    const mates = team.filter(x => x.n !== m.n);
    const extra = memberExtra(D, m, team, boss, buff, EMPTY, uses);
    each[m.n] = memberDamage(D, m, mates, boss, extra, buff, uses, false) + summonDamage(D, m, team, boss);
    args[m.n] = mates;
  }
  let on = EMPTY;
  if (high) {
    /* the ones already doing the most damage take it, which is what the teams in the videos do */
    on = new Set(Object.keys(each).sort((a, b) => each[b] - each[a]).slice(0, D.high.n));
    for (const m of team) {
      if (!on.has(m.n) && m.n !== 'Laviscus') continue;
      const extra = memberExtra(D, m, team, boss, buff, on, uses);
      each[m.n] = memberDamage(D, m, args[m.n], boss, extra, buff, uses, on.has(m.n))
        + summonDamage(D, m, team, boss);
    }
  }
  const total = (mow ? mow.own : 0) + sum(Object.keys(each).map(k => each[k]));
  return {total: total, each: each, on: [...on]};
}

/* score the five the page's user picked: the Machine of War that adds the most, then the total */
function scoreTeam(D, names, fightIndex, opts) {
  opts = opts || {};
  const boss = D.bosses[fightIndex][opts.dbf ? 1 : 0];
  const team = names.map(n => D.by[n]).filter(Boolean);
  if (team.length !== names.length) return null;
  let mow = null, best = -Infinity;
  for (const mw of D.mows) {
    if (boss.mow[mw.n] === undefined) continue;             /* the boss's own faction is banned */
    const opt = {n: mw.n, b: mw.b, own: boss.mow[mw.n]};
    const got = teamTotal(D, team, boss, opt, false).total;
    if (got > best) { best = got; mow = opt; }
  }
  const out = teamTotal(D, team, boss, mow, !!opts.high);
  out.mow = mow ? mow.n : null;
  return out;
}

/* the page hands over the JSON calc_data.py built, once */
function load(data) {
  data.by = {};
  for (const c of data.chars) data.by[c.n] = c;
  data.bosses.forEach((both, i) => both.forEach((b, j) => { b.id = i + ':' + j; }));
  _BIG.clear();
  return data;
}

/* prove this agrees with guild_raid.py before anyone trusts a number it prints */
function check(D) {
  const bad = [];
  for (const v of D.vec) {
    const got = scoreTeam(D, v.t, v.f, {dbf: !!v.d, high: !!v.h});
    const err = got ? (got.total - v.s) / Math.max(v.s, 1) : 1;
    if (Math.abs(err) > 0.001) bad.push({v: v, got: got ? Math.round(got.total) : null, err: err});
  }
  return bad;
}

module.exports = {PIERCE, sum, prod, chain, hitValue, matches, applies, critOf, abilityHits, normalAttack,
  bestAttack, buffsFor, buffed, hitsOf, ruleFactor, openerDamage, TEAM_REACH,
  activeTurns, tweakSpec, memberDamage, biggestHit, outrage, memberExtra, summonDamage,
  teamTotal, scoreTeam, load, check};
