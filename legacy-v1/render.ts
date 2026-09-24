import { BIBLIOGRAPHY, CHAPTERS, CONCLUSION, DYNASTIES, KEY_DATES, MATRIX, SOURCES, THESIS, type Chapter } from "./content";

/* --------------------------------------------------------------------------
   Chicago notes: first citation of a source = full note, later = short form.
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

const $ = <T extends Element = HTMLElement>(sel: string, root: ParentNode = document) => root.querySelector(sel) as T;

/* -------------------------------------------------------------------------- */
function sceneMarkup(c: Chapter): string {
  const sizes = [960, 1600, 2560];
  const srcset = sizes.map((w) => `scenes/${c.scene}-${w}.webp ${w}w`).join(", ");
  return `
    <div class="scene" data-scene="${c.scene}">
      <img class="scene-img" loading="lazy" decoding="async" alt="${c.alt}" srcset="${srcset}" sizes="100vw" src="scenes/${c.scene}-1600.webp" />
      <canvas class="scene-gl" aria-hidden="true"></canvas>
      <div class="chapter-hanzi" aria-hidden="true">${c.hanzi}</div>
      <div class="scene-overlay">
        <div class="chapter-head">
          <span class="seal" aria-hidden="true">${c.letter}</span>
          <div>
            <p class="chapter-kicker">${c.name} <span class="cjk">${c.hanzi}</span> ${c.pinyin} · “${c.gloss}”</p>
            <h2 class="chapter-title">${c.title}</h2>
            <p class="chapter-idea">${c.bigIdea}</p>
          </div>
        </div>
      </div>
      <p class="scene-caption">${c.caption}</p>
    </div>`;
}

function devMarkup(c: Chapter): string {
  return c.developments
    .map(
      (d, i) => `
      <article class="dev reveal" id="${c.id}-${i + 1}">
        <div class="dev-top">
          <span class="seal dev-num" aria-hidden="true">${c.letter}${i + 1}</span>
          <h3>${d.title}</h3>
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
      </article>`,
    )
    .join("");
}

function artifactsMarkup(c: Chapter): string {
  if (!c.artifacts?.length) return "";
  const cols = c.artifacts.length > 1 ? 2 : 1;
  return `<div class="artifacts" style="--cols:${cols}">
    ${c.artifacts
      .map(
        (a, i) => `
      <figure class="artifact reveal ${c.artifacts!.length === 1 ? "artifact--wide" : i === 0 ? "" : "artifact--small"}" data-artifact="${a.kind}">
        <div class="artifact-stage">
          <div class="artifact-loading">Loading 3D model…</div>
        </div>
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
  return `<figure class="spotlight reveal">
    ${s.image ? `<img src="${s.image}" alt="${s.imageAlt ?? ""}" loading="lazy" decoding="async" />` : ""}
    <div>
      <p class="label">${s.kind}</p>
      <blockquote>“${s.quote}”</blockquote>
      <figcaption>${s.attribution}</figcaption>
    </div>
  </figure>`;
}

function chapterMarkup(c: Chapter): string {
  return `
  <section class="chapter" id="${c.id}" aria-labelledby="${c.id}-title" data-letter="${c.letter}">
    ${sceneMarkup(c).replace('class="chapter-title"', `class="chapter-title" id="${c.id}-title"`)}
    <div class="chapter-body paper">
      <div class="wrap">
        <div class="dev-grid">${devMarkup(c)}</div>
        ${artifactsMarkup(c)}
        ${spotlightMarkup(c)}
        <div class="synthesis reveal">
          <span class="seal" aria-hidden="true">${c.hanzi}</span>
          <div><p class="label">Why it matters · ${c.name}</p><p>${c.synthesis}</p></div>
        </div>
      </div>
    </div>
  </section>`;
}

/* -------------------------------------------------------------------------- */
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
        return `<div class="dyn-bar" data-tone="${it.tone}" style="left:${l}%;width:${w}%" title="${label}" aria-label="${label}">${w > 11 ? it.name : ""}</div>`;
      })
      .join("");
    return `<div class="dyn-row"><b>${r.row}</b><div class="dyn-track">${bars}</div></div>`;
  }).join("");
  return axis + rows;
}

function matrixRows(): string {
  return MATRIX.map((m) => {
    const ch = CHAPTERS.find((c) => c.letter === m.cat)!;
    return `<tr>
      <td><a href="#${ch.id}"><span class="seal seal--sm" style="font-family:var(--f-display);font-size:16px">${m.cat}</span></a></td>
      <td>${m.development}</td>
      <td class="proc">${m.process}</td>
      <td>${m.link}</td>
      <td>${m.cc}</td>
    </tr>`;
  }).join("");
}

function keyDates(): string {
  return KEY_DATES.map((d) => `<li class="reveal"><span class="y">${d.year}</span><span class="t">${d.text}</span><span class="c">${d.cat}</span></li>`).join("");
}

function rail(): string {
  return CHAPTERS.map(
    (c) => `<li><a class="rail-link" href="#${c.id}" data-target="${c.id}">${c.letter}<span class="rail-tip">${c.name} · ${c.title}</span></a></li>`,
  ).join("");
}

export function renderSite(): void {
  $("#thesis").innerHTML = THESIS;
  $("#dynasty-chart").innerHTML = dynastyChart();
  $("#chapters").innerHTML = CHAPTERS.map(chapterMarkup).join("");
  $("#matrix-table tbody").innerHTML = matrixRows();
  $("#keydates").innerHTML = keyDates();
  $("#conclusion-text").innerHTML = CONCLUSION;
  $("#rail-list").innerHTML = rail();
  $("#endnotes").innerHTML = notes
    .map((n, i) => `<li id="fn-${i + 1}">${n} <a class="back" href="#fnref-${i + 1}" aria-label="Back to reference ${i + 1}">↩</a></li>`)
    .join("");
  $("#bib").innerHTML = Object.keys(BIBLIOGRAPHY)
    .filter((k) => usedBib.has(k))
    .map((k) => `<li>${BIBLIOGRAPHY[k]}</li>`)
    .join("");
}

export function noteHtml(n: number): string {
  return notes[n - 1] ?? "";
}
