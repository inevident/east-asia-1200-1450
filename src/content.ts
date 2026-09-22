/* ==========================================================================
   Content — East Asia, c. 1200–c. 1450, organised with the PIRATES framework.
   Footnote tokens:  {{sourceId:locator|otherId:locator}}  -> one Chicago note.
   The renderer numbers notes in reading order, prints the full citation the
   first time a source appears and the shortened form after that.
   ========================================================================== */

const ACCESSED = "accessed September 25, 2026";
const ACCESSED_BIB = "Accessed September 25, 2026";

export interface Source {
  full: (loc?: string) => string;
  short: (loc?: string) => string;
  bibKey: string; // several notes can share one bibliography entry
}

const withLoc = (s: string, loc?: string) => (loc ? `${s}, ${loc}.` : `${s}.`);

const afeSong = (title: string, url: string): Source => ({
  full: (loc) =>
    withLoc(
      `“${title},” in <i>China in 1000 CE: The Most Advanced Society in the World</i>, Asia for Educators, Columbia University, ${ACCESSED}, <a href="${url}">${url}</a>`,
      loc,
    ),
  short: (loc) => (loc ? `“${title},” ${loc}.` : `“${title}.”`),
  bibKey: "afe_song",
});

const afeMongols = (title: string, url: string): Source => ({
  full: (loc) =>
    withLoc(
      `“${title},” in <i>The Mongols in World History</i>, Asia for Educators, Columbia University, ${ACCESSED}, <a href="${url}">${url}</a>`,
      loc,
    ),
  short: () => `“${title}.”`,
  bibKey: "afe_mongols",
});

const web = (lead: string, title: string, url: string, shortForm: string, bibKey: string): Source => ({
  full: (loc) => withLoc(`${lead}“${title},” ${ACCESSED}, <a href="${url}">${url}</a>`, loc),
  short: (loc) => (loc ? `${shortForm}, ${loc}.` : `${shortForm}.`),
  bibKey,
});

export const SOURCES: Record<string, Source> = {
  ced: {
    full: (loc) =>
      withLoc(
        `College Board, <i>AP World History: Modern Course and Exam Description</i>, effective fall 2026 (New York: College Board, 2026)${loc ? `, ${loc}` : ""}, <a href="https://apcentral.collegeboard.org/media/pdf/ap-world-history-modern-course-and-exam-description.pdf">https://apcentral.collegeboard.org/media/pdf/ap-world-history-modern-course-and-exam-description.pdf</a>`,
      ),
    short: (loc) => withLoc(`College Board, <i>Course and Exam Description</i>`, loc),
    bibKey: "ced",
  },
  afe_pop: afeSong("Population Boom", "https://afe.easia.columbia.edu/songdynasty-module/econ-rev-intro-pop.html"),
  afe_comm: afeSong("Commercialization", "https://afe.easia.columbia.edu/songdynasty-module/econ-rev-commercial.html"),
  afe_money: afeSong("Paper Money", "https://afe.easia.columbia.edu/songdynasty-module/econ-rev-money.html"),
  afe_iron: afeSong("Iron &amp; Steel", "https://afe.easia.columbia.edu/songdynasty-module/econ-rev-iron-steel.html"),
  afe_rice: afeSong("Rice Cultivation", "https://afe.easia.columbia.edu/songdynasty-module/tech-rice.html"),
  afe_print: afeSong("Printing &amp; Movable Type", "https://afe.easia.columbia.edu/songdynasty-module/tech-printing.html"),
  afe_ship: afeSong("Shipbuilding and the Compass", "https://afe.easia.columbia.edu/songdynasty-module/tech-compass.html"),
  afe_gun: afeSong("Gunpowder", "https://afe.easia.columbia.edu/songdynasty-module/tech-gunpowder.html"),
  afe_sch: afeSong("Scholar-Officials of the Song", "https://afe.easia.columbia.edu/songdynasty-module/confucian-scholar.html"),
  afe_neo: afeSong("‘Neo-Confucianism’ &amp; Family", "https://afe.easia.columbia.edu/songdynasty-module/confucian-neo.html"),
  afe_yuanrel: afeMongols(
    "The Mongols in China: Life in China under Mongol Rule: Religion",
    "https://afe.easia.columbia.edu/mongols/china/china3_f.htm",
  ),
  afe_astro: afeMongols("Mongol Support for Science: The Beijing Observatory", "https://afe.easia.columbia.edu/mongols/pop/china/astro_pop.htm"),
  afe_keypts: web(
    "Asia for Educators, ",
    "Key Points: 1000 CE–1450 CE",
    "https://afe.easia.columbia.edu/main_pop/kpct/kp_1000-1450ce.htm",
    "Asia for Educators, “Key Points: 1000 CE–1450 CE”",
    "afe_keypts",
  ),
  afe_ming: {
    full: (loc) =>
      withLoc(
        `Sue Gronewald, “The Ming Voyages,” Asia for Educators, Columbia University, ${ACCESSED}, <a href="https://afe.easia.columbia.edu/special/china_1000ce_mingvoyages.htm">https://afe.easia.columbia.edu/special/china_1000ce_mingvoyages.htm</a>`,
        loc,
      ),
    short: () => `Gronewald, “Ming Voyages.”`,
    bibKey: "afe_ming",
  },
  polo: {
    full: (loc) =>
      withLoc(
        `Marco Polo, <i>The Book of Ser Marco Polo, the Venetian, Concerning the Kingdoms and Marvels of the East</i>, trans. and ed. Henry Yule, 3rd ed., rev. Henri Cordier (London: John Murray, 1903)`,
        loc,
      ),
    short: (loc) => withLoc(`Polo, <i>Book of Ser Marco Polo</i>`, loc),
    bibKey: "polo",
  },
  orias: {
    full: (loc) =>
      withLoc(
        `“Through the Strait of Malacca to China: 1345–1346,” in <i>The Travels of Ibn Battuta: A Virtual Tour with the 14th Century Traveler</i>, Office of Resources for International and Area Studies (ORIAS), University of California, Berkeley, ${ACCESSED}, <a href="https://orias.berkeley.edu/resources-teachers/travels-ibn-battuta/journey/through-strait-malacca-china-1345-1346">https://orias.berkeley.edu/resources-teachers/travels-ibn-battuta/journey/through-strait-malacca-china-1345-1346</a>`,
        loc,
      ),
    short: () => `“Through the Strait of Malacca to China.”`,
    bibKey: "orias",
  },
  conlan: {
    full: () =>
      `Thomas D. Conlan, <i>Scrolls of the Mongol Invasions of Japan</i>, Princeton University, ${ACCESSED}, <a href="https://digital.princeton.edu/mongol-invasions/">https://digital.princeton.edu/mongol-invasions/</a>.`,
    short: () => `Conlan, <i>Scrolls of the Mongol Invasions</i>.`,
    bibKey: "conlan",
  },
  brit_yuan: {
    full: () =>
      `<i>Encyclopaedia Britannica</i>, s.v. “History of China: The Yuan, or Mongol, Dynasty,” ${ACCESSED}, <a href="https://www.britannica.com/topic/history-of-China/The-Yuan-or-Mongol-dynasty">https://www.britannica.com/topic/history-of-China/The-Yuan-or-Mongol-dynasty</a>.`,
    short: () => `<i>Britannica</i>, s.v. “Yuan, or Mongol, Dynasty.”`,
    bibKey: "brit_yuan",
  },
  brit_maxia: {
    full: () =>
      `<i>Encyclopaedia Britannica</i>, s.v. “Ma-Xia school,” ${ACCESSED}, <a href="https://www.britannica.com/art/Ma-Xia-school">https://www.britannica.com/art/Ma-Xia-school</a>.`,
    short: () => `<i>Britannica</i>, s.v. “Ma-Xia school.”`,
    bibKey: "brit_maxia",
  },
  lumen: {
    full: () =>
      `Boundless, “Trade and Currency under the Yuan,” in <i>World Civilization</i> (Open SUNY/Lumen Learning), ${ACCESSED}, <a href="https://courses.lumenlearning.com/suny-hccc-worldcivilization/chapter/trade-and-currency-under-the-yuan/">https://courses.lumenlearning.com/suny-hccc-worldcivilization/chapter/trade-and-currency-under-the-yuan/</a>.`,
    short: () => `Boundless, “Trade and Currency under the Yuan.”`,
    bibKey: "lumen",
  },
  loc_vn: {
    full: () =>
      `Ronald J. Cima, ed., <i>Vietnam: A Country Study</i> (Washington, DC: Federal Research Division, Library of Congress, 1989), “The Tran Dynasty and the Defeat of the Mongols,” <a href="https://countrystudies.us/vietnam/9.htm">https://countrystudies.us/vietnam/9.htm</a>.`,
    short: () => `Cima, <i>Vietnam</i>, “Tran Dynasty.”`,
    bibKey: "loc_vn",
  },
  unesco_haeinsa: web(
    "UNESCO World Heritage Centre, ",
    "Haeinsa Temple Janggyeong Panjeon, the Depositories for the Tripitaka Koreana Woodblocks",
    "https://whc.unesco.org/en/list/737/",
    "UNESCO, “Haeinsa Temple Janggyeong Panjeon”",
    "unesco_haeinsa",
  ),
  unesco_qz: web(
    "UNESCO World Heritage Centre, ",
    "Quanzhou: Emporium of the World in Song-Yuan China",
    "https://whc.unesco.org/en/list/1561/",
    "UNESCO, “Quanzhou”",
    "unesco_qz",
  ),
  unesco_gc: web("UNESCO World Heritage Centre, ", "The Grand Canal", "https://whc.unesco.org/en/list/1443/", "UNESCO, “Grand Canal”", "unesco_gc"),
  unesco_hunmin: web(
    "UNESCO Memory of the World, ",
    "Hunminjeongum Manuscript",
    "https://www.unesco.org/en/memory-world/hunminjeongum-manuscript",
    "UNESCO, “Hunminjeongum Manuscript”",
    "unesco_hunmin",
  ),
  bnf: web(
    "Bibliothèque nationale de France, ",
    "‘Jikji,’ a Treasure of the World of Printing",
    "https://www.bnf.fr/en/jikji-treasure-world-printing",
    "Bibliothèque nationale de France, “‘Jikji’”",
    "bnf",
  ),
  jnto: web(
    "Japan National Tourism Organization, ",
    "Kinkakuji Temple",
    "https://www.japan.travel/en/spot/1152/",
    "Japan National Tourism Organization, “Kinkakuji Temple”",
    "jnto",
  ),
  smart_david: web("Smarthistory, ", "The David Vases", "https://smarthistory.org/the-david-vases/", "Smarthistory, “David Vases”", "smart_david"),
};

/** Bibliography (Chicago, alphabetical by first element). */
export const BIBLIOGRAPHY: Record<string, string> = {
  afe_song: `Asia for Educators. <i>China in 1000 CE: The Most Advanced Society in the World</i>. Song Dynasty China module. Columbia University. ${ACCESSED_BIB}. <a href="https://afe.easia.columbia.edu/songdynasty-module/">https://afe.easia.columbia.edu/songdynasty-module/</a>.`,
  afe_keypts: `Asia for Educators. “Key Points: 1000 CE–1450 CE.” Columbia University. ${ACCESSED_BIB}. <a href="https://afe.easia.columbia.edu/main_pop/kpct/kp_1000-1450ce.htm">https://afe.easia.columbia.edu/main_pop/kpct/kp_1000-1450ce.htm</a>.`,
  afe_mongols: `Asia for Educators. <i>The Mongols in World History</i>. Columbia University. ${ACCESSED_BIB}. <a href="https://afe.easia.columbia.edu/mongols/">https://afe.easia.columbia.edu/mongols/</a>.`,
  bnf: `Bibliothèque nationale de France. “‘Jikji,’ a Treasure of the World of Printing.” ${ACCESSED_BIB}. <a href="https://www.bnf.fr/en/jikji-treasure-world-printing">https://www.bnf.fr/en/jikji-treasure-world-printing</a>.`,
  lumen: `Boundless. “Trade and Currency under the Yuan.” In <i>World Civilization</i>. Open SUNY/Lumen Learning. ${ACCESSED_BIB}. <a href="https://courses.lumenlearning.com/suny-hccc-worldcivilization/chapter/trade-and-currency-under-the-yuan/">https://courses.lumenlearning.com/suny-hccc-worldcivilization/chapter/trade-and-currency-under-the-yuan/</a>.`,
  loc_vn: `Cima, Ronald J., ed. <i>Vietnam: A Country Study</i>. Washington, DC: Federal Research Division, Library of Congress, 1989. <a href="https://www.loc.gov/item/88600482/">https://www.loc.gov/item/88600482/</a>.`,
  ced: `College Board. <i>AP World History: Modern Course and Exam Description</i>. Effective fall 2026. New York: College Board, 2026. <a href="https://apcentral.collegeboard.org/media/pdf/ap-world-history-modern-course-and-exam-description.pdf">https://apcentral.collegeboard.org/media/pdf/ap-world-history-modern-course-and-exam-description.pdf</a>.`,
  conlan: `Conlan, Thomas D. <i>Scrolls of the Mongol Invasions of Japan</i>. Princeton University. ${ACCESSED_BIB}. <a href="https://digital.princeton.edu/mongol-invasions/">https://digital.princeton.edu/mongol-invasions/</a>.`,
  brit_yuan: `<i>Encyclopaedia Britannica</i>. “History of China: The Yuan, or Mongol, Dynasty.” ${ACCESSED_BIB}. <a href="https://www.britannica.com/topic/history-of-China/The-Yuan-or-Mongol-dynasty">https://www.britannica.com/topic/history-of-China/The-Yuan-or-Mongol-dynasty</a>.`,
  brit_maxia: `<i>Encyclopaedia Britannica</i>. “Ma-Xia School.” ${ACCESSED_BIB}. <a href="https://www.britannica.com/art/Ma-Xia-school">https://www.britannica.com/art/Ma-Xia-school</a>.`,
  afe_ming: `Gronewald, Sue. “The Ming Voyages.” Asia for Educators, Columbia University. ${ACCESSED_BIB}. <a href="https://afe.easia.columbia.edu/special/china_1000ce_mingvoyages.htm">https://afe.easia.columbia.edu/special/china_1000ce_mingvoyages.htm</a>.`,
  jnto: `Japan National Tourism Organization. “Kinkakuji Temple.” Travel Japan. ${ACCESSED_BIB}. <a href="https://www.japan.travel/en/spot/1152/">https://www.japan.travel/en/spot/1152/</a>.`,
  orias: `Office of Resources for International and Area Studies (ORIAS). “Through the Strait of Malacca to China: 1345–1346.” In <i>The Travels of Ibn Battuta: A Virtual Tour with the 14th Century Traveler</i>. University of California, Berkeley. ${ACCESSED_BIB}. <a href="https://orias.berkeley.edu/resources-teachers/travels-ibn-battuta/journey/through-strait-malacca-china-1345-1346">https://orias.berkeley.edu/resources-teachers/travels-ibn-battuta/journey/through-strait-malacca-china-1345-1346</a>.`,
  polo: `Polo, Marco. <i>The Book of Ser Marco Polo, the Venetian, Concerning the Kingdoms and Marvels of the East</i>. Translated and edited by Henry Yule. 3rd ed., revised by Henri Cordier. 2 vols. London: John Murray, 1903. Book 2, chapter 24 excerpted in <i>The Mongols in World History</i>, Asia for Educators, Columbia University, <a href="https://afe.easia.columbia.edu/mongols/figures/ser_xxiv.pdf">https://afe.easia.columbia.edu/mongols/figures/ser_xxiv.pdf</a>; volume 2 at Project Gutenberg, <a href="https://www.gutenberg.org/ebooks/12410">https://www.gutenberg.org/ebooks/12410</a>.`,
  smart_david: `Smarthistory. “The David Vases.” ${ACCESSED_BIB}. <a href="https://smarthistory.org/the-david-vases/">https://smarthistory.org/the-david-vases/</a>.`,
  unesco_hunmin: `UNESCO Memory of the World. “Hunminjeongum Manuscript.” ${ACCESSED_BIB}. <a href="https://www.unesco.org/en/memory-world/hunminjeongum-manuscript">https://www.unesco.org/en/memory-world/hunminjeongum-manuscript</a>.`,
  unesco_gc: `UNESCO World Heritage Centre. “The Grand Canal.” ${ACCESSED_BIB}. <a href="https://whc.unesco.org/en/list/1443/">https://whc.unesco.org/en/list/1443/</a>.`,
  unesco_haeinsa: `UNESCO World Heritage Centre. “Haeinsa Temple Janggyeong Panjeon, the Depositories for the Tripitaka Koreana Woodblocks.” ${ACCESSED_BIB}. <a href="https://whc.unesco.org/en/list/737/">https://whc.unesco.org/en/list/737/</a>.`,
  unesco_qz: `UNESCO World Heritage Centre. “Quanzhou: Emporium of the World in Song-Yuan China.” ${ACCESSED_BIB}. <a href="https://whc.unesco.org/en/list/1561/">https://whc.unesco.org/en/list/1561/</a>.`,
};

// ---------------------------------------------------------------------------

export interface Development {
  title: string;
  when: string;
  where: string;
  body: string;
  process: string[]; // global-process tags
  connection: string;
}

export interface Artifact {
  kind: "junk" | "vase" | "compass";
  title: string;
  blurb: string;
}

export interface Chapter {
  id: string;
  letter: string;
  hanzi: string;
  pinyin: string;
  gloss: string;
  name: string;
  title: string;
  bigIdea: string;
  scene: string;
  alt: string;
  caption: string;
  developments: Development[];
  artifacts?: Artifact[];
  spotlight?: { kind: string; title: string; quote: string; attribution: string; image?: string; imageAlt?: string };
  synthesis: string;
}

export const THESIS = `Between c. 1200 and c. 1450, East Asia was at once the most commercially dynamic region on Earth and one of the most culturally continuous. In China, the Song dynasty’s Confucian bureaucracy, its patriarchal family ideals and its rice-based agriculture survived the shock of Mongol conquest (the Yuan, 1271–1368), and the Ming deliberately restored them after 1368. Korea, Japan and Vietnam borrowed Chinese writing, Confucian thought and Buddhism, yet adapted them into distinct states of their own. And the region was never isolated. Champa rice, Persian cobalt, Islamic astronomy and Tibetan Buddhism flowed in, while paper money, printing, gunpowder, the compass and porcelain flowed out along the Silk Roads and across the Indian Ocean. This site follows both halves of that story, <em>continuity at home and connection abroad</em>, through the seven PIRATES categories.`;

export const CHAPTERS: Chapter[] = [
  // =====================================================================
  {
    id: "political",
    letter: "P",
    hanzi: "政",
    pinyin: "zhèng",
    gloss: "to govern",
    name: "Political",
    title: "The Mandate & the Meritocracy",
    bigIdea:
      "Chinese dynasties justified their power through Confucian ideas and ran it through an examination-trained bureaucracy. The model proved so durable that the Mongol conquerors eventually restored it, and China’s neighbors defined themselves by how much of it they chose to adopt.",
    scene: "political",
    alt: "Moonlit alley between rows of examination cells lit by candles, a proctor with a lantern in the distance and a watchtower at the end beneath a full moon.",
    caption:
      "Artist’s reconstruction · An imperial examination compound (<i>gongyuan</i>) at night. Candidates sat sealed in rows of tiny cells, writing essays on the Confucian classics by candlelight, while proctors patrolled the alleys and watched from a central tower.",
    developments: [
      {
        title: "Government by examination",
        when: "Song dynasty, 960–1279",
        where: "China",
        body: `The Song made the civil service examination the normal road to power. Instead of relying on hereditary aristocrats or generals, emperors recruited <strong>scholar-officials</strong> who had mastered the Confucian classics. Competition exploded, from fewer than 30,000 candidates per exam early in the dynasty to about 400,000 by its end, and in some prefectures only one candidate in 333 passed. To keep the system fair, officials replaced candidates’ names with numbers and had clerks recopy every answer so that no examiner could recognize a candidate’s handwriting.{{afe_sch}} The result was a loyal, literate <strong>scholar-gentry</strong> class, the backbone of a state that used “traditional methods of Confucianism and an imperial bureaucracy to maintain and justify its rule.”{{ced:38}}`,
        process: ["State building", "Comparison"],
        connection: `Most Afro-Eurasian states of the period ran on birth and military power, like Europe’s feudal nobility or Japan’s samurai. Song China’s <em>merit-based</em> bureaucracy was different in kind, and it lasted: China kept examination recruitment until 1905. <strong>Cause → effect:</strong> cheap printed books (see Intellectual) put exam texts within reach of far more families, one reason the number of candidates exploded.`,
      },
      {
        title: "A conquest dynasty: the Mongol Yuan",
        when: "1271–1368",
        where: "China, from Dadu (Beijing)",
        body: `Khubilai Khan, Chinggis Khan’s grandson, founded the <strong>Yuan dynasty</strong> in 1271, destroyed the last of the Southern Song by 1279 and moved the capital to Beijing.{{afe_keypts}} The Yuan kept Chinese-style ministries but divided subjects into four legal classes: Mongols; <em>semuren</em> (allies from Central and West Asia, such as Turks and Muslims); <em>hanren</em> (northern Chinese); and <em>nanren</em> (former subjects of the Southern Song). They also suspended the examinations for decades. When exams returned in 1313, they had separate curricula and standards for each group. At the first exams in 1315, the 300 degrees were split evenly, 75 per group, even though southern Chinese vastly outnumbered everyone else.{{brit_yuan}}`,
        process: ["State building", "Mongol Empire"],
        connection: `The Yuan was one khanate in a Eurasian empire that also ruled Persia (the Ilkhanate) and Russia (the Golden Horde). The College Board stresses that this expansion “facilitated Afro-Eurasian trade and communication.”{{ced:55}} <strong>Continuity &amp; change:</strong> conquest changed <em>who</em> ruled China but not <em>how</em> it was ruled. Like earlier northern conquerors, the Mongols ended up relying on Confucian bureaucrats and examinations.`,
      },
      {
        title: "The Ming restoration & the tributary world",
        when: "1368–1450",
        where: "China and the Indian Ocean",
        body: `Weakened by rebellion, inflation and epidemic disease, the Yuan were driven back to the steppe in 1368 by the new <strong>Ming dynasty</strong> (1368–1644), which restored Chinese rule.{{afe_keypts}} The early Ming rebuilt Confucian government and revived the <strong>tributary system</strong>, in which foreign rulers acknowledged the emperor’s superiority with envoys and gifts in return for recognition and trade. Admiral Zheng He’s seven voyages (1405–1433) carried that system across the Indian Ocean as far as the east coast of Africa. The first fleet alone numbered 317 ships and nearly 28,000 men.{{afe_ming}}`,
        process: ["State building", "Indian Ocean"],
        connection: `Zheng He’s fleets were diplomacy backed by overwhelming force. The College Board singles them out as “Chinese maritime activity” that encouraged “significant technological and cultural transfers.”{{ced:58}} <strong>Change → continuity:</strong> after the Yongle emperor died, Confucian officials condemned the voyages as wasteful and the program ended.{{afe_ming}} Europe’s Atlantic voyages later in the century went the opposite way.`,
      },
      {
        title: "Neighbors who adapted, not copied",
        when: "1185–1428",
        where: "Japan · Korea · Vietnam",
        body: `In <strong>Japan</strong>, a warrior government replaced court rule. The <strong>Kamakura shogunate</strong> (1185–1333) governed through a network of samurai pledged to keep the peace, and under the weaker <strong>Ashikaga</strong> shoguns (1336–1573) regional lords called daimyo fought constantly for power.{{afe_keypts}} Samurai defeated Mongol invasions in 1274 and 1281. Historian Thomas Conlan argues they fought the invaders to a standstill without needing the “divine winds” (<em>kamikaze</em>) of later legend.{{conlan}} <strong>Korea’s</strong> Goryeo dynasty became a Mongol vassal after invasions that began in 1231.{{afe_keypts}} <strong>Vietnam’s</strong> Trần dynasty threw back three Mongol invasions. At the Bạch Đằng River in 1288, iron-tipped stakes planted in the riverbed wrecked a Mongol fleet as the tide went out.{{loc_vn}}`,
        process: ["Cultural adaptation", "Comparison"],
        connection: `The College Board frames this era around Chinese traditions that “influenced neighboring regions.”{{ced:39}} Those neighbors adapted Chinese models rather than copying them. Japan’s bonds of land and loyalty between lords and samurai invite the classic AP comparison with <em>European feudalism</em>. Vietnam used a Chinese-style state to defend itself <em>against</em> Chinese empires, defeating the Mongols in 1288 and later ending a Ming occupation (1407–1427).`,
      },
    ],
    synthesis: `Across all four stories, the Confucian bureaucratic state was the region’s center of gravity. Song rulers perfected it, Mongol conquerors bent and then restored it, and Ming emperors made it the model for a tributary world order. Neighbors measured their independence by how they adapted it: a shogun’s warrior government in Japan, a Neo-Confucian Joseon kingdom in Korea after 1392, and a Vietnamese state that used Chinese forms to fight Chinese armies.`,
  },
  // =====================================================================
  {
    id: "intellectual",
    letter: "I",
    hanzi: "學",
    pinyin: "xué",
    gloss: "learning",
    name: "Intellectual",
    title: "Printing the Classics",
    bigIdea:
      "Neo-Confucian scholarship, cheap printed books and science shared across the Mongol Empire made East Asia one of the most literate and learned regions of the medieval world. Korea’s new alphabet showed how that learning could be made local.",
    scene: "intellectual",
    alt: "Close-up of wooden movable type set in an iron frame with mirror-reversed Chinese characters, loose type blocks, and a printed page beginning with the words of the Great Learning.",
    caption:
      "Artist’s reconstruction · Wooden movable type, set in mirror image with the opening of the <i>Great Learning</i> (大學之道…), one of Zhu Xi’s Four Books, beside the freshly printed page.",
    developments: [
      {
        title: "Neo-Confucianism: Zhu Xi’s synthesis",
        when: "Zhu Xi, 1130–1200 · official from 1313",
        where: "China → Korea, Japan, Vietnam",
        body: `The Song saw a vigorous revival of Confucianism, which shaped the examinations, the identity of the scholar-official class, the family system and political debate. This revived <strong>Neo-Confucianism</strong> taught that self-cultivation leads not only to personal virtue but to a harmonious society and state. Its master synthesizer, <strong>Zhu Xi</strong> (1130–1200), wrote commentaries on the <em>Four Books</em>, championed them as the center of a scholar’s education, and saw his synthesis accepted as <em>the</em> orthodox interpretation of Confucianism in later dynasties and in other East Asian countries.{{afe_neo}} When the Yuan restored the examinations in 1313, Confucian learning returned to the center of Chinese government.{{brit_yuan}}`,
        process: ["Cultural diffusion", "Syncretism"],
        connection: `Neo-Confucianism was itself a product of exchange. It answered <em>Buddhism</em>, which had reached China from India along the Silk Roads, by taking on the big questions about the universe and the mind that Buddhism raised. It then spread outward: the College Board lists the “influence of Neo-Confucianism and Buddhism in East Asia” among the period’s key cultural traditions.{{ced:39}} <strong>Continuity:</strong> a curriculum fixed in this era shaped East Asian government and family life for six centuries.`,
      },
      {
        title: "Print culture: from clay type to metal type",
        when: "c. 1040s–1377",
        where: "China · Korea",
        body: `Chinese printers mass-produced books by carving whole pages into wooden blocks, inking them and pressing paper onto them. The artisan <strong>Bi Sheng</strong> (990–1051) invented movable type made of baked clay, which proved fragile.{{afe_print}} Korean printers went further. The <strong><em>Jikji</em></strong>, a Buddhist work printed in 1377 in what is now Cheongju, is the oldest known book printed with <strong>movable metal type</strong>, 78 years before the Gutenberg Bible.{{bnf}} In China, printing “dramatically lowered the price of books,” spreading literacy and boosting drama and other popular culture.{{afe_print}}`,
        process: ["Technology transfer", "Comparison"],
        connection: `The College Board lists “paper from China” as a key diffusion of the period.{{ced:61}} Comparing East Asian printing with Gutenberg’s press is revealing. Chinese writing needs thousands of distinct characters, so woodblocks remained practical in China for centuries. Europe’s alphabet of a few dozen letters made movable type far more economical, and that difference in writing systems shaped each region’s print revolution.`,
      },
      {
        title: "Science across the Mongol Empire",
        when: "1260s–1280s",
        where: "Persia → Beijing",
        body: `The Mongols moved experts across their empire as deliberately as they moved goods. Knowing that Persian astronomers had made major advances at the <strong>Maragheh observatory</strong>, Khubilai Khan invited the astronomer <strong>Jamal al-Din</strong> to Beijing, where he brought Persian instruments and the khan commissioned an observatory. Working with him, the Chinese astronomer, mathematician and hydrologist <strong>Guo Shoujing</strong> (1231–1316) devised a new, more accurate calendar.{{afe_astro}}`,
        process: ["Technology transfer", "Mongol Empire"],
        connection: `This is a textbook case of what the College Board describes: “interregional contacts and conflicts between states and empires, including the Mongols, encouraged significant technological and cultural transfers.”{{ced:56}} Knowledge that once crept along caravan routes now traveled with the backing of a single ruling family that stretched from Persia to China.`,
      },
      {
        title: "Hangul: an alphabet for the people",
        when: "Created 1443 · published 1446",
        where: "Joseon Korea",
        body: `Korean scholars wrote in Classical Chinese, which took years to master. In 1443 King <strong>Sejong</strong> of the Joseon dynasty created a phonetic alphabet that ordinary people could learn quickly. It was published in 1446 in the book <em>Hunminjeongeum</em>, “the proper sounds for instructing the people.”{{unesco_hunmin}}`,
        process: ["Cultural adaptation", "Continuity & change"],
        connection: `Hangul shows East Asian adaptation at its sharpest. Joseon remained deeply Confucian and kept Classical Chinese for official learning, yet it built a script to fit the Korean language. A Unit 2 parallel is the Mongols’ adoption of the <em>Uyghur script</em> to run their empire.{{ced:56}} In both cases, a writing system became a tool of state power and identity.`,
      },
    ],
    synthesis: `The intellectual life of the period rested on one Chinese foundation, Confucian texts read through Zhu Xi, carried by one Chinese technology, printing. Neither stayed Chinese. Korea cast type in metal and invented its own alphabet, the Mongols brought Persian astronomy to Beijing, and the Four Books became the shared curriculum of an entire region.`,
  },
  // =====================================================================
  {
    id: "religious",
    letter: "R",
    hanzi: "信",
    pinyin: "xìn",
    gloss: "faith",
    name: "Religious",
    title: "Faith Across Borders",
    bigIdea:
      "Buddhism, an Indian religion transformed in China, kept changing as it moved into Korea and Japan. Meanwhile Confucian ancestor rites and the Mongols’ patronage of many faiths made East Asia one of the most religiously layered regions of the world.",
    scene: "religious",
    alt: "Shafts of sunlight entering through slatted windows into a long wooden hall lined with racks of lacquered printing blocks, a monk standing in the haze.",
    caption:
      "Artist’s reconstruction · The Tripitaka depository at Haeinsa, Korea, where more than 80,000 woodblocks of the Buddhist canon, carved 1237–1248, are still stored. The slatted windows were designed to ventilate the halls.",
    developments: [
      {
        title: "Mahayana Buddhism takes root: Chan, Pure Land & Zen",
        when: "12th–15th centuries",
        where: "China → Korea, Japan",
        body: `The College Board identifies three branches of Buddhism shaping Asian societies: <strong>Theravada</strong>, <strong>Mahayana</strong> and <strong>Tibetan</strong>.{{ced:39}} East Asia followed Mahayana schools. <strong>Chan</strong> (meditation) Buddhism and devotional <strong>Pure Land</strong> Buddhism flourished in China and spread to Korea and Japan. In Japan, Chan became <strong>Zen</strong>, and under the Ashikaga shoguns it spread among the samurai along with meditation and a formal tea ceremony.{{afe_keypts}}`,
        process: ["Cultural diffusion", "Syncretism"],
        connection: `Buddhism is the period’s classic example of diffusion. It began in India, traveled the Silk Roads into China and moved on to Korea and Japan, changing at each stop. The College Board lists “the influence of Buddhism in East Asia” as a key example of cultural diffusion.{{ced:61}} <strong>Syncretism:</strong> in Japan, Buddhist practice blended with worship of the native Shinto <em>kami</em>. Zen’s discipline suited a warrior class, much as Christianity adapted to Europe’s knights.`,
      },
      {
        title: "The Tripitaka Koreana: carving a defense against the Mongols",
        when: "1237–1248",
        where: "Goryeo Korea (now at Haeinsa)",
        body: `As Mongol armies ravaged Korea, Goryeo craftsmen carved the entire Buddhist canon, the <strong>Tripitaka</strong>, onto some <strong>80,000 woodblocks</strong> between 1237 and 1248. It was an appeal to the Buddha’s authority for the defense of Korea against the Mongol invasions. Buddhist scholars still prize the blocks for their accuracy. They survive at <strong>Haeinsa Temple</strong> in 15th-century storage halls whose conservation design has protected them for centuries.{{unesco_haeinsa}}`,
        process: ["State & religion", "Cause → effect"],
        connection: `The blocks show the Mongol conquests setting off responses far beyond the battlefield. Faith and state power worked together here, as when European kings endowed cathedrals or Muslim rulers funded mosques and madrasas. The project also depended on printing technology that had come from China, so an act of devotion became a feat of engineering.`,
      },
      {
        title: "Ancestors & ritual: Confucianism as family religion",
        when: "Continuous; revived in the Song",
        where: "China · Korea · Vietnam",
        body: `Confucianism was more than a philosophy of government. <strong>Filial piety</strong>, the duty to respect and obey one’s parents, extended to the ancestors. Everyone was expected to marry so that family lines would continue and male heirs could make offerings of food and drink to the deceased. Zhu Xi even compiled a practical manual of family ritual.{{afe_neo}}`,
        process: ["Continuity", "Comparison"],
        connection: `Ancestor veneration was one of East Asia’s deepest continuities. It outlasted dynastic change and foreign conquest, and the College Board lists “filial piety in East Asia” among the region’s defining traditions.{{ced:39}} <strong>Comparison:</strong> just as Islamic law shaped family life, inheritance and gender roles across Dar al-Islam, Confucian ritual tied religion to everyday family life in East Asia.`,
      },
      {
        title: "Tolerance, with limits, under the Yuan",
        when: "1260s–1368",
        where: "Yuan China · Quanzhou",
        body: `The Mongols were drawn to <strong>Tibetan Buddhism</strong> and recruited Tibetan monks, the most important being the <strong>ʼPhags-pa Lama</strong>, to help them rule. They supported Islam and built many mosques in China. Khubilai even promoted Nestorian Christianity, his mother’s faith. Tolerance had limits, though: after a religious debate in 1281, Khubilai backed the Buddhists and imposed severe restrictions on Daoism.{{afe_yuanrel}} In port cities, foreign faiths thrived. Visiting in 1345–1346, the Moroccan traveler Ibn Battuta wrote that whenever he met Muslims in China he felt as if he were meeting his own family.{{orias}}`,
        process: ["Diasporas", "Cultural exchange"],
        connection: `Merchant diasporas “introduced their own cultural traditions into the indigenous cultures” and were changed by them in turn, a key Unit 2 concept.{{ced:58}} Tibetan Buddhism at the Yuan court shows the same exchange in the other direction: a religion from Inner Asia moving into the heart of Chinese imperial power.`,
      },
    ],
    synthesis: `Religious life in East Asia was layered rather than exclusive. A Korean monk might carve Buddhist sutras, a Chinese official honor his ancestors with Confucian rites, and a Muslim merchant pray in a Quanzhou mosque, sometimes in the same kingdom and the same decade. Diffusion supplied the religions, but adaptation made them East Asian.`,
  },
  // =====================================================================
  {
    id: "artistic",
    letter: "A",
    hanzi: "藝",
    pinyin: "yì",
    gloss: "art",
    name: "Artistic",
    title: "Brush, Kiln & Gold",
    bigIdea:
      "East Asian art of this era was treasured at home and traded across the world. Song landscape painting shaped Japanese art, and porcelain decorated with Persian cobalt became one of history’s first truly global luxury goods.",
    scene: "artistic",
    alt: "The three-storey Golden Pavilion with gilded upper floors and a phoenix on its roof, reflected in a still pond, framed by cedars and red autumn maples.",
    caption:
      "Artist’s reconstruction · Kinkaku, the Golden Pavilion in Kyoto, begun in 1397 for the retired shogun Ashikaga Yoshimitsu and reflected in the Kyōko-chi (“mirror pond”). Today’s building is a 1955 reconstruction.",
    developments: [
      {
        title: "Landscape in mist: Song painting",
        when: "Ma Yuan, c. 1160–1225 · Xia Gui, fl. c. 1195–1224",
        where: "Southern Song court, Hangzhou",
        body: `Southern Song court painters <strong>Ma Yuan</strong> and <strong>Xia Gui</strong> created a lyrical landscape style of simplified brushwork, bold asymmetry, mist and graded ink tones that suggest vast open space. Ma Yuan became famous for “<strong>one-corner</strong>” compositions, which crowd the painted forms into one corner and leave the rest as emptiness or mist.{{brit_maxia}} The opening scene of this site, with its pagoda above a misty river, was composed in that spirit.`,
        process: ["Cultural diffusion"],
        connection: `When the Southern Song fell, the Ma-Xia style declined in China but found new life in Japan, influencing painters such as Shūbun and Sesshū.{{brit_maxia}} It illustrates the College Board’s example of “Chinese literary and scholarly traditions and their spread” to Japan and Korea.{{ced:39}}`,
      },
      {
        title: "Blue-and-white: porcelain as a global commodity",
        when: "1300s",
        where: "Jingdezhen → the Islamic world",
        body: `Chinese potters led the world in high-fired ceramics. Under the Yuan, the kilns of <strong>Jingdezhen</strong> perfected <strong>blue-and-white porcelain</strong>, painted with cobalt that came largely from Persia. The famous <strong>David Vases</strong> (1351) carry inscriptions recording their donor, their date and their dedication to a Daoist temple.{{smart_david}} Visiting China in the 1340s, Ibn Battuta judged its porcelain “the finest of all makes of pottery.”{{orias}}`,
        process: ["Trade networks", "Cultural blending"],
        connection: `Blue-and-white is Afro-Eurasian exchange you can hold in your hands: a Persian mineral, fired in a Chinese kiln, shipped through ports like Quanzhou to buyers across the Islamic world. The College Board notes that demand for luxury goods rose across Afro-Eurasia as “Chinese, Persian, and Indian artisans and merchants expanded their production of textiles and porcelains for export.”{{ced:54}} <em>Rotate the meiping vase below to see the cobalt decoration.</em>`,
      },
      {
        title: "The Golden Pavilion: Japan’s synthesis",
        when: "1397",
        where: "Kyoto, Japan",
        body: `In 1397 the shogun <strong>Ashikaga Yoshimitsu</strong> founded a retirement villa in Kyoto whose centerpiece became <strong>Kinkaku</strong>, the Golden Pavilion. Each story uses a different style: aristocratic Heian-period design on the first, a samurai residence on the second, and a Chinese Zen hall on the third. The upper two stories are covered in gold leaf. After Yoshimitsu’s death the villa became a Zen temple, and its <strong>Kyōko-chi</strong> (“mirror pond”) still reflects the building. The pavilion burned in 1950 and was rebuilt in 1955.{{jnto}}`,
        process: ["Cultural adaptation", "Legitimacy & power"],
        connection: `Kinkaku stacks Japan’s political history in wood and gold: the old imperial court, the new warrior class and imported Chinese Zen. Like monumental architecture elsewhere in this period, from Gothic cathedrals to the stone enclosures of Great Zimbabwe, it projected its patron’s wealth and legitimacy.`,
      },
    ],
    artifacts: [
      {
        kind: "vase",
        title: "Blue-and-white meiping",
        blurb: "Drag to rotate. A Yuan-style meiping (“plum vase”) with cloud-collar lappets, a scrolling-peony band and lotus panels, painted in cobalt.",
      },
    ],
    synthesis: `East Asian art in this period reflected power and connection. Court painting and gilded pavilions displayed the prestige of emperors and shoguns, while porcelain carried East Asian craft into kitchens and palaces from Cairo to Calicut. The styles crossed borders too: Song landscape painting shaped Japanese art, and Islamic markets shaped what Chinese potters made.`,
  },
  // =====================================================================
  {
    id: "technological",
    letter: "T",
    hanzi: "技",
    pinyin: "jì",
    gloss: "skill",
    name: "Technological",
    title: "Engines of the Song",
    bigIdea:
      "Innovations in farming, warfare, navigation and industry transformed Chinese society. Several of them, carried west along Mongol and Indian Ocean routes, went on to transform the rest of Afro-Eurasia.",
    scene: "technological",
    alt: "A five-masted Chinese junk with rust-red battened sails glowing against a sunset, sailing across rolling ocean waves with an escort fleet on the horizon.",
    caption:
      "Artist’s reconstruction · A treasure fleet of seagoing junks under battened lug sails, in the manner of Zheng He’s voyages of 1405–1433.",
    developments: [
      {
        title: "Champa rice & the farming revolution",
        when: "Introduced by 1012",
        where: "Champa (Vietnam) → southern China",
        body: `Emperor Zhenzong learned of a fast-ripening, drought-resistant rice from <strong>Champa</strong>, a kingdom in what is now Vietnam, and sent envoys to bring back samples. By 1012 it had been introduced in the lower Yangzi and Huai river regions. <strong>Champa rice</strong> grew where older varieties failed, on higher land and on terraces climbing hillsides, and allowed double or even triple cropping in some areas. Together with better irrigation and water control, it “spectacularly increased rice yields.”{{afe_rice}}`,
        process: ["Environment", "Diffusion of crops"],
        connection: `Champa rice is a model case of crops diffusing along exchange networks. The College Board lists “new rice varieties in East Asia” beside bananas in Africa and citrus in the Mediterranean.{{ced:62}} <strong>Cause → effect → effect:</strong> more rice meant more people, larger cities and a more commercial economy (see Economic and Social).`,
      },
      {
        title: "Gunpowder weapons",
        when: "Formula recorded 1044",
        where: "Song China → Mongols → the world",
        body: `The Song military manual <em>Wujing zongyao</em> (1044) records the first true gunpowder formula. Song engineers used it for fire arrows, bombs of gunpowder and scrap iron launched by catapults, and “fire-spurting lances” with bamboo or metal barrels, early ancestors of the gun. Better weapons helped the Song hold off the Mongols for decades. But the Mongols adopted the technology too, often by capturing Chinese engineers and gunners.{{afe_gun}}`,
        process: ["Technology transfer", "Long-term change"],
        connection: `The College Board names “gunpowder from China” as a signature diffusion of the period.{{ced:61}} Carried by Mongol armies and along Eurasian routes, gunpowder weapons reached the Islamic world and Europe. Its full impact came after 1450, when gunpowder helped build the great land empires of Unit 3.`,
      },
      {
        title: "Seagoing junks & the magnetic compass",
        when: "Compass at sea by 1119",
        where: "China’s southeastern coast",
        body: `“The Song Chinese were world leaders in shipbuilding.” <strong>Watertight bulkheads</strong> improved buoyancy and protected cargo, <strong>stern-post rudders</strong> improved steering, and sounding lines measured the depth of the water. Navigators used a magnetized needle that pointed north and south, and the first reports of a <strong>compass</strong> used for sea travel date to 1119.{{afe_ship}} <em>Explore the cutaway junk and the water compass below.</em>`,
        process: ["Trade networks", "Technology transfer"],
        connection: `The College Board ties the growth of Indian Ocean trade to “the use of the compass, the astrolabe, and larger ship designs.”{{ced:57}} Junks joined Arab dhows and Indian ships on routes that “depended on environmental knowledge, including advanced knowledge of the monsoon winds.”{{ced:58}} Chinese maritime technology helped make the Indian Ocean the busiest sea network in the world.`,
      },
      {
        title: "Iron, steel & proto-industry",
        when: "Peak c. 1078",
        where: "Northern and central China",
        body: `During the Song, heavy industry grew astoundingly. <strong>Iron production</strong> reached about <strong>125,000 tons a year</strong> by 1078, six times the output of 800 CE. Workers produced everything from nails, tools and chains for suspension bridges to steel arrowheads and mass-produced iron armor, using huge bellows often driven by waterwheels.{{afe_iron}}`,
        process: ["Economic systems", "Comparison"],
        connection: `The College Board lists “steel and iron production” among Song China’s innovations and notes that “manufacture of iron and steel expanded in China” as Afro-Eurasian demand grew.{{ced:39|ced:54}} Output on this scale, powered by water and organized for mass production, is why historians call Song China <em>proto-industrial</em>. Europe would not reach comparable iron output until the eighteenth century.`,
      },
    ],
    artifacts: [
      {
        kind: "junk",
        title: "Cutaway: a seagoing junk",
        blurb: "Drag to rotate, scroll or pinch to zoom, and tap the markers. The starboard side is removed to show the watertight compartments and their cargo.",
      },
      {
        kind: "compass",
        title: "Mariner’s water compass",
        blurb: "Drag to turn the board. The floating needle keeps pointing north–south, just as it did for Song pilots. The rings mark the 24 directions and the 8 trigrams.",
      },
    ],
    synthesis: `Song technology was a system rather than a list of inventions. Champa rice fed workers, iron made tools and weapons, printing spread know-how, and junks with compasses moved goods to market. Its global effects came through the networks traced in this site: gunpowder and the compass traveled west, and new crops and cobalt traveled east.`,
  },
  // =====================================================================
  {
    id: "economic",
    letter: "E",
    hanzi: "商",
    pinyin: "shāng",
    gloss: "commerce",
    name: "Economic",
    title: "The First Commercial Revolution",
    bigIdea:
      "Song China built the most commercialized economy of its age, with paper money, canals, market towns and seaports. Mongol rule then plugged it into a trading world that stretched from Venice to Java.",
    scene: "economic",
    alt: "A merchant's counter with Yuan-dynasty paper banknotes, strings and loose copper cash coins, silver ingots, an abacus, folded silk and a blue-and-white porcelain jar.",
    caption:
      "Artist’s reconstruction · A merchant’s counter under the Yuan: a paper note modeled on the 1287 <i>Zhiyuan tongxing baochao</i> issue (with its printed warning to counterfeiters), strings of copper cash, silver ingots, an abacus, silk and a blue-and-white jar.",
    developments: [
      {
        title: "Paper money",
        when: "Government issue from the 1020s",
        where: "Song & Yuan China",
        body: `Merchants had long swapped paper certificates of deposit instead of hauling heavy strings of copper coins. In the 1020s the Song government took over the system, “producing the world’s first government-issued paper money,” even as coin output soared past 6 billion a year by 1085.{{afe_money}} The Yuan made paper the empire’s main currency. Marco Polo marveled at notes made from mulberry bark and stamped with the khan’s red seal. “Anyone forging it,” he reported, “would be punished with death,” and no one dared refuse them.{{polo:1: bk. 2, pt. 1, chap. 24}}`,
        process: ["Money economies", "Failed transfer"],
        connection: `The College Board lists “use of paper money” among the new forms of credit that expanded Silk Road trade.{{ced:54}} But money depends on trust. When the Mongol Ilkhanate issued copies of Yuan paper money in Persia in 1294, public distrust of the unfamiliar currency doomed the experiment.{{lumen}} <strong>Comparison:</strong> the same technology succeeded in China, where the state had long practice issuing it, and failed where people had no experience of it.`,
      },
      {
        title: "Commercialization & the Grand Canal",
        when: "Song through Yuan",
        where: "China’s core, south to north",
        body: `Song China’s economy became “increasingly commercialized while continuing to depend on free peasant and artisanal labor.”{{ced:39}} The old Tang system, which confined trade to fixed city markets and hours, broke down. Commerce spilled through whole cities, and bulk trade in rice drew farmers into periodic markets and fast-growing market towns.{{afe_comm}} The <strong>Grand Canal</strong>, first built under the Sui dynasty and later extended to the Yuan capital at Dadu (Beijing), carried grain from the rice-rich south to the political north.{{unesco_gc}}`,
        process: ["Urbanization", "Cause → effect"],
        connection: `The College Board counts “transportation innovations, like the Grand Canal expansion” among China’s key innovations.{{ced:39}} Surplus rice fed growing cities. Marco Polo called the Southern Song capital Hangzhou “beyond dispute the finest and the noblest in the world.”{{polo:2: bk. 2, pt. 3, chap. 76}} <strong>Change:</strong> this urban boom contrasts with the smaller cities of 13th-century Europe.`,
      },
      {
        title: "Quanzhou: emporium of the world",
        when: "10th–14th centuries",
        where: "Fujian coast",
        body: `Under the Song and Yuan, <strong>Quanzhou</strong>, which foreigners called Zayton, grew into one of the busiest seaports in the world. UNESCO’s listing, “Quanzhou: Emporium of the World in Song-Yuan China,” links administrative sites, religious buildings of diverse communities, and ceramic and iron production centers into a single system of production and overseas trade.{{unesco_qz}} Ibn Battuta used the port as his base in 1345–1346 and called China “the safest and most agreeable country in the world for the traveler.”{{orias}}`,
        process: ["Indian Ocean", "Diasporas"],
        connection: `Quanzhou was a hub of the Indian Ocean network in the College Board framework. Arab and Persian merchant communities settled in Chinese ports, just as “Chinese merchant communities” settled in Southeast Asia.{{ced:58}} <strong>Change after 1368:</strong> the early Ming favored official tribute missions over private trade, and Quanzhou’s golden age faded.`,
      },
      {
        title: "The Silk Roads under the Pax Mongolica",
        when: "c. 1250–1350",
        where: "Across Eurasia",
        body: `Mongol rule created the <strong>Pax Mongolica</strong>, a period of relatively safe travel and commerce across Eurasia. Chinese silk and spices moved west while European silver and cloth moved east, and maritime routes carried goods alongside the overland caravans.{{lumen}} As the Mongols expanded, “new people were drawn into their conquerors’ economies and trade networks,” and trade in luxury goods grew with caravanserais, credit and money economies.{{ced:54|ced:55}}`,
        process: ["Trade networks", "Unintended consequences"],
        connection: `The same roads carried disease. The College Board notes the continued “diffusion of crops and pathogens, with epidemic diseases, including the bubonic plague, along trade routes.”{{ced:62}} Along with war, famine and inflation, plague helped bring down the Yuan in 1368. <strong>Connectivity drove both the prosperity and the crisis of the period.</strong>`,
      },
    ],
    spotlight: {
      kind: "Primary source",
      title: "Marco Polo on the Great Kaan’s paper money",
      quote:
        "All these pieces of paper are issued with as much solemnity and authority as if they were of pure gold or silver… Anyone forging it would be punished with death.",
      attribution: "Marco Polo, <i>The Book of Ser Marco Polo</i>, trans. Henry Yule (1903), book 2, chapter 24.",
      image: "img/yuan-note.webp",
      imageAlt: "Reconstruction of a Yuan dynasty paper note: title 至元通行寶鈔 across the top, denomination 貳貫 above two strings of coins, red official seals, and a printed warning against counterfeiting.",
    },
    synthesis: `The Song–Yuan economy linked a farming revolution to a monetary one: surplus rice supported cities, canals and ports, and paper money made trade faster and cheaper. Mongol unity extended those links across Eurasia, and its costs arrived along the same routes as plague and inflation. The early Ming responded by turning toward tribute and control.`,
  },
  // =====================================================================
  {
    id: "social",
    letter: "S",
    hanzi: "家",
    pinyin: "jiā",
    gloss: "family",
    name: "Social",
    title: "Family, Class & Gender",
    bigIdea:
      "Beneath the rise and fall of dynasties, East Asian society rested on the patriarchal family, a Confucian ranking of social groups, and the labor of a vast peasantry whose numbers rose and fell with harvests, conquest and disease.",
    scene: "social",
    alt: "Aerial view of curving flooded rice terraces glowing in golden evening light, a small farming hamlet with lit windows among them and misty mountains beyond.",
    caption:
      "Artist’s reconstruction · Flooded rice terraces and a farming hamlet at sunset. Terraced fields and fast-ripening Champa rice fed the dense peasant population at the base of East Asian society.",
    developments: [
      {
        title: "The patriarchal, filial family",
        when: "Continuous",
        where: "China · Korea · Vietnam · Japan",
        body: `In Confucian teaching the family is the most basic unit of society. Everyone was to respect and obey their parents and put the family’s interests before their own, and marriage was essential so that male heirs could carry on the family line and honor the ancestors. Girls left their families when they married. By bearing sons, a woman eventually gained a respected place in her husband’s family, and mothers and grandmothers held real authority.{{afe_neo}}`,
        process: ["Continuity", "Cultural diffusion"],
        connection: `The College Board highlights “filial piety in East Asia” and the spread of Neo-Confucian values to neighboring societies.{{ced:39}} Through dynastic change and foreign conquest, the filial, patriarchal family was the region’s great <strong>social continuity</strong>. Joseon Korea wrote it even more strictly into law and custom after 1392.`,
      },
      {
        title: "Women’s lives: foot binding & property",
        when: "Song onward",
        where: "China (elite households first)",
        body: `The Song is often seen as a time when women’s status declined. Compared with the Tang, women were less active in politics and less often seen on the streets. Confucian teachers argued against widows remarrying, and <strong>foot binding</strong> began in Song times. Yet women’s property rights were relatively secure, and older women were often very powerful within their families.{{afe_neo}}`,
        process: ["Gender", "Continuity & change"],
        connection: `This matches the College Board’s phrase “Confucian traditions of both respect for and expected deference from women.”{{ced:39}} Foot binding, a painful practice that spread from elite households, became a lasting marker of status and of women’s confinement. It shows how Neo-Confucian ideals and elite fashion together could lock social expectations in place for centuries.`,
      },
      {
        title: "Class: scholars, farmers, artisans, merchants",
        when: "Song through Ming",
        where: "China",
        body: `Confucian thought ranked society by moral usefulness: <strong>scholars</strong> first, then the <strong>farmers</strong> who fed the realm, then <strong>artisans</strong>, with <strong>merchants</strong> last. In practice the examinations made the scholar-gentry an elite of education, open in principle to any man who mastered the classics,{{afe_sch}} while commerce made many merchants rich despite their low rank. Under the Yuan, a new <strong>ethnic hierarchy</strong> of Mongols, <em>semuren</em>, northern Chinese and southern Chinese cut across the old order.{{brit_yuan}}`,
        process: ["Social hierarchy", "Comparison"],
        connection: `Compare Europe’s hereditary estates or South Asia’s caste system. East Asia’s ideal ranking was based on moral usefulness, not birth. Real mobility, though, favored educated men from families that could afford years of study. <strong>Tension:</strong> merchants grew richer in the commercial revolution while Confucian ideals still ranked them lowest, a contradiction that ran through later Chinese history.`,
      },
      {
        title: "People, plague & the peasantry",
        when: "742 → 1100 → 1300s",
        where: "China",
        body: `Most East Asians were farmers. As rice cultivation expanded in central and southern China, the population grew from about <strong>50 million</strong> in 742 to <strong>100 million</strong> by 1100, probably more than all of Europe.{{afe_pop}} After the Song court fled south to Hangzhou in 1127, population and wealth shifted south as well.{{afe_keypts}} The fourteenth century reversed the trend: war, famine and epidemic disease, including plague carried along Afro-Eurasian trade routes,{{ced:62}} brought severe losses and fed the rebellions that ended Mongol rule.`,
        process: ["Environment", "Cause → effect"],
        connection: `East Asia’s social history shows environment and exchange shaping ordinary lives. A crop from Champa helped drive the population up, and pathogens moving along Mongol-era routes helped drive it down. <strong>Environmental change → demographic change → political change</strong>, a chain that runs from rice paddies to the fall of the Yuan.`,
      },
    ],
    synthesis: `East Asian society changed more slowly than its governments or economies. Family hierarchy, patriarchy and Confucian ideas of rank held steady from the Song to the Ming. Change came from below and from outside: new rice fed booming populations, commerce enriched merchants, conquest imposed ethnic ranks, and plague cut populations down.`,
  },
];

// ---------------------------------------------------------------------------
// Connections matrix (synthesis table)
export const MATRIX: { cat: string; development: string; process: string; link: string; cc: string }[] = [
  {
    cat: "P",
    development: "Examination bureaucracy · Yuan conquest · Ming tributary order",
    process: "State building",
    link: "Merit-based rule vs. Europe’s and Japan’s hereditary elites; the Yuan as one of four Mongol khanates; Zheng He in the Indian Ocean",
    cc: "Continuity of the Confucian state through change of dynasty",
  },
  {
    cat: "I",
    development: "Neo-Confucianism · print culture · Mongol-era astronomy · Hangul",
    process: "Cultural diffusion & technology transfer",
    link: "Buddhist ideas absorbed; paper and printing diffuse west; Persian astronomy moves east via the Mongols",
    cc: "Change in literacy and scripts inside a continuous Confucian canon",
  },
  {
    cat: "R",
    development: "Chan/Pure Land/Zen · Tripitaka Koreana · ancestor rites · Yuan pluralism",
    process: "Diffusion & syncretism",
    link: "Buddhism from India via the Silk Roads; Muslim diasporas in Chinese ports; Tibetan Buddhism at the Yuan court",
    cc: "Continuity of Buddhism and ancestor rites; change as Zen fuses with samurai culture",
  },
  {
    cat: "A",
    development: "Ma-Xia landscape painting · blue-and-white porcelain · Golden Pavilion",
    process: "Trade & cultural blending",
    link: "Persian cobalt and Islamic markets shape Jingdezhen wares; Song styles reshape Japanese painting",
    cc: "Change: porcelain becomes a global commodity",
  },
  {
    cat: "T",
    development: "Champa rice · gunpowder · junks & compass · iron and steel",
    process: "Environment & technology transfer",
    link: "Crop diffusion from Champa; gunpowder and compass diffuse west; monsoon navigation in the Indian Ocean",
    cc: "Change with global, long-term consequences",
  },
  {
    cat: "E",
    development: "Paper money · commercialization & Grand Canal · Quanzhou · Pax Mongolica",
    process: "Trade networks & money economies",
    link: "Silk Roads credit; Indian Ocean ports and diasporas; the failed Ilkhanate paper money of 1294; plague along trade routes",
    cc: "Commercial revolution (change), then Ming contraction",
  },
  {
    cat: "S",
    development: "Filial family · women’s status · class ranking · population & plague",
    process: "Comparison & environment",
    link: "Compare caste and European estates; disease diffuses along Mongol-era routes",
    cc: "Strong continuity (family, patriarchy) amid demographic change",
  },
];

export const CONCLUSION = `From the examination cell to the treasure ship, East Asia between 1200 and 1450 shows the two forces AP World History asks us to track together. The first is <strong>continuity</strong>: Confucian government, the filial family, rice agriculture and Buddhism outlasted the Song, the Mongols and the rise of the Ming. The second is <strong>connection</strong>. Champa rice came from Vietnam, cobalt from Persia and astronomers from Maragheh, while printing, paper money, gunpowder, the compass and porcelain went out along the Silk Roads and the Indian Ocean. The Mongol century was the hinge: it shattered the region, then reconnected it, spreading prosperity and plague alike. By 1450, Ming China had turned inward, Joseon Korea had created its own alphabet, and Japan’s samurai had built a political order of their own. Each had adapted a shared inheritance to its own ends.`;

// Dynasty chart (years clamped to the 1180–1460 view window)
export const DYNASTIES: { row: string; items: { name: string; from: number; to: number; tone: string; note?: string }[] }[] = [
  {
    row: "China",
    items: [
      { name: "Jin (north)", from: 1115, to: 1234, tone: "d" },
      { name: "Southern Song", from: 1127, to: 1279, tone: "a" },
      { name: "Yuan (Mongol)", from: 1271, to: 1368, tone: "b" },
      { name: "Ming", from: 1368, to: 1644, tone: "a" },
    ],
  },
  {
    row: "Korea",
    items: [
      { name: "Goryeo", from: 918, to: 1392, tone: "a", note: "Mongol vassal from the 1250s" },
      { name: "Joseon", from: 1392, to: 1897, tone: "c" },
    ],
  },
  {
    row: "Japan",
    items: [
      { name: "Kamakura shogunate", from: 1185, to: 1333, tone: "a" },
      { name: "Muromachi (Ashikaga)", from: 1336, to: 1573, tone: "c" },
    ],
  },
  {
    row: "Vietnam",
    items: [
      { name: "Lý", from: 1009, to: 1225, tone: "d" },
      { name: "Trần", from: 1225, to: 1400, tone: "a" },
      { name: "Hồ", from: 1400, to: 1407, tone: "d" },
      { name: "Ming rule", from: 1407, to: 1427, tone: "b" },
      { name: "Lê", from: 1428, to: 1789, tone: "c" },
    ],
  },
];

export const KEY_DATES: { year: string; text: string; cat: string }[] = [
  { year: "1206", text: "Temüjin proclaimed Chinggis Khan", cat: "P" },
  { year: "1231", text: "Mongol invasions of Korea begin", cat: "P" },
  { year: "1237–48", text: "Tripitaka Koreana carved", cat: "R" },
  { year: "1271", text: "Khubilai proclaims the Yuan dynasty", cat: "P" },
  { year: "1274 & 1281", text: "Mongol invasions of Japan fail", cat: "P" },
  { year: "1279", text: "Last Southern Song resistance crushed", cat: "P" },
  { year: "1288", text: "Đại Việt victory at Bạch Đằng", cat: "P" },
  { year: "1294", text: "Ilkhanate’s paper-money experiment fails", cat: "E" },
  { year: "1313", text: "Yuan restores exams on Zhu Xi’s commentaries", cat: "I" },
  { year: "1336", text: "Ashikaga (Muromachi) shogunate begins", cat: "P" },
  { year: "1345–46", text: "Ibn Battuta visits China", cat: "E" },
  { year: "1351", text: "The David Vases are dedicated", cat: "A" },
  { year: "1368", text: "Ming dynasty founded", cat: "P" },
  { year: "1377", text: "Jikji printed with metal type", cat: "I" },
  { year: "1392", text: "Joseon dynasty founded in Korea", cat: "P" },
  { year: "1397", text: "Kinkaku (Golden Pavilion) begun", cat: "A" },
  { year: "1405–33", text: "Zheng He’s seven voyages", cat: "T" },
  { year: "1428", text: "Lê dynasty restores Vietnamese rule", cat: "P" },
  { year: "1443", text: "King Sejong creates Hangul", cat: "I" },
];
