"""Build the small, source-backed P4A participation site with no dependencies."""
from pathlib import Path
from datetime import date
import html
import json
import posixpath
import shutil
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
BASE = 'https://auraofintelligence.github.io/p4a-xyz-committees-inquiries/'
REPO = 'https://github.com/auraofintelligence/p4a-xyz-committees-inquiries'
P4A = 'https://p4a.xyz/'
NAMES = {'qld':'Queensland','nsw':'New South Wales','vic':'Victoria','wa':'Western Australia','sa':'South Australia','tas':'Tasmania','act':'ACT','nt':'Northern Territory','federal':'Commonwealth'}
STATUS = {'open':'Open','upcoming':'Upcoming','closed':'Closed','unverified':'Uncertain','ongoing':'Standing route'}
NAV = [('homelands/','Minjerribah & Redland'),('queensland/','Queensland'),('australia/','Australia'),('take-part/','How to take part')]
DATA = json.loads((ROOT/'data/registry.json').read_text(encoding='utf-8-sig'))
RECORDS = DATA['records']
CHECKED = DATA['checked']
PAGES = []

def e(value):
    return html.escape(str(value or ''), quote=True)

def rel(page, target):
    if target.startswith(('https://','http://','#')):
        return target
    return posixpath.relpath(target or 'index.html', posixpath.dirname(page) or '.') + ('/' if target.endswith('/') else '')

def link(page, target, label, cls='', cue=True):
    outside = target.startswith('https://') and not target.startswith(P4A)
    extra = ' target="_blank" rel="noopener noreferrer"' if outside else ''
    return f'<a href="{e(rel(page,target))}"' + (f' class="{e(cls)}"' if cls else '') + extra + '>' + e(label) + ('<span class="external-cue" aria-label="opens a new tab"> ↗</span>' if outside and cue else '') + '</a>'

def pretty_date(value):
    if not value: return ''
    return date.fromisoformat(value).strftime('%d %B %Y').lstrip('0')

def deadline(record, long=False):
    d = record['deadline']
    if d.get('label'): text = d['label']
    elif d.get('date'):
        text = pretty_date(d['date'])
        if d.get('time'):
            h,m = map(int, d['time'].split(':')[:2])
            text += ' · ' + str(h%12 or 12) + (f':{m:02d}' if m else '') + (' am' if h<12 else ' pm')
            text += ' · ' + (d.get('timezone') or 'timezone not stated')
        else: text += ' · time not published'
    elif record['status']=='ongoing': text = 'Recurring or continuing route'
    elif record['status']=='upcoming': text = 'Opening date / next stage: see details'
    else: text = 'No closing date verified'
    if long:
        note = d.get('note') or d.get('timezoneNote') or ''
        if note: text += '. ' + note
    return text

def badges(record):
    p = '<span class="priority-badge">P4A connection</span>' if record.get('connections') else ''
    return f'<div class="badge-row"><span class="status-badge status-{e(record["status"])}">{STATUS[record["status"]]}</span>{p}</div>'

def ordered(records):
    return sorted(records, key=lambda r:(-r.get('priority',0),r['deadline'].get('date') or '9999',r['title']))

def jurisdiction_route(r):
    if r['participationLevel'] in ('council','community'):return 'homelands/'
    if r['jurisdiction']=='qld':return 'queensland/'
    if r['jurisdiction']=='federal':return 'australia/'
    return 'states/'+r['jurisdiction']+'/'

def archive_route(route):
    return 'archive/'+route

def archive_link(page,route,label):
    return '<p class="scope-archive-link">'+link(page,archive_route(route),'Closed records: '+label+' archive','text-link')+'</p>'

def card(page, r):
    route = 'opportunities/' + r['id'] + '/'
    reason = ''
    if r.get('connections'):
        reason = '<p class="priority-reason"><b>Why highlighted:</b> '+e(r['connections'][0]['reason'])+'</p>'
    uncertainty = '<p class="uncertainty-note"><b>Uncertainty:</b> '+e(r.get('uncertaintyReason') or r['deadline'].get('note') or 'A current public invitation or its participation details have not been confirmed. See the source notes.')+'</p>' if r['status']=='unverified' else ''
    search = ' '.join([r['title'],r['purpose'],r['body'],r.get('place',''),r.get('kind','')]+[c['title'] for c in r.get('connections',[])])
    return f'''<article class="opportunity-card feature-panel" data-record data-status="{e(r['status'])}" data-priority="{r.get('priority',0)}" data-jurisdiction="{e(r['jurisdiction'])}" data-level="{e(r['participationLevel'])}" data-title="{e(r['title'])}" data-deadline="{e(r['deadline'].get('date',''))}" data-search="{e(search.lower())}">
{badges(r)}<div class="card-body"><h3>{link(page,route,r['title'])}</h3><p>{e(r['purpose'])}</p><div class="record-meta"><span>{e(NAMES.get(r['jurisdiction'],r['jurisdiction']))} · {e(r['kind'])}</span><span><strong>{'Next step' if r['status']=='ongoing' else 'Deadline / stage'}:</strong> {e(deadline(r))}</span></div>{uncertainty}{reason}</div><div class="card-actions">{link(page,route,'Details & participation','text-link')}<small>Checked {e(r['checked'])}</small></div></article>'''

def cards(page, records):
    return '<div class="participation-grid">'+''.join(card(page,r) for r in ordered(records))+'</div>'

def section(title, description, body, identifier=''):
    return f'<section class="participation-section"'+(f' id="{e(identifier)}"' if identifier else '')+f'><div class="section-heading"><div><h2>{e(title)}</h2><p>{e(description)}</p></div></div>{body}</section>'

def hero(title, description, eyebrow='P4A · committees & participation', side=''):
    return f'<section class="participation-hero"><div><p class="eyebrow">{e(eyebrow)}</p><h1>{e(title)}</h1><p class="lead">{e(description)}</p></div>'+(f'<aside class="hero-side">{side}</aside>' if side else '')+'</section>'

def chrome(page, title, body, description):
    doors=[('pages/maps.html','Maps'),('pages/architecture.html','System'),('pages/twinkle.html','Twinkle'),('pages/states.html','States'),('pages/starter-field-kit.html','Start local'),('pages/deployment-gear.html','Gear')]
    nav=''.join(link(page,P4A+p,t) for p,t in doors)
    section_nav='<nav class="participation-nav" aria-label="Committees and inquiries"><div class="participation-nav-title">'+link(page,'index.html','Committees & inquiries')+'</div><div class="participation-nav-links">'+link(page,'homelands/','Minjerribah & Redland')+link(page,'queensland/','Queensland')+link(page,'australia/','Australia')+'<details class="participation-place-menu"><summary>States & territories <span aria-hidden="true">⌄</span></summary><div>'+''.join(link(page,'queensland/' if j=='qld' else 'states/'+j+'/',NAMES[j]) for j in NAMES if j!='federal')+'</div></details>'+link(page,'take-part/','Taking part')+'</div></nav>'
    map_assets=f'<link rel="stylesheet" href="{e(rel(page,"assets/site-map.css"))}"><script src="{e(rel(page,"assets/site-map.js"))}" defer></script>' if page=='pages/site-map.html' else ''
    return f'''<!doctype html>
<html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#3f0f75"><title>{e(title)} | P4A</title><meta name="description" content="{e(description)}"><link rel="canonical" href="{e(BASE+('' if page=='index.html' else page.removesuffix('index.html')))}"><link rel="icon" href="{e(rel(page,'assets/favicon.svg'))}"><link rel="stylesheet" href="{e(rel(page,'styles.css'))}"><link rel="stylesheet" href="{e(rel(page,'assets/participation.css'))}">{map_assets}<script src="{e(rel(page,'assets/site-nav.js'))}" defer></script><script src="{e(rel(page,'assets/participation.js'))}" defer></script></head>
<body class="participation-site" data-theme="royal"><a class="skip-link" href="#main">Skip to content</a><header class="site-header"><a class="brand" href="{P4A}index.html" aria-label="P4A home"><span class="brand-mark">P4A</span><span class="brand-text"><strong>Purple Party</strong><span>for Australia</span></span></a><nav class="site-nav" data-nav aria-label="Primary">{nav}</nav><button class="index-toggle" type="button" data-menu-toggle aria-expanded="false" aria-controls="site-index"><span class="index-toggle-lines" aria-hidden="true"><i></i><i></i><i></i></span><span class="index-toggle-label">Index</span></button></header>
<main id="main">{section_nav}{body}</main>
<footer class="site-footer"><div><p>P4A is currently a proposed movement and drafting project. Content is exploratory unless explicitly marked as adopted policy.</p><p>p4a.xyz - Less splash, more class. A civic workbench, started on Minjerribah.</p><p class="participation-research-date">Participation sources checked {pretty_date(CHECKED)}. {link(page,'sources/','Coverage and source limits')}.</p></div><nav class="footer-links" aria-label="Footer links">{link(page,'pages/site-map.html','Site map')}{link(page,P4A+'pages/site-map.html','All P4A pages')}{link(page,'LICENCE.md','Strange But True licence')}{link(page,REPO,'Committees source',cue=False)}{link(page,'robots.txt','robots.txt')}</nav></footer><a class="back-top" href="#main" aria-label="Back to top">↑ Top</a></body></html>'''

def write(page, title, body, description=''):
    dest=OUT/page
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(chrome(page,title,body,description or title),encoding='utf-8')
    PAGES.append((page,title))

def coverage_table(page, rows=None):
    rows=rows or DATA['coverage']
    content=''
    for c in rows:
        count = c.get('observedOpenCount')
        label = c.get('label',NAMES.get(c['jurisdiction'],c['jurisdiction']))
        content+=f'<tr><th scope="row">{link(page,c["sourceUrl"],label)}</th><td>{e(c.get("status","partial"))}'+(f'<br>{count} open calls in reviewed index' if count is not None else '')+f'</td><td>{e(c["note"])}</td></tr>'
    return '<div class="coverage-table-wrap"><table class="coverage-table"><caption>Official list coverage · checked '+CHECKED+'</caption><thead><tr><th>Jurisdiction / source</th><th>Review status</th><th>What this covers</th></tr></thead><tbody>'+content+'</tbody></table></div>'

def filters(page, records, default='all'):
    jurisdictions=sorted({r['jurisdiction'] for r in records},key=lambda j:list(NAMES).index(j))
    status_options=[('all','All records'),('available','Open & upcoming'),('open','Open'),('upcoming','Upcoming'),('ongoing','Standing routes'),('unverified','Uncertain'),('closed','Closed')]
    def status_count(value):
        return len(records) if value=='all' else len([r for r in records if r['status'] in ('open','upcoming')]) if value=='available' else len([r for r in records if r['status']==value])
    opts=''.join(f'<option value="{v}"'+(' selected' if v==default else '')+'>'+t+' ('+str(status_count(v))+')</option>' for v,t in status_options)
    assert len(jurisdictions)<=1, 'A human view must have a single jurisdiction'
    selected=jurisdictions[0] if jurisdictions else ''
    return f'''<form class="filter-panel" data-filters hidden><input type="hidden" name="jurisdiction" value="{selected}" data-default="{selected}"><div class="filter-grid"><label>Search within this jurisdiction<input type="search" name="search" placeholder="Try housing, health, transport…" autocomplete="off" data-default=""></label><label>Status<select name="status" data-default="{default}">{opts}</select></label><label>Sort by<select name="order" data-default="priority"><option value="priority">P4A connections first</option><option value="deadline">Closing date</option><option value="title">Title A–Z</option></select></label></div><div class="filter-actions"><label><input type="checkbox" name="connected"> P4A topic matches only</label><button type="button" data-reset>Reset this view</button></div></form><p class="results-count" data-results-count aria-live="polite">{len(records)} records in this jurisdiction. Priority labels explain existing P4A connections.</p><noscript><p class="notice">All records for this jurisdiction are shown below with their status. Browser filters are available with JavaScript.</p></noscript><div class="participation-grid" data-records>{''.join(card(page,r) for r in ordered(records))}</div><p class="notice" data-empty hidden>No matching records in this jurisdiction’s dated list. Try another topic or status, and check its official source list for gaps.</p>'''

def build():
    OUT.mkdir(exist_ok=True)
    for path in ['styles.css','assets/participation.css','assets/participation.js','assets/site-nav.js','assets/site-map.css','assets/site-map.js','assets/external-links.js','assets/favicon.svg','assets/fonts/archivo-var.woff2','assets/fonts/jetbrains-mono-var.woff2','assets/fonts/archivo-OFL.txt','assets/fonts/jetbrains-mono-OFL.txt','LICENCE.md']:
        dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
    (OUT/'.nojekyll').write_text('',encoding='utf-8')
    (OUT/'data').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'data/registry.json',OUT/'data/registry.json')
    local=[r for r in RECORDS if 'homelands' in r.get('groups',[])]
    available=[r for r in RECORDS if r['status'] in ('open','upcoming')]
    parliament=[r for r in available if r.get('parliamentary') and r['status']=='open']
    page='index.html'
    body=hero('Have your say. Follow it through.','P4A’s founder and designer lives on North Stradbroke Island / Minjerribah. This starting path follows the layers of community and government that bind or influence his life: Redland City, Queensland and the Commonwealth. Use the navigation to explore participation across the rest of Australia.',side='<p class="eyebrow">Committees & inquiries</p><strong>All topics. Meaningful priorities.</strong><p>Open and upcoming opportunities are gathered across Australia. Genuine matches with existing P4A Twinkles and systems are highlighted, with the reason shown.</p>')
    body+='<p class="prose">To map the rules and public responsibilities that touch your own life, start with '+link(page,'https://auraofintelligence.github.io/australian-law-2012-lukes-relevance/pages/your-relevance.html','Your Relevance in Luke’s law workbench')+'.</p>'
    body+='<div class="button-row">'+link(page,'homelands/','Begin with Minjerribah & Redland','button')+'</div>'
    body+=f'<div class="status-strip"><span>Checked {pretty_date(CHECKED)}</span><span>'+link(page,'sources/','Coverage, gaps & verification')+'</span></div>'
    routes=[('homelands/','01 · Local','Minjerribah & Redland','Island community participation and Redland City Council consultations, petitions and meeting rules.'),('queensland/','02 · State','Queensland','Queensland Parliament and state-government opportunities. Search within this state level.'),('australia/','03 · Commonwealth','Australia','Federal Parliament and Commonwealth opportunities. Search within the national level.')]
    body+=section('Choose the body you want to influence','Each level has its own list and search. P4A topic matches are highlighted within the selected level. Use States & territories in the navigation for another jurisdiction.','<div class="route-grid">'+''.join('<a class="route-card feature-panel" href="'+e(rel(page,p))+'"><p class="eyebrow">'+e(t)+'</p><h3>'+e(title)+'</h3><p>'+e(d)+'</p></a>' for p,t,title,d in routes)+'</div>')
    write(page,'Committees, inquiries & participation',body,'Open and upcoming public participation, beginning with Minjerribah and Redland City, with meaningful P4A connections highlighted.')

    page='homelands/index.html'
    body=hero('Begin on Minjerribah.','Start with the decisions and community work that touch island life, alongside Redland City’s actual consultation, petition and meeting processes.','The homelands · Minjerribah & Redland City')
    body+='<div class="prose"><p>Minjerribah / North Stradbroke Island is on Quandamooka Country. Country, community governance, a council boundary and a parliamentary electorate have distinct roles. The island’s participation routes include community-led work as well as government decisions about land, water, services and access.</p><p>Follow '+link(page,'https://qyac.net.au/','Quandamooka Yoolooburrabee Aboriginal Corporation')+' for its own governance and community notices. A general council consultation does not convey Traditional Owners’ consent. Nation or member-specific processes keep their own eligibility.</p></div>'
    body+=section('Open invitations and upcoming community participation','Each card explains whether it is an inquiry, consultation, community expression of interest or event.',cards(page,[r for r in local if r['status'] in ('open','upcoming')]))
    body+=section('Use the council and community routes','Public addresses require approval. Petitions have their own rules. Watching a livestream is observation; no public remote-speaking entitlement has been verified.',cards(page,[r for r in local if r['status']=='ongoing']))
    uncertain_local=[r for r in local if r['status']=='unverified']
    if uncertain_local:body+=section('Uncertain invitations','These records remain visible with their source limitations.',cards(page,uncertain_local))
    body+=archive_link(page,'homelands/','Minjerribah & Redland')
    body+=section('The connected P4A place journeys','Return to existing context and keep the participation record alongside the place.','<nav class="button-row" aria-label="P4A places">'+link(page,P4A+'pages/minjerribah.html','Minjerribah','button button-secondary')+link(page,P4A+'states/qld/councils/redland/index.html','Redland City','button button-secondary')+link(page,P4A+'states/qld/index.html','Queensland','button button-secondary')+link(page,P4A+'states/qld/places/federal/index.html','Federal representation','button button-secondary')+'</nav>')
    write(page,'Minjerribah & Redland City',body)

    for j,route in [('qld','queensland'),('federal','australia')]:
        page=route+'/index.html';rs=[r for r in RECORDS if r['jurisdiction']==j and r['participationLevel'] in ('state','federal') and r['status']!='closed']
        description='Public submission calls, relevant state consultations and clearly labelled standing routes.' if j=='qld' else 'Senate, House and joint committee invitations, alongside relevant federal consultations.'
        body=hero('Queensland participation.' if j=='qld' else 'Have a say nationally.',description)
        body+='<div class="notice">Every record for this level is shown by default. Status and uncertainty tags explain what is known. '+link(page,'sources/','Review source coverage and gaps')+'.</div>'
        body+=filters(page,rs)
        body+=archive_link(page,route+'/', 'Australia / Commonwealth' if j=='federal' else NAMES[j])
        body+=section('Back to P4A’s place context','Existing council, state and federal journeys remain in P4A.','<div class="button-row">'+link(page,P4A+'states/qld/index.html','Queensland portal','button button-secondary')+link(page,P4A+'states/qld/places/federal/index.html','Queensland federal areas','button button-secondary')+link(page,P4A+'pages/places.html','All councils and electorates','button button-secondary')+'</div>')
        write(page,NAMES[j]+' participation',body)

    for j,name in NAMES.items():
        if j in ('qld','federal'): continue
        page='states/'+j+'/index.html'; rs=[r for r in RECORDS if r['jurisdiction']==j and r['participationLevel']=='state' and r['status']!='closed']
        body=hero(name+'.','Official invitations, upcoming participation and the status of our source review.')
        rows=[c for c in DATA['coverage'] if c['jurisdiction']==j]
        body+=coverage_table(page,rows)
        body+=filters(page,rs) if rs else '<p class="notice">No open or upcoming call has been verified in this review. This does not establish that no participation opportunity exists. Use the official list above.</p>'
        body+=archive_link(page,'states/'+j+'/',name)
        body+='<p>'+link(page,P4A+'states/'+j+'/index.html','P4A '+name+' portal','text-link')+' · '+link(page,P4A+'states/'+j+'/places/state/index.html','State / territory representation','text-link')+' · '+link(page,P4A+'states/'+j+'/places/federal/index.html','Federal representation','text-link')+'</p>'
        write(page,name+' participation',body)

    scopes=[('homelands/','Minjerribah & Redland')]+[('australia/' if j=='federal' else 'queensland/' if j=='qld' else 'states/'+j+'/', 'Australia / Commonwealth' if j=='federal' else name) for j,name in NAMES.items()]
    for route,label in scopes:
        page=archive_route(route)+'index.html'
        archived=[r for r in RECORDS if jurisdiction_route(r)==route and r['status']=='closed']
        body=hero(label+' archive.','Closed participation records for this jurisdiction, retaining their original sources and check dates.')
        body+='<p>'+link(page,route,'Return to current '+label+' opportunities','text-link')+'</p>'
        body+=filters(page,archived) if archived else '<p class="notice">There are no closed records in this jurisdiction’s archive yet.</p>'
        body+='<p class="prose">A closed submission round can be followed by hearings, a report or another consultation. Use each original record to follow verified developments. Moving a record here does not refresh its source date or assert an outcome.</p>'
        write(page,label+' archive',body)

    for r in RECORDS:
        page='opportunities/'+r['id']+'/index.html'
        body=hero(r['title'],r['purpose'],NAMES[r['jurisdiction']]+' · '+r['kind'])+badges(r)
        if r['status']=='unverified': body+='<p class="notice"><strong>Unverified invitation.</strong> This record is a lead to check. It is not presented as a confirmed open call.</p>'
        if r['status']=='closed': body+='<p class="notice"><strong>The recorded feedback round has closed.</strong> Follow the official source for outcomes or any new invitation.</p>'
        if r.get('statusNote'): body+='<p class="notice">'+e(r['statusNote'])+'</p>'
        facts=[('Responsible body',r['body']),('Place / scope',r.get('place',NAMES[r['jurisdiction']])),('How to take part',r['method']),('Deadline / next stage',deadline(r,True)),('Eligibility and restrictions',r['eligibility']),('What may become public',r['disclosure']),('What was checked',r['verification']),('Date checked',pretty_date(r['checked']))]
        body+='<div class="detail-layout"><div><dl class="fact-list">'+''.join('<dt>'+e(k)+'</dt><dd>'+e(v)+'</dd>' for k,v in facts)+'</dl>'
        for related in r.get('relatedLinks',[]):
            body+='<p class="prose">'+e(related['before'])+link(page,related['url'],related['label'])+e(related['after'])+'</p>'
        if r.get('islandRelevance'):body+='<div class="notice"><strong>Minjerribah connection:</strong> '+e(r['islandRelevance'])+'</div>'
        if r.get('connections'):
            body+=section('Why this is highlighted','The link is a topic match to existing P4A work. It does not imply agreement with an inquiry’s conclusions or official endorsement.','<ul class="connection-list">'+''.join('<li>'+link(page,c['url'],c['title'])+'<p>'+e(c['reason'])+'</p></li>' for c in r['connections'])+'</ul>')
        body+=section('Official sources','The responsible institution’s current page governs participation.','<ul class="source-list">'+''.join('<li>'+link(page,s['url'],s.get('title','Official source'))+'<small>'+e(s.get('supports',s.get('note','')))+' · '+e(s.get('access','reviewed official source'))+'</small></li>' for s in r['sources'])+'</ul>')+'</div>'
        return_route=archive_route(jurisdiction_route(r)) if r['status']=='closed' else jurisdiction_route(r)
        body+='<aside class="feature-panel"><p class="eyebrow">Your next step</p><h3>Read the official invitation.</h3><p>Check its terms, deadline and publication conditions before sending anything.</p>'+link(page,r['sourceUrl'],'Open official source','button')+'<p>'+link(page,'take-part/','Prepare a useful contribution','text-link')+'</p><p>'+link(page,return_route,'Return to this jurisdiction’s archive' if r['status']=='closed' else 'Return to this jurisdiction','text-link')+'</p></aside></div>'
        write(page,r['title'],body)

    page='take-part/index.html'
    body=hero('Make your contribution useful.','Choose a real invitation, understand its scope and decide what you are comfortable putting on the public record.')
    body+='''<div class="prose"><h2>Start with the question being asked</h2><p>Read the terms of reference or consultation questions. Identify which body can act, what evidence you can offer and the change you want considered. A short, specific account can be useful; follow any format or word limit in the invitation.</p><h2>Check the route and deadline</h2><p>A written parliamentary submission, council survey, petition, public address and community event are different routes. A hearing date does not guarantee a chance to speak. An inquiry’s reporting date is not the submission deadline. Date-only deadlines have no invented midnight cutoff here; ask the responsible body when a precise cutoff matters.</p><h2>Choose what can become public</h2><p>Parliamentary submissions and submitter names may be published after a committee authorises release. A request for confidentiality or a withheld name is a request for the committee to decide; it is not automatic. Keep sensitive personal details separate as the official guidance directs. Meeting contributions can be livestreamed, recorded and minuted. A survey may have different privacy terms from a public comment board.</p><p>Read each record’s publication note and the official collection notice. Do not assume contact details, a person’s story or an online account will be anonymous. Obtain permission before including someone else’s personal information.</p><h2>Keep a copy and follow what changes</h2><p>Keep the invitation, date sent, receipt and a copy of your contribution. Follow the response, hearing record, report or decision. Separate a proposal from an observed result. The P4A practice keeps three accounts together: what it cost, what was given freely and what changed.</p><h2>How P4A priority works</h2><p>A priority label requires a direct subject match with an existing P4A Twinkle or system. The card explains the connection and the detail page links to the unchanged original work. Records without a match remain in their jurisdiction’s list. Sort by closing date or title to browse independently of P4A connections.</p></div>'''
    body+=section('Existing P4A tools and context','These are places to explore or prepare your own work. They do not lodge a submission.','<div class="button-row">'+link(page,P4A+'pages/private-civic-profile-builder.html','Private civic draft','button button-secondary')+link(page,P4A+'pages/civic-ledger.html','Civic ledger','button button-secondary')+link(page,P4A+'pages/legal-rag.html','Legal memory','button button-secondary')+'</div>')
    body+='<div class="prose"><p>Use '+link(page,'https://auraofintelligence.github.io/australian-law-2012-lukes-relevance/pages/your-relevance.html','Your Relevance')+' to map the laws and institutions that touch your circumstances. When you need the exact provision and source trail, continue with the '+link(page,'https://github.com/auraofintelligence/australian-legal-engine','Australian Legal Engine')+'.</p><p>For recurring charges or contract evidence, '+link(page,'https://auraofintelligence.github.io/household-bill-check/','Household Bill Check')+' helps organise the clause, bill, dates and questions. Its '+link(page,'https://auraofintelligence.github.io/household-bill-check/mutuals.html#public-record','community evidence and reform brief')+' connects consented patterns with a possible public submission.</p></div>'
    write(page,'How to take part',body)

    page='sources/index.html'
    body=hero('Know what has been checked.','A complete catalogue is the aim. This page records the actual official lists reviewed, invitations represented and gaps still needing work.')
    body+='<p class="notice">Research checked '+pretty_date(CHECKED)+'. Rebuilding the website does not refresh its sources. Official sources may change after this review; use their current invitations before acting.</p>'
    body+=coverage_table(page)
    body+='<div class="prose"><h2>What the labels mean</h2><ul><li><strong>Open:</strong> a directly checked official invitation is accepting participation at the research date.</li><li><strong>Upcoming:</strong> an official source announces a future opening or a participation event, with restrictions shown.</li><li><strong>Standing route:</strong> a continuing mechanism with its own eligibility and application rules.</li><li><strong>Closed:</strong> the specific contribution round ended; a later project stage may continue.</li><li><strong>Unverified:</strong> a lead, inaccessible detail or ambiguous invitation that needs follow-up.</li></ul><h2>Coverage and evidence</h2><p>Every entry from an enumerated open-call index is represented, even where there is no P4A match. Current-inquiry lists can include closed submission windows, ongoing institutional scrutiny and hearings with invited witnesses. Those are reviewed separately. The directory does not assert coverage of every council, community organisation, government consultation or unpublished future inquiry.</p><p>Short summaries are original paraphrases. Each detail page retains its official links, field-level limits, eligibility, publication conditions and check date. Source-page copies, contact lists and browser material are not published.</p></div>'
    body+='<p>'+link(page,'data/registry.json','Download the dated public records','text-link')+' · '+link(page,REPO+'/blob/main/content/research-notes.md','Research and maintenance notes','text-link')+'</p>'
    write(page,'Sources & coverage',body)
    page='pages/site-map.html'
    intro='<section class="human-map-intro"><p class="eyebrow">P4A · Find your way</p><h1>Where would you like to go?</h1><p class="human-lead">Choose a public body, then search its participation opportunities. The directory below keeps each jurisdiction separate.</p><p class="human-map-date">Navigation reviewed '+pretty_date(CHECKED)+'. Source facts keep their own check dates.</p><div class="human-start-grid"><article><h2>Choose a jurisdiction</h2><p>Start with the public body whose decisions you want to influence.</p>'+link(page,'index.html','Choose your starting place')+'</article><article><h2>Follow the local path</h2><p>Minjerribah community and Redland City Council participation.</p>'+link(page,'homelands/','Open the local path')+'</article><article><h2>Keep exploring P4A</h2><p>The main site map connects the wider workbench.</p>'+link(page,P4A+'pages/site-map.html','Every P4A room')+'</article></div><div class="human-filter" hidden data-site-filter><label for="site-map-search">Find a page or topic</label><div><input id="site-map-search" type="search" placeholder="Try Redland, housing, health…" autocomplete="off"><button type="button" data-site-clear>Clear</button></div><p role="status" aria-live="polite" data-site-search-status></p></div></section>'
    groups=[('start','Start here',[('index.html','Committees and inquiries'),('take-part/index.html','How to take part'),('sources/index.html','Sources and coverage')])]
    for key,label,route in [('local','Minjerribah & Redland City','homelands/')]+[(j,'Australia · Commonwealth' if j=='federal' else name,'australia/' if j=='federal' else 'queensland/' if j=='qld' else 'states/'+j+'/') for j,name in NAMES.items()]:
        rs=[r for r in RECORDS if (r['participationLevel'] in ('council','community') if key=='local' else r['jurisdiction']==key and r['participationLevel'] in ('state','federal'))]
        groups.append((key,label,[(route+'index.html',label+' participation'),(archive_route(route)+'index.html',label+' archive')]+[('opportunities/'+r['id']+'/index.html',r['title']) for r in ordered(rs)]))
    for key,label,items in groups:
        intro+='<details class="human-directory" id="map-'+key+'" data-site-group'+(' open' if key=='start' else '')+'><summary><strong>'+label+'</strong><span>'+str(len(items))+' pages</span></summary><ul>'+''.join('<li data-site-page data-search="'+e((t+' '+p+' '+label).lower())+'">'+link(page,p,t)+'</li>' for p,t in items)+'</ul></details>'
    write(page,'Find your way', '<div class="human-site-map">'+intro+'</div>')
    write('404.html','Page not found',hero('Find your way back.','This participation page could not be found.')+'<div class="button-row">'+link('404.html','index.html','Home','button')+link('404.html','index.html','Choose a jurisdiction','button button-secondary')+'</div>')
    urls=[BASE+('' if p=='index.html' else p.removesuffix('index.html')) for p,t in PAGES if p!='404.html']
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(u)+'</loc></url>' for u in urls)+'</urlset>\n',encoding='utf-8')
    shutil.copyfile(ROOT/'content/robots-policy.txt',OUT/'robots.txt')
    (OUT/'llms.txt').write_text('# P4A committees and participation\n\nDated official-source directory checked '+CHECKED+'. Coverage gaps: '+BASE+'sources/. Topic priority is P4A editorial context, not official endorsement. This voluntary guide grants no additional reuse or AI-training permission. Third-party material retains its own rights.\n\n'+''.join('- ['+t+']('+BASE+('' if p=='index.html' else p.removesuffix('index.html'))+')\n' for p,t in PAGES if p!='404.html'),encoding='utf-8')
    expected_pages={p for p,t in PAGES}
    for stale in OUT.rglob('*.html'):
        if stale.relative_to(OUT).as_posix() not in expected_pages:
            assert stale.resolve().is_relative_to(OUT.resolve())
            stale.unlink()
    size=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    print(json.dumps({'pages':len(PAGES),'records':len(RECORDS),'artifactBytes':size,'checked':CHECKED}))

if __name__=='__main__':
    build()
