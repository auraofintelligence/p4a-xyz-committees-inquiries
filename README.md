# P4A committees and inquiries

[Open this P4A section](https://auraofintelligence.github.io/p4a-xyz-committees-inquiries/) · [Main P4A workbench](https://p4a.xyz/)

This is a continuation of P4A the Purple Party for Australia, held in a separate repository because the main Pages site is near its size limit. It uses the existing P4A theme, branding, six primary navigation doors, searchable five-theme Index, footer and site-map pattern. Existing Twinkles are linked where a real topic match exists and are not edited.

P4A’s founder and designer lives on North Stradbroke Island / Minjerribah. The starting path follows the community and government relationships affecting his life: Redland City, Queensland and the Commonwealth. Other states and territories are reached through navigation.

Visitors choose a responsible body before searching. Australia shows federal participation only; each state shows state-level participation. Each parliament has separate Inquiries & participation and All committees views. Council participation has its own state/territory chooser and individual council pages, while Minjerribah and Redland retain their dedicated starting path. There is no combined opportunity view. Every current record is visible by default, including uncertain invitations with an explicit tag and explanation. Closed contribution rounds retain their detail URLs and move to that parliament or council's own archive.

The section menu is specifically for committees and inquiries: two Browse choices and a parliament/council selector. Changing the view retains the selected body; changing the body retains the view. The Council participation shortcut opens the participation layer directly: choose a state or territory, then one council. General council and electorate directories remain separate. Homelands is a shortcut to the committees and inquiries for Redland City, Queensland and Australia, with six direct links and no combined record list. Redland's local committee evidence is in `data/redland-committees.json`; its general meeting participation and local invitations have their own view. The legacy local archive URL remains a link to the scoped Redland archive.

## Source coverage

Latest research: 7 November 2026, Australia/Brisbane. Individual records retain their own source dates. The directory contains 214 parliamentary committee entries: NSW 61, Queensland 10, NT 9, Tasmania 23, WA 16, SA 19, ACT 9 and federal 67. Victoria has no current committees following Parliament's expiry on 3 November; its official archive remains linked. Counts describe directory entries: ACT's nine pages include eight committees plus Legal Affairs' scrutiny role; NT's directory also retains a statutory-role entry. Eight Senate links group separate legislation and references committees.

NSW's Current inquiry filter returns 66 entries. Direct pages show open calls, closed submission rounds and final-report conflicts, so that number is not an accepting-submissions count. Its two confirmed written calls are separate from its complete committee directory. Federal Women’s Health still has conflicting official dates. The [sources and coverage page](https://auraofintelligence.github.io/p4a-xyz-committees-inquiries/sources/) records the remaining access and participation gaps. This is a dated directory, not a live feed.

The council chooser imports 536 council identities and 16 separately labelled local bodies or unincorporated areas from existing P4A data. The remaining 550 local areas were individually searched, preserving Redland and the ACT explanation. The audit contains 948 pathway links: 737 official pages read, 12 official links with limited destination access and 199 uncertain indexed leads. Every ordinary council has a located route or prior procedure review except Yarrabah, whose source-access gap and official contact-directory fallback are explicit. Detailed procedures are separately reviewed for 21 councils outside Redland. Seventeen new dated council invitations were added during this council-only pass. National project coverage and unreviewed conditions remain incomplete.

Council body audits separately record 2,077 named entries across 322 of the 550 audited local areas, plus 90 continuing-method records. Indexed-only entries (796) and historical-source entries (14) stay visibly uncertain; 228 areas still lack a verified named inventory. Those are coverage gaps, not zero-committee findings. Council chooser badges separate open/upcoming invitations, standing routes and uncertain records. Brisbane now includes all four projects from its current portal section and a separately announced future consultation. The source registry and audit JSON stay canonical in GitHub, linked from the coverage page instead of duplicated in the small Pages artifact. Reviewed source aliases and false-invitation exclusions are retained for future imports. No automation is configured.

Canonical participation records are in `data/registry.json`. Each carries its responsible body, purpose, method, deadline precision, eligibility, publication conditions, official sources, check date, jurisdiction and participation level. Committee entries and source inquiry links are in `data/committees.json`; council identities and procedure reviews are in `data/councils.json`. Priority requires a stated match to existing P4A work. Search supports multiple words; visible status buttons and optional topic, participation-route and responsible-body filters remain inside the chosen view. Sort by P4A matches, closing date, check date or title. Active filters are stated explicitly.

## Maintain and preview

Read [AGENTS.md](AGENTS.md) and [research notes](content/research-notes.md).

```text
python tools/build.py
python tools/validate.py
python -m http.server 8772 --bind 127.0.0.1 --directory _site
```

Open `http://127.0.0.1:8772/` in Chrome. The generated `_site/` directory is ignored by Git. The Pages workflow builds and validates it, then uploads only the checked public artifact. No screenshots, browser profiles, dependencies or raw source-page downloads are published.

After an official check confirms that a round closed, change that record’s status to `closed`, retain its dates and source links, add any verified outcome separately, and rebuild. The generator moves it to its own jurisdiction’s archive while preserving its detail page. A reporting date or an old cached call is not a submission deadline. Research dates do not advance on rebuild.

There must be exactly zero em dashes in source and generated files. Validation rejects literal and encoded forms. The P4A stylesheet has one comment punctuation change and keeps the same visual rules.

## Rights and discovery

The [Strange But True Public Source Licence](LICENCE.md) is retained unchanged. P4A and this section are public source, not open source. Third-party source material and fonts keep their own rights. [Attribution](content/attribution.md) records the reused theme and font licences.

The human site map, `sitemap.xml`, `robots.txt` and `llms.txt` are generated together. The project crawler file follows P4A’s search and GPTBot choices. On the shared GitHub Pages hostname, only the host-root `robots.txt` controls crawling. Its matching project-path entries and sitemap must be published there as well. These cooperative directions do not enforce copyright or grant reuse or AI-training rights.
