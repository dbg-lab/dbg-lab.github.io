# Site inspiration — labs whose websites we want to steal from

Running list of lab sites worth looking back at, with notes on *what specifically*
is good and how it would map onto our Hugo + hugo-scroll setup.

---

## Disease Transcriptomics Lab (Nuno L. Barbosa-Morais, GIMM / NMS-UNL)

<https://diseasetranscriptomicslab.github.io/> · repo: `diseasetranscriptomicslab.github.io` (GitHub Pages)

Nuno is a former colleague of dbg's. Same single-page scroll flow as ours, but a much
richer people section — this is the main reason it's here.

### Stack

Hand-rolled static site, **no generator** (no Jekyll, no Hugo). Plain
`index.html` + `css/styles.css` + `js/main.js`, served from GitHub Pages.
Footer credits "Built with Claude Sonnet 4.6."

- Sections live as separate partials in `sections/*.html` (`hero`, `about`, `team`,
  `research`, `software`, `news`, `outreach`, `publications`, `alumni`, `location`)
  and are **fetched at runtime** by `loadSection()` in `js/main.js`, replacing empty
  `<div id="section-team">` placeholders.
- Design tokens all in one `:root` block at the top of `styles.css` — `--navy #0D1B2A`,
  `--teal #087c72` (annotated with its WCAG contrast ratio), `--fog #F0F4F8`,
  `--radius`, `--shadow` / `--shadow-lg`, `--font-display: 'Playfair Display'`,
  `--font-body: 'DM Sans'`. Retheme the whole site by editing that block.
- Section backgrounds alternate automatically (`--fog` / `--white`) in JS rather than
  being hard-coded per section.
- `.fade-up` + IntersectionObserver for scroll-triggered entrance, with a hand-set
  `style="transition-delay:.05s"` … `.3s` stagger down each grid.

**Don't copy the runtime `fetch()` of sections.** It breaks with no JS, is invisible
to crawlers/link previews, and doesn't work over `file://` (his `main.js` even has a
`checkProtocol()` guard telling you to run `python3 -m http.server`). Hugo already
assembles partials at build time, which is strictly better. Everything below is
about *content model and visual design*, not the loading mechanism.

### Team section — the part dbg likes

Order down the page: section label ("People") → title ("Meet the team") → **group
photo** (full-width, rounded) → **PI card** → **3-column member grid** → a small
"Want to join us?" call-to-action box at the bottom of the same section.

**PI card** — `display:grid; grid-template-columns: 320px 1fr`, big shadow, photo
column stretches to match the bio height (`min-height:380px`, `object-fit:cover`,
`object-position:center top` so the face stays in frame on tall portraits).
Fields: pill badge "PRINCIPAL INVESTIGATOR" → name + country-flag emoji →
long first-person bio → `**Research interests:**` line with `·` separators →
email with a small inline SVG envelope icon → pill social links.

**Member cards** — `repeat(3, 1fr)` grid, → 2 cols at 860px, → 1 col at 560px.
Each card is photo-on-top / info-below, and carries a lot more than ours does:

| Field | Notes |
|---|---|
| Photo | `aspect-ratio: 5/4`, `object-fit:cover`, `object-position:center top`; gradient placeholder behind it, and an initials-circle fallback (`.member-photo-placeholder`) for people without a photo yet |
| Role badge | tiny uppercase teal letterspaced caps above the name, e.g. "POSTDOCTORAL RESEARCHER", "PHD STUDENT" — and usefully, "PHD STUDENT (STARTS SEP 2026)" for incoming people |
| Name + flag | name in the display serif, country flag emoji beside it |
| Bio | short, **first person**, with a "fun fact" — reads like a person, not a directory entry |
| Interests | `**Interests:**` + `·`-separated phrases |
| Email | inline SVG envelope + mailto |
| Social | pill-shaped outline links: ORCID · LinkedIn · Bluesky · GitHub. Convention is `href="#"` to hide one |

Hover: `translateY(-4px)` + shadow upgrade. No accordion, no modal — everything is
visible on the card, which is why the section reads as substantive rather than as a
grid of headshots.

Nice touch: `sections/team.html` opens with a ~30-line HTML comment that is a
**how-to-edit guide** for lab members (duplicate a `.member-card` block, which
class holds what, how to swap the placeholder for a real photo, even a list of
country flag emojis). Worth imitating in our shortcode docs.

### Alumni section — also better than ours

Grouped by **departure year** (2026, 2024, 2023 …), each year a row:

- Name, hyperlinked with a tiny inline LinkedIn glyph
- Colored role badge (`badge-phd`, `badge-trainee`, …)
- Years in lab ("2015–2024")
- Optional program context ("LisbonBioMed PhD Program")
- **"Pubs with lab: [1] [2] [3] …"** — numbered links straight to DOI/PubMed
- A strip of small portrait thumbnails per year group

Plus a group-photo slideshow of lab photos going back years (`initAlumniSlideshow`,
labeled "December 2015" etc.) and a hover interaction on the timeline.

The pubs-with-lab links are the standout idea — it turns the alumni list into
evidence of output instead of a courtesy list, and we already have the BibTeX to
generate it from `data/publications.yaml`.

### Other sections worth revisiting later

- **Research** — one card per project/theme with a colored top stripe (solid for one
  theme, gradient when a project spans two), collapsible accordion body, people
  attributed on the card, keyword pills, plus both a theme filter and a free-text
  keyword filter across cards. Relevant to our TODO #1 (carousel for featured
  research) — his accordion + filter is probably the better answer than a carousel.
- **Software/Tools** — same filter pattern, separate section from research.
- **News** — data-driven from `js/news-data.js` (a plain JS array), not hand-written
  HTML. Also pulls a live Bluesky feed and a YouTube feed for their BIOMICS project.
- **Hero** — typewriter animation over the lab tagline.
- **About** — short mission text plus three "pillars".

### Concrete deltas for our site

Ours (`content/homepage/people.md` + `layouts/shortcodes/lab-member-card.html`)
currently supports only `image`, `name`, `title`. To get to Nuno's density:

1. Extend `lab-member-card` with `bio`, `interests`, `email`, `orcid`, `linkedin`,
   `github`, `bluesky`, `flag`, and a `starts` variant of the role badge — or move
   people to `data/people.yaml` and render the grid from it, which is TODO #4
   ("Set up code for lab members portraits and info from a yaml file"). YAML is the
   better path; it also lets alumni, current members, and the join-us copy share one
   source.
2. Add an initials-circle placeholder so a new member can go up before their photo exists.
3. Standardize the photo crop (`aspect-ratio` + `object-position:center top`) — our
   headshots are currently inconsistent.
4. Add a lab group photo above the people grid (TODO #5, "social / lab fun section").
5. Alumni: add years-in-lab, current position, and pubs-with-lab links generated from
   `data/publications.yaml`.
6. Keep our Razzmatazz red doing the work his teal does — role badges, section labels,
   hover borders. That's TODO #4's "add red in more places."
