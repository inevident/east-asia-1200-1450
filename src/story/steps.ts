import type { Place } from "../world/geo";

/* ==========================================================================
   The tour: every scroll step names where the camera goes, which places are
   labelled, and which routes or arcs are drawn. Panel text comes from content.ts.
   Camera: target place, distance (world units, 1 = 10 km), pitch (deg above
   horizontal) and yaw (deg; 0 = looking north, positive = camera swung east).
   ========================================================================== */

export interface Cam {
  at: Place;
  d: number;
  pitch: number;
  yaw: number;
  /** shift from the place, in map units (x east, y north), to frame a particular part of a landmark */
  off?: [number, number];
}
export type LabelKind = "city" | "event" | "region" | "site" | "sea";
export interface Label {
  at: Place;
  text: string;
  sub?: string;
  kind?: LabelKind;
  /** which side of the marker the text sits on */
  dir?: "n" | "s" | "e" | "w";
  /** height of the marker above the ground (world units) */
  lift?: number;
}
export type RouteStyle = "land" | "sea" | "fleet" | "canal" | "war" | "idea" | "goods" | "plague";
export interface RouteRef {
  id: string;
  style: RouteStyle;
  /** "scroll" draws the line as the reader scrolls through the step */
  draw?: "scroll" | "full";
  /**
   * Part of the stop's locked stretch (0..1) during which the line draws. The camera reaches each place at these
   * points: one place 0.67 | two 0.35 (rests to 0.48), 0.83 | three 0.23 (0.33), 0.56 (0.65), 0.88 | four 0.18, 0.42, 0.67, 0.91.
   * Default: once the camera has reached the last place.
   */
  span?: [number, number];
}
export interface Arc {
  from: Place;
  to: Place;
  style: RouteStyle;
  /** height of the arc's apex as a fraction of its length */
  lift?: number;
  /** point in the stop's locked stretch (0..1) at which this arc starts drawing; default: when the camera has arrived */
  delay?: number;
}
export type MoverKind = "fleet" | "junks" | "caravan" | "barges";
export interface Mover {
  kind: MoverKind;
  route: string;
  /** follow the reader's scroll through the step, or loop continuously */
  mode: "scroll" | "loop";
  /** part of the stop's locked stretch during which a "scroll" mover travels its route */
  span?: [number, number];
}

export type StepKind = "hero" | "prologue" | "chapter" | "dev" | "synth" | "connections" | "outro";
export interface Step {
  id: string;
  kind: StepKind;
  chapter?: number;
  dev?: number;
  cams: Cam[];
  labels?: Label[];
  routes?: RouteRef[];
  arcs?: Arc[];
  movers?: Mover[];
  /** landmark ids (anchors) that should be in focus / lit */
  focus?: string[];
}

const cam = (at: Place, d: number, pitch = 45, yaw = 0, off?: [number, number]): Cam => ({ at, d, pitch, yaw, off });
const L = (at: Place, text: string, sub?: string, kind: LabelKind = "city", dir?: Label["dir"]): Label => ({ at, text, sub, kind, dir });
const R = (at: Place, text: string): Label => ({ at, text, kind: "region" });
const SEA = (at: Place, text: string): Label => ({ at, text, kind: "sea" });

// polities and seas, reused across steps
const REG = {
  song: R([115.5, 27.5], "Southern Song"),
  jin: R([114, 37.5], "Jin"),
  yuan: R([108, 36], "Yuan"),
  ming: R([112, 31], "Ming"),
  goryeo: R([127.4, 36.4], "Goryeo"),
  joseon: R([127.6, 36.2], "Joseon"),
  japan: R([137.6, 36.2], "Japan"),
  daiviet: R([105.2, 19.6], "Đại Việt"),
  champa: R([108.4, 14.2], "Champa"),
  steppe: R([103, 46], "Mongol steppe"),
  tibet: R([88, 32.5], "Tibet"),
  ilkhanate: R([52, 33], "Ilkhanate"),
  chagatai: R([72, 41.5], "Chagatai Khanate"),
  horde: R([58, 47.5], "Golden Horde"),
  islam: R([46, 28], "Dār al-Islām"),
  india: R([79, 22], "South Asia"),
};
const SEAS = {
  indian: SEA([78, 2], "Indian Ocean"),
  scs: SEA([114.5, 15.5], "South China Sea"),
  ecs: SEA([125.5, 29.5], "East China Sea"),
  japan: SEA([134, 40], "Sea of Japan"),
  yellow: SEA([123.5, 35.5], "Yellow Sea"),
  arabian: SEA([63, 15], "Arabian Sea"),
};

const INDIAN_OCEAN_PORTS: Label[] = [
  L("quanzhou", "Quanzhou", "“Zayton”", "city", "e"),
  L("guangzhou", "Guangzhou", undefined, "city", "w"),
  L("malacca", "Malacca", undefined, "city", "e"),
  L("calicut", "Calicut", undefined, "city", "e"),
  L("hormuz", "Hormuz", undefined, "city", "e"),
  L("aden", "Aden", undefined, "city", "s"),
  L("mogadishu", "Mogadishu", undefined, "city", "e"),
  L("malindi", "Malindi", undefined, "city", "e"),
];

export const STEPS: Step[] = [
  // ------------------------------------------------------------------ opening
  {
    id: "top",
    kind: "hero",
    cams: [cam([119, 31.5], 640, 52, -12)],
    labels: [REG.song, REG.jin, REG.goryeo, REG.japan, REG.daiviet, SEAS.ecs],
  },
  {
    id: "prologue",
    kind: "prologue",
    cams: [cam([92, 27], 1320, 60, 0)],
    labels: [REG.song, REG.jin, REG.goryeo, REG.japan, REG.daiviet, REG.champa, REG.steppe, REG.tibet, REG.islam, REG.india, SEAS.indian, SEAS.scs],
    routes: [
      { id: "silk", style: "land", draw: "scroll" },
      { id: "sea", style: "sea", draw: "scroll" },
      { id: "sea_west", style: "sea", draw: "scroll" },
      { id: "swahili", style: "sea", draw: "scroll" },
    ],
  },

  // ------------------------------------------------------------------ P · Political
  {
    id: "political",
    kind: "chapter",
    chapter: 0,
    cams: [cam([115, 33], 520, 55, -6)],
    labels: [REG.song, REG.jin, REG.goryeo, REG.japan, REG.daiviet],
  },
  {
    id: "political-1",
    kind: "dev",
    chapter: 0,
    dev: 0,
    cams: [cam([117.5, 32.5], 230, 50, -8), cam("hangzhou", 9.5, 34, -18, [-0.2, -0.1])],
    labels: [
      L("kaifeng", "Kaifeng", "Northern Song capital, to 1127", "city", "e"),
      L("hangzhou", "Lin’an (Hangzhou)", "Southern Song capital", "city", "e"),
      REG.song,
    ],
    focus: ["hangzhou"],
  },
  {
    id: "political-2",
    kind: "dev",
    chapter: 0,
    dev: 1,
    cams: [cam([98, 42], 900, 58, 0), cam([112, 42.5], 190, 50, 0), cam("dadu", 10.5, 38, 12)],
    labels: [
      REG.yuan,
      REG.chagatai,
      REG.ilkhanate,
      REG.horde,
      L("karakorum", "Karakorum", "Mongol capital before Khubilai", "city", "e"),
      L("shangdu", "Shangdu", "Khubilai’s summer capital", "city", "e"),
      L("dadu", "Dadu (Beijing)", "Yuan capital, 1271–1368", "city", "e"),
    ],
    routes: [{ id: "steppe", style: "land", draw: "scroll", span: [0.21, 0.34] }],
    focus: ["dadu"],
  },
  {
    id: "political-3",
    kind: "dev",
    chapter: 0,
    dev: 2,
    cams: [cam("nanjing", 11, 36, -10, [0, -0.3]), cam([86, 9], 1150, 62, 0)],
    labels: [
      L("nanjing", "Nanjing", "first Ming capital", "city", "w"),
      L("liujiagang", "Liujiagang", "the fleets assemble", "city", "e"),
      ...INDIAN_OCEAN_PORTS.filter((l) => l.at !== "quanzhou" && l.at !== "guangzhou"),
      SEAS.indian,
    ],
    routes: [{ id: "zhenghe", style: "fleet", draw: "scroll", span: [0.74, 0.97] }],
    movers: [{ kind: "fleet", route: "zhenghe", mode: "scroll", span: [0.74, 0.97] }],
    focus: ["nanjing", "liujiagang"],
  },
  {
    id: "political-4",
    kind: "dev",
    chapter: 0,
    dev: 3,
    cams: [cam([133.5, 35.2], 230, 50, -10), cam("hakata", 16, 36, 18), cam("bachdang", 14, 36, 10)],
    labels: [
      L("kamakura", "Kamakura", "shogun’s capital, 1185–1333", "city", "e"),
      L("kyoto", "Kyoto", "emperor’s court; Ashikaga shoguns", "city", "s"),
      L("hakata", "Hakata Bay", "Mongol landings, 1274 & 1281", "event", "e"),
      L("kaesong", "Kaesong", "Goryeo capital", "city", "w"),
      L("thanglong", "Thăng Long", "Trần capital", "city", "w"),
      L("bachdang", "Bạch Đằng River", "Mongol fleet wrecked, 1288", "event", "e"),
      REG.japan,
      REG.goryeo,
      REG.daiviet,
    ],
    routes: [
      { id: "invasion_japan", style: "war", draw: "scroll", span: [0.21, 0.34] },
      { id: "invasion_vietnam", style: "war", draw: "scroll", span: [0.86, 0.97] },
    ],
    focus: ["hakata", "bachdang", "kamakura"],
  },
  {
    id: "political-synth",
    kind: "synth",
    chapter: 0,
    cams: [cam([118, 30], 560, 56, 4)],
    labels: [REG.ming, REG.joseon, REG.japan, REG.daiviet],
  },

  // ------------------------------------------------------------------ I · Intellectual
  {
    id: "intellectual",
    kind: "chapter",
    chapter: 1,
    cams: [cam([118.5, 31], 380, 52, 8)],
  },
  {
    id: "intellectual-1",
    kind: "dev",
    chapter: 1,
    dev: 0,
    cams: [cam("bailudong", 9, 32, -12), cam([118, 30], 560, 56, 0)],
    labels: [
      L("bailudong", "White Deer Grotto Academy", "revived by Zhu Xi, 1179", "site", "e"),
      L("wuyi", "Wuyi Mountains", "where Zhu Xi taught", "site", "s"),
      L("hanseong", "Korea", undefined, "city", "e"),
      L("kyoto", "Japan", undefined, "city", "e"),
      L("thanglong", "Vietnam", undefined, "city", "w"),
    ],
    arcs: [
      { from: "bailudong", to: "hanseong", style: "idea", delay: 0.74 },
      { from: "bailudong", to: "kyoto", style: "idea", delay: 0.79 },
      { from: "bailudong", to: "thanglong", style: "idea", delay: 0.84 },
    ],
    focus: ["bailudong"],
  },
  {
    id: "intellectual-2",
    kind: "dev",
    chapter: 1,
    dev: 1,
    cams: [cam([121.5, 32.5], 330, 52, 0), cam("cheongju", 9, 34, 10)],
    labels: [
      L("jianyang", "Jianyang", "commercial woodblock printing", "site", "e"),
      L("hangzhou", "Hangzhou", undefined, "city", "e"),
      L("cheongju", "Cheongju", "Jikji printed with metal type, 1377", "event", "e"),
    ],
    arcs: [{ from: "hangzhou", to: "cheongju", style: "idea", delay: 0.33 }],
    focus: ["cheongju"],
  },
  {
    id: "intellectual-3",
    kind: "dev",
    chapter: 1,
    dev: 2,
    cams: [cam([82, 38], 1000, 55, 0), cam("dadu", 8, 34, -30, [0.8, -0.9])],
    labels: [
      L("maragheh", "Maragheh", "Ilkhanate observatory, 1259", "event", "e"),
      L("dadu", "Dadu (Beijing)", "Khubilai’s observatory", "event", "e"),
      REG.ilkhanate,
      REG.yuan,
    ],
    arcs: [{ from: "maragheh", to: "dadu", style: "idea", lift: 0.12, delay: 0.33 }],
    focus: ["maragheh", "dadu"],
  },
  {
    id: "intellectual-4",
    kind: "dev",
    chapter: 1,
    dev: 3,
    cams: [cam("hanseong", 9, 34, -6)],
    labels: [L("hanseong", "Hanseong (Seoul)", "Joseon capital · Hangul, 1443", "city", "e"), REG.joseon],
    focus: ["hanseong"],
  },
  {
    id: "intellectual-synth",
    kind: "synth",
    chapter: 1,
    cams: [cam([116, 33], 600, 56, 0)],
  },

  // ------------------------------------------------------------------ R · Religious
  {
    id: "religious",
    kind: "chapter",
    chapter: 2,
    cams: [cam([124, 33], 420, 52, 6)],
  },
  {
    id: "religious-1",
    kind: "dev",
    chapter: 2,
    dev: 0,
    cams: [cam([127, 33.5], 330, 52, 0)],
    labels: [
      L("hangzhou", "Hangzhou", "Chan monasteries", "city", "w"),
      L("ningbo", "Ningbo", "port for Korea & Japan", "city", "e"),
      L("kaesong", "Goryeo", undefined, "city", "w"),
      L("kamakura", "Kamakura", "Zen for the samurai", "city", "e"),
      L("kyoto", "Kyoto", undefined, "city", "s"),
      SEAS.ecs,
    ],
    arcs: [
      { from: "ningbo", to: "kaesong", style: "idea", delay: 0.64 },
      { from: "ningbo", to: "hakata", style: "idea", delay: 0.69 },
      { from: "hakata", to: "kamakura", style: "idea", delay: 0.76 },
    ],
  },
  {
    id: "religious-2",
    kind: "dev",
    chapter: 2,
    dev: 1,
    cams: [cam("ganghwa", 22, 42, -10), cam("haeinsa", 6.5, 32, 24, [0, 0.1])],
    labels: [
      L("ganghwa", "Ganghwa Island", "Goryeo court in refuge, 1232–70", "city", "w"),
      L("haeinsa", "Haeinsa Temple", "home of the 80,000 blocks", "site", "e"),
    ],
    focus: ["haeinsa"],
  },
  {
    id: "religious-3",
    kind: "dev",
    chapter: 2,
    dev: 2,
    cams: [cam("village", 6.5, 30, -24, [0.05, 0.15])],
    labels: [L("village", "A lineage village", "ancestral hall & graves", "site", "e")],
    focus: ["village"],
  },
  {
    id: "religious-4",
    kind: "dev",
    chapter: 2,
    dev: 3,
    cams: [cam("quanzhou", 9, 34, 12, [0.2, -0.3]), cam([103, 31], 820, 56, 0)],
    labels: [
      L("quanzhou", "Quanzhou", "mosques, temples & churches", "city", "e"),
      L("sakya", "Sakya", "seat of the ʼPhags-pa Lama", "site", "e"),
      L("dadu", "Dadu", "Yuan court", "city", "e"),
      REG.tibet,
    ],
    arcs: [{ from: "sakya", to: "dadu", style: "idea", delay: 0.8 }],
    focus: ["quanzhou", "sakya"],
  },
  {
    id: "religious-synth",
    kind: "synth",
    chapter: 2,
    cams: [cam([118, 33], 520, 56, 0)],
  },

  // ------------------------------------------------------------------ A · Artistic
  {
    id: "artistic",
    kind: "chapter",
    chapter: 3,
    cams: [cam("hangzhou", 38, 32, -34)],
  },
  {
    id: "artistic-1",
    kind: "dev",
    chapter: 3,
    dev: 0,
    cams: [cam("hangzhou", 5.5, 20, -48, [-1.15, 0.05])],
    labels: [L("hangzhou", "West Lake, Lin’an", "the Southern Song court", "site", "e")],
    focus: ["hangzhou"],
  },
  {
    id: "artistic-2",
    kind: "dev",
    chapter: 3,
    dev: 1,
    cams: [cam("jingdezhen", 8.5, 34, 8, [0.2, 0]), cam([84, 22], 1150, 60, 0)],
    labels: [
      L("jingdezhen", "Jingdezhen", "the porcelain capital", "city", "e"),
      L("kashan", "Kashan", "cobalt blue", "city", "e"),
      L("quanzhou", "Quanzhou", undefined, "city", "e"),
      L("hormuz", "Hormuz", undefined, "city", "e"),
      L("cairo", "Cairo", undefined, "city", "e"),
      L("calicut", "Calicut", undefined, "city", "e"),
    ],
    arcs: [
      { from: "kashan", to: "jingdezhen", style: "goods", lift: 0.1, delay: 0.74 },
      { from: "jingdezhen", to: "quanzhou", style: "goods", lift: 0.25, delay: 0.8 },
    ],
    routes: [
      { id: "sea", style: "sea", draw: "scroll", span: [0.84, 0.97] },
      { id: "sea_west", style: "sea", draw: "scroll", span: [0.84, 0.97] },
    ],
    focus: ["jingdezhen"],
  },
  {
    id: "artistic-3",
    kind: "dev",
    chapter: 3,
    dev: 2,
    cams: [cam("kyoto", 4.2, 24, 20, [0.1, 0.0])],
    labels: [{ ...L("kyoto", "Kinkaku, the Golden Pavilion", "Kyoto, 1397", "site", "e"), lift: 0.35 }],
    focus: ["kyoto"],
  },
  {
    id: "artistic-synth",
    kind: "synth",
    chapter: 3,
    cams: [cam("jingdezhen", 26, 38, -20)],
  },

  // ------------------------------------------------------------------ T · Technological
  {
    id: "technological",
    kind: "chapter",
    chapter: 4,
    cams: [cam([113, 29], 520, 55, 0)],
  },
  {
    id: "technological-1",
    kind: "dev",
    chapter: 4,
    dev: 0,
    cams: [cam([113, 22], 470, 52, 0), cam("terraces", 7.5, 32, 20)],
    labels: [
      L("champa", "Champa", "fast-ripening rice", "city", "e"),
      L([119.2, 32.9], "Lower Yangzi & Huai", "Champa rice planted by 1012", "event", "e"),
      L("terraces", "Terraced hills", undefined, "site", "e"),
      REG.champa,
    ],
    arcs: [{ from: "champa", to: [119.2, 32.9], style: "goods", lift: 0.2, delay: 0.33 }],
    focus: ["terraces"],
  },
  {
    id: "technological-2",
    kind: "dev",
    chapter: 4,
    dev: 1,
    cams: [cam("kaifeng", 10, 36, -6), cam([84, 36], 1100, 56, 0)],
    labels: [
      L("kaifeng", "Kaifeng", "Wujing zongyao, 1044", "event", "e"),
      L("karakorum", "Mongols", undefined, "city", "e"),
      L("samarkand", "Central Asia", undefined, "city", "e"),
      L("baghdad", "Middle East", undefined, "city", "e"),
    ],
    arcs: [
      { from: "kaifeng", to: "karakorum", style: "war", lift: 0.2, delay: 0.74 },
      { from: "karakorum", to: "samarkand", style: "war", lift: 0.12, delay: 0.8 },
      { from: "samarkand", to: "baghdad", style: "war", lift: 0.12, delay: 0.86 },
    ],
    focus: ["kaifeng"],
  },
  {
    id: "technological-3",
    kind: "dev",
    chapter: 4,
    dev: 2,
    cams: [cam("quanzhou", 9, 20, 60, [1.8, -1.4])],
    labels: [L("quanzhou", "Quanzhou", "junks bound for the Indian Ocean", "city", "e"), SEAS.scs],
    movers: [{ kind: "junks", route: "sea", mode: "loop" }],
    focus: ["quanzhou"],
  },
  {
    id: "technological-4",
    kind: "dev",
    chapter: 4,
    dev: 3,
    cams: [cam("iron", 7, 32, -14)],
    labels: [L("iron", "Northern ironworks", "~125,000 tons a year by 1078", "site", "e"), L("kaifeng", "Kaifeng", undefined, "city", "e")],
    focus: ["iron"],
  },
  {
    id: "technological-synth",
    kind: "synth",
    chapter: 4,
    cams: [cam("quanzhou", 26, 28, 50, [1.0, -1.0])],
    movers: [{ kind: "junks", route: "sea", mode: "loop" }],
  },

  // ------------------------------------------------------------------ E · Economic
  {
    id: "economic",
    kind: "chapter",
    chapter: 5,
    cams: [cam([114, 32], 470, 54, -4)],
  },
  {
    id: "economic-1",
    kind: "dev",
    chapter: 5,
    dev: 0,
    cams: [cam("chengdu", 14, 38, 0), cam("dadu", 14, 40, 8), cam([78, 38], 1050, 56, 0)],
    labels: [
      L("chengdu", "Chengdu, Sichuan", "Song paper money", "city", "e"),
      L("dadu", "Dadu", "Yuan paper currency", "city", "e"),
      L("tabriz", "Tabriz", "Ilkhanate paper money fails, 1294", "event", "e"),
    ],
    arcs: [{ from: "dadu", to: "tabriz", style: "goods", lift: 0.1, delay: 0.84 }],
    focus: ["chengdu", "dadu"],
  },
  {
    id: "economic-2",
    kind: "dev",
    chapter: 5,
    dev: 1,
    cams: [cam("hangzhou", 14, 36, -24, [0.1, 1.2]), cam("yangzhou", 16, 38, -22), cam("linqing", 16, 38, -22), cam("dadu", 14, 38, -18, [-0.3, 0.4])],
    labels: [
      L("hangzhou", "Hangzhou", "southern end", "city", "e"),
      L("yangzhou", "Yangzhou", "crossing the Yangzi", "city", "e"),
      L("linqing", "Linqing", undefined, "city", "e"),
      L("dadu", "Dadu", "northern end", "city", "e"),
    ],
    routes: [{ id: "canal", style: "canal", draw: "scroll", span: [0.05, 0.9] }],
    movers: [{ kind: "barges", route: "canal", mode: "scroll", span: [0.05, 0.9] }],
    focus: ["hangzhou", "dadu"],
  },
  {
    id: "economic-3",
    kind: "dev",
    chapter: 5,
    dev: 2,
    cams: [cam("quanzhou", 9, 32, 18, [0.4, -0.5]), cam([88, 10], 1150, 62, 0)],
    labels: [...INDIAN_OCEAN_PORTS, L("cairo", "Cairo", undefined, "city", "e"), SEAS.indian, SEAS.arabian],
    routes: [
      { id: "sea", style: "sea", draw: "scroll", span: [0.74, 0.97] },
      { id: "sea_west", style: "sea", draw: "scroll", span: [0.74, 0.97] },
      { id: "swahili", style: "sea", draw: "scroll", span: [0.74, 0.97] },
    ],
    movers: [{ kind: "junks", route: "sea", mode: "loop" }],
    focus: ["quanzhou"],
  },
  {
    id: "economic-4",
    kind: "dev",
    chapter: 5,
    dev: 3,
    cams: [cam("dunhuang", 170, 48, 0), cam([76, 40], 950, 56, 0)],
    labels: [
      L("dadu", "Dadu", undefined, "city", "e"),
      L("karakorum", "Karakorum", undefined, "city", "e"),
      L("dunhuang", "Dunhuang", undefined, "city", "s"),
      L("kashgar", "Kashgar", undefined, "city", "s"),
      L("samarkand", "Samarkand", undefined, "city", "s"),
      L("bukhara", "Bukhara", undefined, "city", "w"),
      L("tabriz", "Tabriz", undefined, "city", "e"),
      L("baghdad", "Baghdad", undefined, "city", "s"),
    ],
    routes: [
      { id: "silk", style: "land", draw: "scroll", span: [0.5, 0.95] },
      { id: "steppe", style: "land", draw: "scroll", span: [0.5, 0.95] },
    ],
    movers: [{ kind: "caravan", route: "silk", mode: "scroll", span: [0.5, 0.95] }],
    focus: ["dunhuang"],
  },
  {
    id: "economic-synth",
    kind: "synth",
    chapter: 5,
    cams: [cam([100, 30], 1000, 58, 0)],
    routes: [
      { id: "silk", style: "land", draw: "full" },
      { id: "sea", style: "sea", draw: "full" },
      { id: "canal", style: "canal", draw: "full" },
    ],
  },

  // ------------------------------------------------------------------ S · Social
  {
    id: "social",
    kind: "chapter",
    chapter: 6,
    cams: [cam([117.5, 29], 300, 46, 0)],
  },
  {
    id: "social-1",
    kind: "dev",
    chapter: 6,
    dev: 0,
    cams: [cam("village", 6, 28, 14, [0.05, 0.2])],
    labels: [L("village", "Farming village", "one lineage, one ancestral hall", "site", "e")],
    focus: ["village"],
  },
  {
    id: "social-2",
    kind: "dev",
    chapter: 6,
    dev: 1,
    cams: [cam("hangzhou", 8, 32, 36, [0.1, 0.2])],
    labels: [L("hangzhou", "Lin’an (Hangzhou)", "Song capital of elite households", "city", "e")],
    focus: ["hangzhou"],
  },
  {
    id: "social-3",
    kind: "dev",
    chapter: 6,
    dev: 2,
    cams: [cam([118.2, 27.6], 210, 50, 0)],
    labels: [
      L("bailudong", "Scholars", "academies & examinations", "event", "w"),
      L("village", "Farmers", "rice villages", "event", "e"),
      L("jingdezhen", "Artisans", "the kilns", "event", "s"),
      L("quanzhou", "Merchants", "the ports", "event", "e"),
    ],
    focus: ["bailudong", "village", "jingdezhen", "quanzhou"],
  },
  {
    id: "social-4",
    kind: "dev",
    chapter: 6,
    dev: 3,
    cams: [cam("hangzhou", 120, 45, 0), cam([92, 36], 1150, 58, 0)],
    labels: [
      L("kaifeng", "Kaifeng", "Northern Song, to 1127", "city", "e"),
      L("hangzhou", "Hangzhou", "the court flees south, 1127", "event", "e"),
      L("samarkand", "Central Asia", undefined, "city", "e"),
      L("kaffa", "to the Black Sea", undefined, "city", "e"),
    ],
    arcs: [
      { from: "kaifeng", to: "hangzhou", style: "war", lift: 0.25, delay: 0.34 },
      { from: "samarkand", to: "dadu", style: "plague", lift: 0.1, delay: 0.8 },
      { from: "samarkand", to: "kaffa", style: "plague", lift: 0.1, delay: 0.85 },
    ],
    routes: [{ id: "silk", style: "plague", draw: "scroll", span: [0.76, 0.97] }],
  },
  {
    id: "social-synth",
    kind: "synth",
    chapter: 6,
    cams: [cam([117, 30], 420, 50, 0)],
  },

  // ------------------------------------------------------------------ closing
  {
    id: "connections",
    kind: "connections",
    cams: [cam([95, 26], 1320, 62, 0)],
    routes: [
      { id: "silk", style: "land", draw: "full" },
      { id: "steppe", style: "land", draw: "full" },
      { id: "sea", style: "sea", draw: "full" },
      { id: "sea_west", style: "sea", draw: "full" },
      { id: "swahili", style: "sea", draw: "full" },
      { id: "zhenghe", style: "fleet", draw: "full" },
      { id: "canal", style: "canal", draw: "full" },
    ],
    labels: [REG.ming, REG.joseon, REG.japan, REG.daiviet, REG.islam, REG.india, SEAS.indian],
  },
  {
    id: "conclusion",
    kind: "outro",
    cams: [cam([119, 31.5], 700, 52, 12)],
  },
];
