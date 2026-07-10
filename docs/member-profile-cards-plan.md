---
title: "Lab Website — Member Profile Cards (card → dialog morph) — Plan / Agent Brief"
status: draft-for-review
created: 2026-07-10
updated: 2026-07-10
owner: Dan Goodman
intended-runner: autonomous Claude Code agent on LXC102 (NOT the Mac)
repo: dbg-lab.github.com  →  github.com/dbg-lab/dbg-lab.github.io
tags: [lab-website, hugo, frontend, people, dialog, view-transitions]
---

# Member Profile Cards — click to expand into a dialog

## Goal
Let a visitor **click a lab-member card** on the People section and have that card
**smoothly morph/expand into a centered dialog** showing richer info: academic
background, project blurb, hobbies/interests, and links (personal homepage +
academic/social). Must look native to the existing hugo-scroll theme.

The historical blocker was purely design/polish. This brief locks the approach so an
implementing agent can build it without re-deciding anything.

## Phasing
- **Phase 1 (now — for the LXC102 agent):** build the card → dialog morph mechanism
  + on-theme styling, using **placeholder/stub content** (all fields optional, so
  cards work with little or no data). Work happens on the **`test` branch**.
- **Phase 2 (later — separate workstream):** the *content pipeline* — collect real
  member info via a **Google Sheet** that lab members can edit, pull it into the
  site, then announce it (Slack + email) and mirror it into Notion. See
  "Phase 2 — content pipeline" below. Do NOT block Phase 1 on this.

## Decisions (LOCKED — do not re-open)
1. **Interaction = native `<dialog>` that morphs from the clicked card**, using the
   **View Transitions API** for the expand animation (progressive enhancement).
   Base is the standards `<dialog>` element via `showModal()`; the morph is layered
   on top and **degrades gracefully** to a plain fade where View Transitions is
   unsupported or `prefers-reduced-motion` is set. Reference implementation we're
   following: Thomas Günther, "Dialog view transitions"
   (https://medienbaecker.com/articles/dialog-view-transitions).
2. **No modal library, no focus-trap library.** Native `<dialog>` + `showModal()`
   already gives focus trapping, inert background, Esc-to-close, and `::backdrop`.
   No jQuery, no build step.
3. **Authoring = extend the existing shortcode**; content stays in
   `content/homepage/people.md`. Add optional params + a markdown project blurb as
   the shortcode's inner content. NO migration to a data file.
4. **Fields (ALL optional; blank → not rendered):**
   - Academic background / education
   - Project blurb (free-text markdown paragraph)
   - Hobbies / interests
   - Links: personal homepage, Google Scholar, LinkedIn, GitHub, ORCID, email
     (render only the ones present, as small icon links)
5. **Works for BOTH current members and alumni via one shared mechanism.** We are
   NOT populating alumni content now, but the alumni card must support the same
   dialog so a future alum can add e.g. a "current position" with zero rework.
   Support an optional `position` field for that.
6. A card is clickable **only if it has extra content**. Cards with just
   image/name/title render exactly as today and are NOT clickable (backward compat).

## How the site works today (grounding for the implementer)
- Static Hugo site, theme `hugo-scroll` (GhostScroll snap-scroll). Run locally with
  `hugo server`.
- **The theme has NO dialog/modal/overlay/popup of any kind to reuse.** Its only JS
  is `themes/hugo-scroll/assets/js/{index.js (scroll behavior), jquery-3.6.3.min.js,
  css-vars-ponyfill.min.js}`. We build the dialog from scratch (trivial with
  `<dialog>`).
- **Theme integration points (use these):**
  - `layouts/partials/custom_head.html` and `layouts/partials/custom_body.html` are
    explicit user-override partials (injected before `</head>` / before `</body>`).
    Override them in the site's own `/layouts/partials/` to inject the shared dialog
    element + controller `<script>` ONCE, site-wide. This is cleaner than emitting a
    script per card.
  - `static/css/custom.css` (served at `/css/custom.css`) holds ALL custom styling.
- People section content: `content/homepage/people.md`, built from shortcodes:
  - `layouts/shortcodes/lab-members.html` — grid container (`<div class="lab-members-grid">{{ .Inner }}</div>`)
  - `layouts/shortcodes/lab-member-card.html` — a card; currently takes `image`, `name`, `title`
  - `layouts/shortcodes/alumni-section.html` — collapsible "Alumni" header + hidden `<div>`
  - `layouts/shortcodes/lab-alumni.html` / `lab-alumni-card.html` — alumni grid + card (`image`, `name`, `title`)
- **Local interactivity idiom to match:** small inline `<script>` blocks (see
  `alumni-section.html` `toggleAlumniSection()` swapping a Font Awesome chevron;
  `publications.html` collapse + `DOMContentLoaded`). Font Awesome is already loaded.
- **Relevant existing CSS** in `custom.css`: `.lab-member-card`,
  `.lab-member-photo` (170×170, `border-radius: 50%`, `object-fit: cover`),
  `.lab-member-info/name/title`, responsive `@media` blocks. Alumni mirror these
  under `.lab-alumni-*`.
- **Theme design tokens (use these — do not invent colors):**
  - `--color-background: #f6f6f3` (off-white panels)
  - Penn blue accent: `#0C5797`
  - Fonts: `--font-display` (uppercase, light — used by `.lab-member-name`),
    `--font-primary` (body); plus `--text-*`, `--weight-*`, `--leading-*`
  - Card idiom: `border-radius: 15px`; hover lift `translateY(-2px)` +
    `box-shadow: 0 8px 25px rgba(0,0,0,0.1)`
- Member photos are square images circle-cropped by CSS. Some source headshots have
  non-transparent backgrounds (e.g. `gloria-liu.jpg` had white corners filled with
  its own sky-blue); the dialog's header image should also be circle-cropped so
  backgrounds stay clean.

## The chosen technique: `<dialog>` + View Transitions morph
Follow the Medienbäcker pattern. The `view-transition-name` (e.g. `member-card`) is
**assigned transiently to ONLY the clicked card at open time** and handed off to the
dialog — since only one dialog is open at a time, no per-card unique names are
needed. Skeleton to adapt (put in the shared controller):

```js
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;

function openMemberDialog(cardEl, dialogEl) {
  const cardImg = cardEl.querySelector(".lab-member-photo");
  const dialogImg = dialogEl.querySelector(".member-dialog-photo");

  // Fallback: no View Transitions support (or reduced motion) → plain open.
  if (!document.startViewTransition || REDUCED) {
    dialogEl.showModal();            // native focus-trap, Esc, ::backdrop for free
    return;
  }
  cardImg.style.viewTransitionName = "member-card";     // 1. name the source
  document.startViewTransition(() => {
    cardImg.style.viewTransitionName = "";              // 2. drop from source
    dialogImg.style.viewTransitionName = "member-card"; // 3. name the dialog
    dialogEl.showModal();                               // 4. open
  });
}

// Closing: intercept so we can morph back to the card, then close.
dialogEl.addEventListener("cancel", (e) => {            // Esc
  e.preventDefault();
  closeMemberDialog(currentCardEl, dialogEl);
});
// (also wire the ✕ button and backdrop click to closeMemberDialog)

function closeMemberDialog(cardEl, dialogEl) {
  const cardImg = cardEl.querySelector(".lab-member-photo");
  const dialogImg = dialogEl.querySelector(".member-dialog-photo");
  if (!document.startViewTransition || REDUCED) { dialogEl.close(); return; }
  dialogImg.style.viewTransitionName = "member-card";
  document.startViewTransition(() => {
    dialogImg.style.viewTransitionName = "";
    cardImg.style.viewTransitionName = "member-card";
    dialogEl.close();
  }).finished.finally(() => { cardImg.style.viewTransitionName = ""; });
}
```

Notes for the implementer:
- Prefer **one shared `<dialog>` element** whose inner content is populated from the
  clicked card's data on open (keeps a single element + single controller). The card
  can carry its rich content in a hidden template / data-attributes, or the dialog
  is filled from per-member hidden blocks the shortcode emits. Either is fine; keep
  it simple and keep markdown blurb as real HTML (not stuffed into an attribute).
- Backdrop-click close: compare `event.target === dialog` (clicks on the `::backdrop`
  land on the dialog element itself).
- Style the morph via `::view-transition-group(member-card)` /
  `::view-transition-old/new` only if needed; the default cross-fade+size morph is
  usually enough.

## Design spec for the dialog
- **Trigger / affordance:** the **whole card is clickable** (default — no separate
  "View profile" button). Give clickable cards `cursor: pointer` and keep the
  existing hover lift. A *stronger* visual cue that a card is clickable is desired
  but NOT yet designed — leave a light touch for now (cursor + hover lift) and we'll
  explore a clearer cue later (candidates: a faint "click for more" hint, an icon on
  hover, a subtle border/glow). Keyboard: `role="button"`, `tabindex="0"`, open on
  Enter/Space.
- **Panel:** native `<dialog>`, styled on-theme — `--color-background` panel, `15px`
  radius, soft shadow, Penn-blue (`#0C5797`) accents (thin top bar / link color /
  divider), comfortable padding. Style `dialog::backdrop` as a dim layer
  (`rgba(0,0,0,~0.5)`, optional slight blur).
- **Layout:** circular header photo (`.member-dialog-photo`), name in `--font-display`
  uppercase, title italic, then sections rendered only if populated: *Background* ·
  *In the lab* (blurb) · *Outside the lab* (hobbies) · a row of icon links. For
  alumni, optional *Now* (current position) line.
- **Responsive:** on narrow screens the dialog becomes a near-full-width sheet with
  internal scroll; never exceeds viewport. (`<dialog>` + `showModal()` already locks
  background interaction; add `overflow` handling on the panel.)
- **A11y:** `<dialog>`+`showModal()` gives focus trap, inert background, Esc, and
  focus restore for free. Still add `aria-labelledby` → the member name, and ensure
  the ✕ button is a real `<button>`. Skip the morph under `prefers-reduced-motion`
  (handled above) — the dialog still opens with the native fade.

## Implementation approach
1. **Extend `layouts/shortcodes/lab-member-card.html`:** new optional params
   `homepage`, `education`, `interests`, `position`, `scholar`, `linkedin`, `github`,
   `orcid`, `email`; project blurb = `.Inner` (`{{ .Inner | markdownify }}`).
   Compute a stable id from the name (`{{ .Get "name" | urlize }}`) and a `hasDetail`
   flag. If `hasDetail`, render the card as an activatable button
   (`role`/`tabindex`/`data-*` hooks + affordance) and emit the member's rich content
   (hidden block or template) for the dialog. Emit each field only when non-empty.
2. **Share the mechanism with alumni.** Prefer factoring a shared partial
   (`layouts/partials/member-card.html`) called by both `lab-member-card.html` and
   `lab-alumni-card.html`. If a full refactor feels risky, at minimum mirror the
   same markup/classes/data-hooks into the alumni card so shared CSS/JS Just Works.
3. **Add the shared dialog + controller ONCE** via a site-level
   `layouts/partials/custom_body.html` override (the theme injects it before
   `</body>`). One `<dialog>` element + the View-Transitions controller above.
4. **Add CSS to `static/css/custom.css`:** dialog panel + `::backdrop`, header photo,
   sections, icon-link row, card affordance/hover, `@media` responsive sheet, and
   optional `::view-transition-*` tuning. Reuse the theme tokens; no off-theme colors.
5. **Populate content in `content/homepage/people.md`** where Dan provides it; leave
   the rest blank. Do NOT invent bios — stub blank and flag what's needed.

## Files expected to change
- `layouts/shortcodes/lab-member-card.html` (extend)
- `layouts/shortcodes/lab-alumni-card.html` (share mechanism)
- `layouts/partials/member-card.html` (new, if factoring shared markup)
- `layouts/partials/custom_body.html` (new site override — shared `<dialog>` + JS)
- `static/css/custom.css` (dialog + affordance styles)
- `content/homepage/people.md` (per-member content Dan supplies)

## Acceptance criteria
- Clicking (or Enter/Space on) a card with detail opens the dialog; the card visibly
  **morphs/expands** into the panel where View Transitions is supported.
- ✕ / backdrop / Esc close it (morphing back); focus is trapped while open and
  restored to the card on close.
- `prefers-reduced-motion` and unsupported browsers get a clean fade, no errors.
- Cards with no extra content are unchanged and not clickable; only populated fields
  appear; all fields optional.
- Works identically for a current member and an alumni card given the same data.
- On-brand in `hugo server` (fonts, `#f6f6f3` panel, `#0C5797` accents, 15px radius,
  soft shadow), desktop + mobile; no console errors; no layout shift / horizontal
  scroll; circular header photo renders cleanly.

## References
- **Card → dialog morph (the pattern we're following):**
  https://medienbaecker.com/articles/dialog-view-transitions
- **Native `<dialog>` API:**
  https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog
- **web.dev dialog tutorial / patterns:**
  https://web.dev/articles/building/a-dialog-component ·
  https://web.dev/patterns/components/dialog
- **View Transitions API tutorial:**
  https://www.smashingmagazine.com/2023/12/view-transitions-api-ui-animations-part1/
- **W3C APG modal dialog (a11y reference to sanity-check against):**
  https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/examples/dialog/
- **Styling inspiration:** https://uiverse.io/ · https://moderncss.dev/ ·
  https://tympanus.net/codrops/

## Phase 2 — content pipeline (LATER; do not block Phase 1)
Goal: collect real per-member content with minimal friction, keep it editable by lab
members, and fan it out to the site + announcements. Rough shape (to be planned in
its own brief):
1. **Google Sheet as source of truth.** Build a sheet (one row per member) with
   columns matching the dialog fields: name, title, image, education, project blurb,
   hobbies/interests, homepage, scholar, linkedin, github, orcid, email, position
   (alumni). Share it so lab members can edit their own row.
2. **Pull the sheet into the site.** A script (or Hugo build step) reads the sheet
   and generates the People content. NOTE: if we go this route, we will likely
   **revisit LOCKED decision #3** — a generated **Hugo data file**
   (`data/lab_members.yaml`) + a template loop is a cleaner target for a sheet pull
   than hand-edited shortcodes in `people.md`. The card→dialog UI from Phase 1 is
   independent of the data source, so this swap is low-risk later.
3. **Announce it.** Slack post to the lab channel + an email with the sheet link and
   a short "please fill your row (all optional)" ask.
4. **Mirror to Notion.** Surface the same info in the lab's Notion (e.g. a People
   database) for internal reference.
Tools available for this later: Google Sheets, Slack, and Notion MCPs.

## Open items for Dan (fill before/with handoff)
- Phase 2 timing/content: gather member info via the Google Sheet later; Phase 1
  ships with placeholders. (No blocker for the LXC102 agent.)
- Later: design a clearer "this card is clickable" cue (Phase 1 keeps it minimal:
  cursor + hover lift).
- Whether the dialog header should show a secondary line (e.g. education) or stay
  minimal.

## Handoff notes
- **Branch:** work on **`test`** (already created off `main` and pushed:
  `github.com/dbg-lab/dbg-lab.github.io`, branch `test`). Build Phase 1 there.
- Run the agent on **LXC102**, not the Mac. Implement → `hugo server` to verify →
  push. Repo uses a branch→PR flow; **direct HTTPS push has failed here — use SSH**
  (`git@github.com:dbg-lab/dbg-lab.github.io.git`).
- When done, append a "## Status" section here: branch/PR, what changed, what still
  needs Dan.
