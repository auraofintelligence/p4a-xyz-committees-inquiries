# P4A committees and inquiries

[Open this P4A section](https://auraofintelligence.github.io/p4a-xyz-committees-inquiries/) · [Main P4A workbench](https://p4a.xyz/)

This is a continuation of P4A the Purple Party for Australia, held in a separate repository because the main Pages site is near its size limit. It uses the existing P4A theme, branding, six primary navigation doors, searchable five-theme Index, footer and site-map pattern. Existing Twinkles are linked where a real topic match exists and are not edited.

P4A’s founder and designer lives on North Stradbroke Island / Minjerribah. The starting path follows the community and government relationships affecting his life: Redland City, Queensland and the Commonwealth. Other states and territories are reached through navigation.

Visitors choose a jurisdiction before searching. Australia shows federal opportunities only; each state shows state-level opportunities; local council and community routes remain in the Minjerribah and Redland path. There is no combined opportunity view. Every current record is visible by default, including uncertain invitations with an explicit tag and explanation. Closed records retain their detail URLs and move to that jurisdiction’s own archive.

## Source coverage

Research checked 6 November 2026, Australia/Brisbane. The initial record set includes 67 invitations, standing routes, hearing programmes and closed records. The live [sources and coverage page](https://auraofintelligence.github.io/p4a-xyz-committees-inquiries/sources/) explains what was enumerated and what remains incomplete. The federal Women’s Health inquiry has conflicting official dates and is explicitly uncertain. South Australian committee attachments and wider community participation still have coverage gaps. This is a dated directory, not a live feed.

Canonical records are in `data/registry.json`. Each carries its responsible body, purpose, method, deadline precision, eligibility, publication conditions, official sources, check date, jurisdiction and participation level. Priority requires a stated match to existing P4A work. Unrelated topics remain in their own jurisdiction’s list.

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
