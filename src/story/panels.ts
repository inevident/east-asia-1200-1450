import { BIBLIOGRAPHY, CHAPTERS, CONCLUSION, DYNASTIES, KEY_DATES, MATRIX, SOURCES, THESIS, type Chapter } from "../content";
import { STEPS, type Step } from "./steps";

/* --------------------------------------------------------------------------
   Chicago notes: first citation of a source = full note, later = short form.
   Notes are numbered in reading order as the panels are built.
   -------------------------------------------------------------------------- */
const notes: string[] = [];
const seen = new Set<string>();
const usedBib = new Set<string>();

function cite(token: string): string {
  const parts = token.split("|").map((p) => {
    const [id, ...rest] = p.split(":");
    return { id: id.trim(), loc: rest.join(":").trim() || undefined };
  });
  const texts = parts.map(({ id, loc }) => {
    const src = SOURCES[id];
    if (!src) throw new Error(`Unknown source "${id}"`);
    const first = !seen.has(id);
    seen.add(id);
    usedBib.add(src.bibKey);
    return first ? src.full(loc) : src.short(loc);
  });
  const joined = texts.map((t, i) => (i < texts.length - 1 ? t.replace(/\.(<\/a>)?$/, "$1") : t)).join("; ");
  notes.push(joined);
  const n = notes.length;
  return `<sup class="fn" id="fnref-${n}"><a href="#fn-${n}" data-fn="${n}" aria-label="Note ${n}">${n}</a></sup>`;
}

const withNotes = (html: string) => html.replace(/\{\{([^}]+)\}\}/g, (_, t: string) => cite(t));

export function noteHtml(n: number): string {
  return notes[n - 1] ?? "";
}

/* -------------------------------------------------------------------------- */
const scene = (c: Chapter | "hero", w = 1600) => `scenes/${c === "hero" ? "hero" : c.scene}-${w}.webp`;

function srcset(slug: string) {
  return [960, 1600, 2560].map((w) => `scenes/${slug}-${w}.webp ${w}w`).join(", ");
}

function chapterCard(c: Chapter, i: number): string {
  return `
  <article class="card card--chapter" aria-labelledby="${c.id}-title">
    <figure class="painting">
      <img loading="lazy" decoding="async" alt="${c.alt}" srcset="${srcset(c.scene)}" sizes="(max-width: 760px) 92vw, 520px" src="${scene(c)}" />
      <figcaption>${c.caption} Rendered in Blender.</figcaption>
    </figure>
    <div class="chapter-head">
      <span class="seal seal--lg" aria-hidden="true">${c.letter}</span>
      <div>
        <p class="kicker">Chapter ${i + 1} of 7 · ${c.name} <span class="cjk" lang="zh-Hant">${c.hanzi}</span> <i>${c.pinyin}</i>, “${c.gloss}”</p>
        <h2 class="chapter-title" id="${c.id}-title">${c.title}</h2>
      </div>
    </div>
    <p class="chapter-idea">${c.bigIdea}</p>
    <p class="hint">Scroll to fly to ${c.developments.length} places on the map.</p>
  </article>`;
}

function devCard(c: Chapter, i: number): string {
  const d = c.developments[i];
  return `
  <article class="card card--dev" aria-labelledby="${c.id}-${i + 1}-title">
    <div class="dev-top">
      <span class="seal dev-num" aria-hidden="true">${c.letter}${i + 1}</span>
      <div>
        <p class="kicker">${c.name} · ${i + 1} of ${c.developments.length}</p>
        <h3 id="${c.id}-${i + 1}-title">${d.title}</h3>
      </div>
    </div>
    <p class="dev-meta"><span>${d.when}</span><span>${d.where}</span></p>
    <div class="dev-body"><p>${withNotes(d.body)}</p></div>
    <div class="conn">
      <div class="conn-head">
        <span class="conn-title">Global connection</span>
        ${d.process.map((p) => `<span class="chip">${p}</span>`).join("")}
      </div>
      <p>${withNotes(d.connection)}</p>
    </div>
  </article>`;
}

function artifactsMarkup(c: Chapter): string {
  if (!c.artifacts?.length) return "";
  return `<div class="artifacts">
    ${c.artifacts
      .map(
        (a) => `
      <figure class="artifact" data-artifact="${a.kind}">
        <div class="artifact-stage"><div class="artifact-loading">Loading 3D model…</div></div>
        <figcaption class="artifact-info">
          <p class="label">Interactive 3D · built in Blender</p>
          <h4>${a.title}</h4>
          <p>${a.blurb}</p>
        </figcaption>
      </figure>`,
      )
      .join("")}
  </div>`;
}

function spotlightMarkup(c: Chapter): string {
  const s = c.spotlight;
  if (!s) return "";
  return `<figure class="spotlight">
    ${s.image ? `<img src="${s.image}" alt="${s.imageAlt ?? ""}" loading="lazy" decoding="async" />` : ""}
    <div>
      <p class="label">${s.kind}</p>
      <blockquote>“${s.quote}”</blockquote>
      <figcaption>${s.attribution}</figcaption>
    </div>
  </figure>`;
}

function synthCard(c: Chapter): string {
  return `
  <article class="card card--synth">
    <div class="synthesis">
      <span class="seal" aria-hidden="true" lang="zh-Hant">${c.hanzi}</span>
      <div><p class="label">Why it matters · ${c.name}</p><p>${c.synthesis}</p></div>
    </div>
    ${spotlightMarkup(c)}
    ${artifactsMarkup(c)}
  </article>`;
}

function dynastyChart(): string {
  const Y0 = 1180,
    Y1 = 1450,
    span = Y1 - Y0;
  const pct = (y: number) => ((Math.min(Math.max(y, Y0), Y1) - Y0) / span) * 100;
  const ticks = [1200, 1250, 1300, 1350, 1400, 1450];
  const axis = `<div class="dyn-axis">${ticks.map((t) => `<span style="left:${pct(t)}%">${t}</span>`).join("")}</div>`;
  const rows = DYNASTIES.map((r) => {
    const bars = r.items
      .filter((it) => it.to > Y0 && it.from < Y1)
      .map((it) => {
        const l = pct(it.from),
          w = pct(it.to) - l;
        const label = `${it.name} (${it.from}–${it.to})${it.note ? ` — ${it.note}` : ""}`;
        return `<div class="dyn-bar" data-tone="${it.tone}" style="left:${l}%;width:${w}%" title="${label}" aria-label="${label}">${w > 13 ? it.name : ""}</div>`;
      })
      .join("");
    return `<div class="dyn-row"><b>${r.row}</b><div class="dyn-track">${bars}</div></div>`;
  }).join("");
  return axis + rows;
}

const LEGEND = `
  <ul class="legend" aria-label="Map key">
    <li><i class="sw sw--land"></i>Silk Roads (overland)</li>
    <li><i class="sw sw--sea"></i>Indian Ocean sea lanes</li>
    <li><i class="sw sw--fleet"></i>Zheng He’s voyages</li>
    <li><i class="sw sw--canal"></i>Grand Canal</li>
    <li><i class="sw sw--idea"></i>Ideas &amp; beliefs spreading</li>
    <li><i class="sw sw--goods"></i>Goods &amp; crops moving</li>
    <li><i class="sw sw--war"></i>Armies &amp; invasions</li>
  </ul>`;

function prologueCard(): string {
  return `
  <article class="card card--prologue" aria-labelledby="prologue-title">
    <p class="kicker">Thesis</p>
    <h2 id="prologue-title">Continuity at home, connection abroad</h2>
    <p class="thesis">${THESIS}</p>
    <div class="dyn">
      <p class="label">Who ruled, 1200–1450</p>
      <div class="dyn-chart">${dynastyChart()}</div>
    </div>
    <div class="howto">
      <p class="label">How to read the map</p>
      <p>Keep scrolling and the camera flies to each place. Labels mark real locations, and the landmarks on the map are miniatures modeled in Blender. Superscript numbers open the Chicago-style notes.</p>
      ${LEGEND}
    </div>
  </article>`;
}

function matrixCard(): string {
  const rows = MATRIX.map((m) => {
    const ch = CHAPTERS.find((c) => c.letter === m.cat)!;
    return `<tr>
      <td><a href="#${ch.id}" aria-label="${ch.name}"><span class="seal seal--sm">${m.cat}</span></a></td>
      <td>${m.development}</td>
      <td class="proc">${m.process}</td>
      <td>${m.link}</td>
      <td>${m.cc}</td>
    </tr>`;
  }).join("");
  return `
  <article class="card card--wide" aria-labelledby="connections-title">
    <p class="kicker">Synthesis</p>
    <h2 id="connections-title">Connections across PIRATES</h2>
    <p>Every category ties East Asia to the same global processes: <strong>trade networks</strong>, <strong>state building</strong> and <strong>cultural exchange and diffusion</strong>. All of the routes from the tour are drawn on the map behind this table.</p>
    <div class="matrix-wrap">
      <table class="matrix">
        <thead><tr><th scope="col">Cat.</th><th scope="col">Key developments</th><th scope="col">Global process</th><th scope="col">Link to the wider world</th><th scope="col">Continuity or change?</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  </article>`;
}

function outroCard(): string {
  return `
  <article class="card card--outro" aria-labelledby="conclusion-title">
    <p class="kicker">Conclusion</p>
    <h2 id="conclusion-title">A shared inheritance, adapted</h2>
    <p>${CONCLUSION}</p>
    <a class="btn" href="#timeline">Timeline, notes &amp; bibliography ↓</a>
  </article>`;
}

function heroMarkup(): string {
  return `
  <div class="hero-paint" aria-hidden="true">
    <img alt="" fetchpriority="high" srcset="${srcset("hero")}" sizes="100vw" src="${scene("hero")}" />
  </div>
  <div class="hero-inner">
    <p class="kicker">AP World History: Modern · Unit 1 · The Global Tapestry</p>
    <h1 class="hero-title"><span class="hero-title__main">East Asia</span><span class="hero-title__years">c. 1200 – 1450</span></h1>
    <p class="hero-sub">Song, Yuan &amp; early Ming China · Goryeo &amp; Joseon Korea · Kamakura &amp; Muromachi Japan · Đại Việt. A flight across a 3D map through <strong>P·I·R·A·T·E·S</strong>: continuity at home, connection abroad.</p>
    <p class="hero-byline"><span class="seal seal--sm" aria-hidden="true">林</span> Ryan Lim</p>
    <a class="scroll-cue" href="#prologue"><span>Scroll to begin the flight</span><i aria-hidden="true"></i></a>
  </div>
  <p class="hero-caption">Opening painting: Lin’an (Hangzhou) at dawn, a pagoda above the Qiantang River with junks bound for the Indian Ocean. Rendered in Blender.</p>`;
}

function stepMarkup(s: Step, idx: number): string {
  let inner = "";
  let cls = s.kind;
  switch (s.kind) {
    case "hero":
      inner = heroMarkup();
      break;
    case "prologue":
      inner = prologueCard();
      break;
    case "chapter":
      inner = chapterCard(CHAPTERS[s.chapter!], s.chapter!);
      break;
    case "dev":
      inner = devCard(CHAPTERS[s.chapter!], s.dev!);
      break;
    case "synth":
      inner = synthCard(CHAPTERS[s.chapter!]);
      break;
    case "connections":
      inner = matrixCard();
      cls = "connections";
      break;
    case "outro":
      inner = outroCard();
      break;
  }
  const letter = s.chapter !== undefined ? CHAPTERS[s.chapter].letter : "";
  const tall = s.cams.length > 1 ? ` style="--keys:${s.cams.length}"` : "";
  return `<section class="step step--${cls}" id="${s.id}" data-step="${idx}" data-letter="${letter}"${tall}>${inner}</section>`;
}

function keyDates(): string {
  return KEY_DATES.map((d) => `<li><span class="y">${d.year}</span><span class="t">${d.text}</span><span class="c">${d.cat}</span></li>`).join("");
}

function rail(): string {
  return CHAPTERS.map(
    (c) => `<li><a class="rail-link" href="#${c.id}" data-target="${c.id}" data-letter="${c.letter}">${c.letter}<span class="rail-tip">${c.name} · ${c.title}</span></a></li>`,
  ).join("");
}

export function renderSite(): void {
  const $ = (sel: string) => document.querySelector(sel) as HTMLElement;
  $("#story").innerHTML = STEPS.map(stepMarkup).join("");
  $("#keydates").innerHTML = keyDates();
  $("#dynasty-chart-full").innerHTML = dynastyChart();
  $("#rail-list").innerHTML = rail();
  $("#endnotes").innerHTML = notes
    .map((n, i) => `<li id="fn-${i + 1}">${n} <a class="back" href="#fnref-${i + 1}" aria-label="Back to reference ${i + 1}">↩</a></li>`)
    .join("");
  $("#bib").innerHTML = Object.keys(BIBLIOGRAPHY)
    .filter((k) => usedBib.has(k))
    .map((k) => `<li>${BIBLIOGRAPHY[k]}</li>`)
    .join("");
}
