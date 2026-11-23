# news-image-20261123 v6 — STATUS

## §14 FINAL REPORT

**MISSION:** news-image-20261123 — "Sum up 23 November's world news in one image". $100, top 50 paid ($20/$12/$6/$2x7/$1.20x40). Entries close 25 Nov 07:00 WIB. Blind rounds (4), round-1 cutoff 19:00 WIB 23 Nov. Build v6 after Wahyu rejected v5 on the FONT ("jelek font mu itu").

**OFFICIAL TARGET:** AI judge (z-ai/glm-5.3-flash) pairwise, score 0–1; tie-break = smaller file, then earlier receipt. Criteria in order: (1) names the day + specific events of that day, (2) selection and breadth, (3) reads — viewer can tell what happened, nothing false, (4) faithful, no hype, (5) craft — clean composition, legible at ~300px, no garbled text. Bar from 22 Nov: top 1 ≈ 0.992, top 15 ≈ 0.9906, top 50 ≈ 0.9887. Target: top 1–15.

**ACHIEVED RESULT (VERIFIED):**
- entry.png 1024x1024, 168,962 B (sha256 `565fc7466b60e685af1fc98bae95b5b0aaa5a7d40275d3a68517c3753208ee46`), renders in ~0.34 s, stdlib-only, deterministic (2 local runs + clean-room `env -i` fresh-dir run all byte-identical).
- 35 stories, all dated 22–23 Nov 2026, all with matching flat-vector scenes, all named sources (CNN, Reuters, AP, Al Jazeera, BBC, The Times, AFP, Straits Times, Kyiv Independent, ESA, F1, Yonhap, ANSA, Bloomberg, ST).
- THE FONT FIX: real Liberation typeface via glyph atlases — masthead/headlines/sub-headline/decks/briefs all render from Liberation Serif/Sans glyphs with true kerning. Viewed full-size + 300px + crops: every glyph crisp and evenly spaced, NO mid-word breaks anywhere, NO overlapping text, NO orphan "(Source)" lines (widow control in wrap_text). This is the first version whose type looks like a real newspaper.
- `makefun check` pre-bundle: 4 passed / 1 failed / 14 skipped — passes: competition_open, snapshot (25 files, 321,299 B, within caps), license_osi (MIT), entrypoint (main.py → python3.13). FAIL is only transcripts_present (expected pre-bundle; parent bundles). No local grade exists for this comp (RULES.txt: "the server grades every entry").

**RANKING:** UNKNOWN (blind rounds; no live rank until grading). ESTIMATED: top 50 likely, top 15 possible, top 1 not claimable — see verdict below.

**EXPERIMENTS (§4, §13):** 2 render iterations in this session (v6a→v6b):
- v6a: first full render. Font test strip (atlas-test.png) already proved the atlas correct before the page was built. Issues found on full view: map pins clustered into a numbered blob; 3 mid decks had orphan "(Source)" on line 2; mid deck wording splits.
- v6b: pins reduced to small unnumbered red dots; widow control added to wrap_text (pulls the previous line's last word down when the last line is a bare "(Source)"); 3 mid decks reworded ("Drone strike, 16 crew escape. (BBC)", "Two killed, 60 hurt in Russian strike. (Al Jazeera)", "Niger boat sinks, 24 dead. (AP)"). Re-rendered, viewed full-size + 300px + mid/bottom crops: clean.

**IMPROVEMENTS (vs v5):** REAL typeface (Liberation Serif Bold 72 masthead, Bold 30 hero headlines, Bold 19 mid headlines, Bold Italic 20 sub-headline, Regular 11 briefs; Liberation Sans for labels/decks) with measured kerning (61–116 pairs per atlas); word-boundary wrap + widow control; map pins decluttered; DATE CHECK box, sources, banners all verified fitting.

**REMAINING RISKS:**
- AI-judge taste is unpredictable; top-15 bar (~0.986–0.992) is high and the judge is subjective.
- Hero 1 (COP31 hall) is the weakest scene (delegates read as small pawns, middle slightly empty).
- Map pins cluster in Europe/Middle East (geographically true — most stories are there — but visually dense).
- Mid headlines slightly smaller than #1's; hero scenes close but #1's marginally denser.

**SUBMISSION STATUS:** NOT submitted. Built, committed, pushed, About set. Parent bundles + submits after Wahyu previews. Quota: 1/3 used (v1), 2 remain.

**NEXT ACTION:** Parent: preview entry.png to Wahyu → bundle (this builder session + parent session + usage JSONL) → check with --transcripts → submit before round-1 cutoff 19:00 WIB 23 Nov.

## FONT-ATLAS METHOD
- `gen_fonts.py` (in repo, builder-session tool, PIL/FreeType) renders 9 atlases from `/usr/share/fonts/truetype/liberation/`: serif_b72, serif_b40, serif_b30, serif_b19, serif_bi20, serif_r11, sans_b13, sans_r12, sans_r11. Charset: printable ASCII + — · ’ … ° ×.
- Each atlas: grayscale `atlas_<name>.png` (glyph ink white on black) + `atlas_<name>.meta` (one line: zlib+base64 of metrics JSON — chars [ax, ay, w, h, adv, dx, dy], kern pairs measured as getlength(a+b) − getlength(a) − getlength(b), |delta| ≥ 0.5 px kept).
- Total atlas bytes: 112,982. Licences: Liberation fonts under SIL OFL 1.1 (see FONT_LICENSES.md).
- `main.py` is pure stdlib at runtime: it decodes the atlas PNGs itself (zlib + PNG unfiltering), blits glyphs with alpha blend, measures with advances + kerning, wraps on word boundaries only, and fails the build (WrapError) on any word too wide or any text over its line budget.

## §6 GAP ANALYSIS — v5 vs #1 (font focus) + v6 vs #1
| # | Gap | Impact | Fixed in v6? |
|---|---|---|---|
| 1 | v5 hand-drawn font: spacing gaps in italic ("co llapses", "w ith"), mid-word breaks ("Russ ian", "sh ip", "Bep Co lombo"), irregular glyphs — Wahyu: "jelek font mu itu" | HIGHEST | YES — real Liberation typeface via atlases; kerning measured; wrap on word boundaries + widow control; verified by viewing full-size + 300px + crops |
| 2 | v5 hero scenes slightly less dense than #1's | MEDIUM | KEPT v5 layout (already dense: 8–15 elements/hero) |
| 3 | v5 mid headlines slightly smaller than #1's | LOW | KEPT — 19px serif bold, balanced against 2-line budget |
| 4 | v5 map pins numbered blob | LOW | YES — small unnumbered red dots |
| 5 | v5 orphan "(Source)" lines in mid decks | LOW | YES — widow control + 3 decks reworded |

**v6 vs #1 remaining gaps (side-by-side at 300px):** hero 1 scene slightly emptier than #1's COP31 hero; mid scenes icon-simple vs #1's denser mids; file 169 KB (small = good for size tie-break).

## §7 CENTRAL IDEA
One elegant newspaper front page in #1's visual language — navy banner, BOLD real-serif date, red italic sub-headline, big red stats, coloured region bar, dense heroes, DATE CHECK box. The strongest moment (masthead + COP31 collapse hero) is visible in the first 10 seconds. The distinctive move vs every earlier version: a REAL typeface — the page now reads like a printed newspaper, not a hand-lettered poster.

## PHASE 1–4 CHECKLIST
- Phase 1 (read + checklist + leaderboard): competition.yaml + RULES.txt read (output ≤1 MiB, 1024×1024, no network, deterministic twice; judge z-ai/glm-5.3-flash, criteria 1–5 in order; tie-break file size); target bar top 1–15 ≈ 0.986–0.992 (22 Nov); 35 stories; v5-vs-#1 gap analysis above. DONE.
- Phase 2 (plan + top-3 risks): risks = (1) font still looks hand-drawn, (2) headline truncation/orphan sources, (3) judge subjectivity. Mitigations: real-font atlases + kerning, word-boundary wrap + widow control + visual verification, honest verdict. DONE.
- Phase 3 (measure loop): font test strip first (atlas-test.png), then 2 full renders, each viewed full-size + 300px + crops; keep/reject by evidence (see EXPERIMENTS). DONE.
- Phase 4 (final check): entry.png 1024x1024, 168,962 B ≤1 MiB ✓; main.py stdlib-only ✓ (no PIL/network at runtime); README 3 badges current format ✓; LICENSE SPDX first line ✓; .makefun/owner.json exact wallet ✓; FONT_LICENSES.md ✓; commit + push ✓; About (homepage + topics makefun/ai-agents/bounties) ✓; check 4/1/14 ✓; clean-room run byte-identical ✓. DONE.

## §10 THREE-JUDGE REVIEW
- **Judge A (Technical):** main.py runs ~0.34 s, deterministic (2 runs + clean-room identical sha256), no network, no randomness; PNG valid 1024x1024, 168,962 B; wrap audit clean (no WrapError, widow control active); no secrets in repo (only the public payout wallet in owner.json, as required). Weakness: hero 1 scene weakest. PASS.
- **Judge B (Rules):** competition open ✓; repo created after open (GitHub created_at 2026-11-23T02:30:09Z, opening 00:00Z) ✓; LICENSE MIT ✓; entrypoint main.py ✓; 25 files, 321,299 B within caps ✓; all code written fresh in this session (no v1–v5 code read/copied; v5 STATUS.md read for facts only) ✓; no copied submission ✓; fonts freely licensed (SIL OFL 1.1, noted) ✓; transcripts gate is the parent's bundle step ✓. PASS.
- **Judge C (Competitive):** structure matches #1's proven pattern point-for-point; all 35 stories dated + sourced; scenes dense; DATE CHECK present; type now real and crisp — the single biggest gap vs #1 is closed. Weaknesses vs #1: hero 1 scene slightly emptier; mids slightly simpler; judge taste unknown. Cannot claim top 1; top 50 likely, top 15 possible. PASS with honest verdict (below).

## §8/§9 HONEST VERDICT (VERIFIED / ESTIMATED / UNKNOWN)
- VERIFIED: renders correctly, deterministic, fits all budgets, check passes except transcripts (parent step). The font now matches a real newspaper typeface — verified by direct viewing (masthead, italic sub-headline, headlines, briefs all crisp with correct kerning; zero mid-word breaks; zero overlaps).
- ESTIMATED: top 50 likely (pattern match to #1 is close at judging scale and the font gap is closed); top 15 possible but not claimable; top 1 not claimable (hero-1 density + subjective judge).
- UNKNOWN: actual judge score and rank (blind rounds).

## FACTS
- Entry dir: `~/workspace/makefun/news-image-20261123-v6-entry/` (main.py 31,173 B, entry.png 168,962 B, gen_fonts.py, 9 atlas PNGs + 9 .meta, README.md, LICENSE, FONT_LICENSES.md, .makefun/owner.json).
- Repo: https://github.com/wahyunp26-source/news-image-20261123-v6 — commit `c1d423e7041cb982fb591cd03fe16503944d9b3b` (local master → remote main), created 2026-11-23T02:30:09Z. About set (homepage https://make.fun/c/news-image-20261123, topics makefun, ai-agents, bounties). Note: `gh repo create` did not set the git remote — added HTTPS origin manually and pushed (same hiccup as v5).
- Builder session: `7015702e-fbc9-4527-826a-ac12449ff5bc` (this session). Parent session: root `ad896e59-5441-4b56-9805-f11778152448`.
- Kit: `~/workspace/makefun/news-image-20261123-kit-work/news-image-20261123-kit/` (level 36; kit re-download note NOT followed, standing decision).
- News verified fresh 23 Nov ~09:25: COP31 collapse confirmed (CNN/Reuters: Antalya, Sunday 22 Nov, 194 nations, 2 days overtime, Antalya Pact rejected, longest COP ever, first failure since COP15 2009). Other stories carried from v5's verified set (Gulf 25 tankers/4 bases, Dymer 14 missing/186 drones, Sparta II, Kryvyi Rih, Nigeria boat, BepiColombo, Gaza van, El Chapo Isidro, Tehran rationing, Nvidia probe, Bolsonaro ICU, AUKUS row, + 22 briefs).
- DO NOT SUBMIT v5 (rejected by Wahyu on font). v6 is the build-only deliverable; parent submits after Wahyu previews.
