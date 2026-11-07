"""Build the small, source-backed P4A participation site with no dependencies."""
from pathlib import Path
from datetime import date
import html
import json
import posixpath
import shutil
from urllib.parse import quote, urlsplit, parse_qs, parse_qsl, urlencode, unquote
import re
import hashlib
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
BASE = 'https://auraofintelligence.github.io/p4a-xyz-committees-inquiries/'
REPO = 'https://github.com/auraofintelligence/p4a-xyz-committees-inquiries'
P4A = 'https://p4a.xyz/'
NAMES = {'qld':'Queensland','nsw':'New South Wales','vic':'Victoria','wa':'Western Australia','sa':'South Australia','tas':'Tasmania','act':'ACT','nt':'Northern Territory','federal':'Commonwealth'}
STATUS = {'open':'Open','upcoming':'Upcoming','closed':'Closed','unverified':'Uncertain','ongoing':'Standing route'}
DATA = json.loads((ROOT/'data/registry.json').read_text(encoding='utf-8-sig'))
RECORDS = DATA['records']
CHECKED = DATA['checked']
COUNCIL_DATA = json.loads((ROOT/'data/councils.json').read_text(encoding='utf-8'))
COUNCILS = COUNCIL_DATA['councils']
COUNCIL_BY_ID = {c['id']:c for c in COUNCILS}
COMMITTEE_DATA = json.loads((ROOT/'data/committees.json').read_text(encoding='utf-8')) if (ROOT/'data/committees.json').exists() else {'committees':[], 'directories':[]}
COMMITTEES = COMMITTEE_DATA['committees']
REDLAND_COMMITTEES=json.loads((ROOT/'data/redland-committees.json').read_text(encoding='utf-8'))
COUNCIL_PATHWAY_DATA=json.loads((ROOT/'data/council-pathways.json').read_text(encoding='utf-8')) if (ROOT/'data/council-pathways.json').exists() else {'audits':[]}
COUNCIL_PATHWAYS={a['councilId']:a for a in COUNCIL_PATHWAY_DATA['audits']}
TOPICS = {'housing':'Housing & planning','health':'Health & care','environment':'Environment & animals','economy':'Work, costs & economy','rights':'Rights & justice','democracy':'Elections & democracy','technology':'Technology & data','infrastructure':'Transport & infrastructure','community':'Community & culture','governance':'Government & accountability'}
PAGES = []
ASSET_VERSIONS={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()[:12] for p in ('assets/participation.css','assets/participation.js','assets/site-nav.js')}

def e(value):
    return html.escape(str(value or ''), quote=True)

def asset(page,path):
    return e(rel(page,path)+'?v='+ASSET_VERSIONS[path])

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
    if r.get('councilId'):return council_route(COUNCIL_BY_ID[r['councilId']])
    if r['participationLevel'] in ('council','community'):return 'councils/qld/redland/'
    if r['jurisdiction']=='qld':return 'queensland/'
    if r['jurisdiction']=='federal':return 'australia/'
    return 'states/'+r['jurisdiction']+'/'

def council_route(council):
    return 'councils/'+council['jurisdiction']+'/'+council['slug']+'/'

def council_records(ident):
    return [r for r in RECORDS if r.get('councilId')==ident or (ident=='qld-council-6250' and 'homelands' in r.get('groups',[]))]

def committee_route(committee):
    return 'committees/'+committee['jurisdiction']+'/'+committee['id']+'/'

def source_key(url):
    parsed=urlsplit(url);query=parse_qs(parsed.query)
    if 'committeeInquiryId' in query:return 'nsw-inquiry-'+query['committeeInquiryId'][0]
    if parsed.netloc.lower().endswith('parliament.wa.gov.au'):
        guid=re.search(r'/([A-Fa-f0-9]{32})(?:/|$)',parsed.path)
        if guid:return 'wa-document-'+guid[1].lower()
    meaningful=sorted((key.lower(),value) for key,value in parse_qsl(parsed.query,keep_blank_values=True) if key.lower()!='ref')
    return parsed.netloc.lower()+unquote(parsed.path).rstrip('/').lower()+('?' + urlencode(meaningful) if meaningful else '')

def committee_records(committee):
    sources={source_key(i['sourceUrl']) for i in committee.get('inquiries',[])}
    parent=urlsplit(committee['sourceUrl']);parent_query=parse_qs(parent.query)
    result=[]
    for r in RECORDS:
        if r['jurisdiction']!=committee['jurisdiction'] or r['participationLevel'] not in ('state','federal'):continue
        if r.get('committeeId') and r['committeeId']!=committee['id']:continue
        child=urlsplit(r['sourceUrl']);child_query=parse_qs(child.query)
        same_qld='cid' in parent_query and parent_query.get('cid')==child_query.get('cid')
        same_path=parent.path.rstrip('/') and child.path.lower().startswith(parent.path.rstrip('/').lower()+'/') and parent.netloc==child.netloc
        if r.get('committeeId')==committee['id'] or source_key(r['sourceUrl']) in sources or same_qld or same_path:result.append(r)
    return result

def browse_route(view,j=None):
    if not j:return view+'/'
    if view=='committees':return 'committees/'+j+'/'
    return 'councils/qld/redland/' if j=='redland' else 'australia/' if j=='federal' else 'queensland/' if j=='qld' else 'states/'+j+'/'

def navigation_context(page):
    if page=='archive/homelands/index.html':return 'inquiries','redland'
    path=page.removeprefix('archive/')
    view='committees' if path.startswith('committees/') else 'inquiries'
    if path.startswith('opportunities/'):
        record=next(r for r in RECORDS if r['id']==path.split('/')[1])
        if record['participationLevel'] in ('state','federal'):return view,record['jurisdiction']
        return view,'redland' if 'homelands' in record.get('groups',[]) else None
    if path.startswith('councils/qld/redland/'):return view,'redland'
    if path.startswith('australia/'):return view,'federal'
    if path.startswith('queensland/'):return view,'qld'
    parts=path.split('/')
    if len(parts)>2 and parts[0] in ('committees','states') and parts[1] in (*NAMES,'redland'):return view,parts[1]
    return view,None

def section_navigation(page):
    view,j=navigation_context(page)
    def choice(target,label,current=False,cls=''):
        return '<a href="'+e(rel(page,target))+'"'+(' class="'+cls+'"' if cls else '')+(' aria-current="location"' if current else '')+'>'+e(label)+'</a>'
    active=page.startswith(('inquiries/','committees/','states/','queensland/','australia/','opportunities/','archive/','councils/qld/redland/'))
    task_links=''.join(choice(browse_route(key,j),label,active and key==view,'committee-browse-link') for key,label in [('inquiries','Inquiries & participation'),('committees','All committees')])
    names={'redland':'Redland City Council','federal':'Australian Parliament',**{k:v+' '+('Assembly' if k in ('act','nt') else 'Parliament') for k,v in NAMES.items() if k!='federal'}}
    choices=''.join(choice(browse_route(view,key),names[key],j==key) for key in ['redland','federal','qld','nsw','vic','wa','sa','tas','act','nt'])
    selected=names[j] if j else 'Choose a parliament or Redland'
    return '<nav class="participation-nav" aria-label="Committees and inquiries" data-browse="'+view+'" data-parliament="'+(j or '')+'"><div class="participation-nav-heading"><div class="participation-nav-title">'+link(page,'index.html','Committees & inquiries')+'</div><div class="participation-nav-help">'+choice('homelands/','Homelands',page=='homelands/index.html')+choice('councils/','Council participation',page.startswith('councils/'))+choice('take-part/','Participation help',page=='take-part/index.html')+'</div></div><div class="committee-navigation-controls"><div class="committee-browse"><span class="committee-nav-label">Browse</span><div>'+task_links+'</div></div><details class="participation-parliament-menu"><summary><span class="committee-nav-label">Parliament / council</span><span class="committee-current-scope">'+e(selected)+' <span aria-hidden="true">⌄</span></span></summary><div>'+choices+'</div></details></div></nav>'

def topic_keys(r):
    if r.get('topics'):return r['topics']
    text=(r['title']+' '+r['purpose']).lower()
    words={'housing':['hous','rent','planning','city plan','tenanc'], 'health':['health','medical','care','blood','ndis','suicide'], 'environment':['environment','wildlife','animal','climate','net zero','water','coast','marine','paraquat','dog','waste','macropod'], 'economy':['econom','work','affordab','cost','tax','energy','finance','asic','budget','foster'], 'rights':['rights','justice','crime','strangulation','firearm','law','slavery','violence','consorting'], 'democracy':['elect','vot','democra','political party'], 'technology':['technolog','digital','cyber','artificial intelligence','data','intelligence'], 'infrastructure':['road','transport','ferry','postal','mobile','infrastructure','facilit','defence estate'], 'community':['community','culture','arts','sport','reconciliation','music','resilien'], 'governance':['oversight','accountab','annual report','administration','commission','scrutiny','public assets']}
    return [key for key,values in words.items() if any(re.search(r'\b'+re.escape(v),text) for v in values)] or ['governance']

def participation_method(r):
    kind=r.get('kind','').lower();method=r['method'].lower()
    if r['status']=='closed':return 'closed','Closed participation round'
    if r['status']=='unverified':return 'check','Check the current participation route'
    if 'survey' in kind:return 'survey','Answer a survey'
    if 'hearing' in kind and 'registration' in kind:return 'speaking','Register interest in speaking'
    if 'hearing' in kind or 'scrutiny' in kind or 'hearing' in r['title'].lower():return 'hearing','Observe or attend a hearing'
    if 'observation' in kind:return 'hearing','Observe a public committee meeting'
    if 'petition' in kind:return 'petition','Petition'
    if 'meeting' in kind or 'public address' in kind:return 'speaking','Apply to speak or ask a question'
    if 'consultation' in kind:return 'consultation','Contribute to a consultation'
    if any(word in kind for word in ('expression of interest','eoi','recruitment','volunteer')):return 'application','Apply or register interest'
    if any(word in kind for word in ('event','course','training')):return 'event','Register for an event or course'
    if r['status']=='ongoing':return 'standing','Use a standing participation route'
    if 'survey' in method and not r.get('parliamentary'):return 'survey','Answer a survey'
    return ('submission','Prepare a written submission') if r.get('parliamentary') else ('feedback','Follow the official participation steps')

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
    search = ' '.join([r['title'],r['purpose'],r['body'],r['method'],r.get('place',''),r.get('kind','')]+[c['title']+' '+c['reason'] for c in r.get('connections',[])])
    topics=topic_keys(r);method_key,method_label=participation_method(r)
    search+=' '+' '.join(TOPICS[t] for t in topics)
    future_events=sorted((event for event in r.get('events',[]) if event.get('date') and event['date']>=CHECKED),key=lambda event:event['date'])
    upcoming='<p class="upcoming-event"><strong>Next scheduled hearing:</strong> '+e(pretty_date(future_events[0]['date']))+'. Check the programme for attendance and witness arrangements.</p>' if future_events else ''
    return f'''<article class="opportunity-card feature-panel" data-record data-id="{e(r['id'])}" data-committee="{e(r.get('committeeId',''))}" data-status="{e(r['status'])}" data-priority="{r.get('priority',0)}" data-jurisdiction="{e(r['jurisdiction'])}" data-level="{e(r['participationLevel'])}" data-council="{e(r.get('councilId',''))}" data-title="{e(r['title'])}" data-deadline="{e(r['deadline'].get('date',''))}" data-checked="{e(r['checked'])}" data-topics="{e(' '.join(topics))}" data-method="{e(method_key)}" data-body="{e(r['body'])}" data-search="{e(search.lower())}">
{badges(r)}<div class="card-body"><h3>{link(page,route,r['title'])}</h3><p class="participation-action"><strong>{e(method_label)}</strong><br>{e(deadline(r))}</p>{upcoming}<p>{e(r['purpose'])}</p><div class="topic-tags">{''.join('<span>'+e(TOPICS[t])+'</span>' for t in topics[:2])}</div><div class="record-meta"><span>{e(r['body'])}</span></div>{uncertainty}{reason}</div><div class="card-actions">{link(page,route,'Details & participation','text-link')}<small>Checked {e(r['checked'])}</small></div></article>'''

def cards(page, records):
    return '<div class="participation-grid">'+''.join(card(page,r) for r in ordered(records))+'</div>'

def section(title, description, body, identifier=''):
    return f'<section class="participation-section"'+(f' id="{e(identifier)}"' if identifier else '')+f'><div class="section-heading"><div><h2>{e(title)}</h2><p>{e(description)}</p></div></div>{body}</section>'

def hero(title, description, eyebrow='P4A · committees & participation', side='', cls=''):
    classes='participation-hero'+(' '+cls if cls else '')
    return f'<section class="{e(classes)}"><div><p class="eyebrow">{e(eyebrow)}</p><h1>{e(title)}</h1><p class="lead">{e(description)}</p></div>'+(f'<aside class="hero-side">{side}</aside>' if side else '')+'</section>'

def chrome(page, title, body, description):
    doors=[('pages/maps.html','Maps'),('pages/architecture.html','System'),('pages/twinkle.html','Twinkle'),('pages/states.html','States'),('pages/starter-field-kit.html','Start local'),('pages/deployment-gear.html','Gear')]
    nav=''.join(link(page,P4A+p,t) for p,t in doors)
    section_nav=section_navigation(page)
    map_assets=f'<link rel="stylesheet" href="{e(rel(page,"assets/site-map.css"))}"><script src="{e(rel(page,"assets/site-map.js"))}" defer></script>' if page=='pages/site-map.html' else ''
    return f'''<!doctype html>
<html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#3f0f75"><title>{e(title)} | P4A</title><meta name="description" content="{e(description)}"><link rel="canonical" href="{e(BASE+('' if page=='index.html' else page.removesuffix('index.html')))}"><link rel="icon" href="{e(rel(page,'assets/favicon.svg'))}"><link rel="stylesheet" href="{e(rel(page,'styles.css'))}"><link rel="stylesheet" href="{asset(page,'assets/participation.css')}">{map_assets}<script src="{asset(page,'assets/site-nav.js')}" defer></script><script src="{asset(page,'assets/participation.js')}" defer></script></head>
<body class="participation-site" data-theme="royal"><a class="skip-link" href="#main">Skip to content</a><header class="site-header"><a class="brand" href="{P4A}index.html" aria-label="P4A home"><span class="brand-mark">P4A</span><span class="brand-text"><strong>Purple Party</strong><span>for Australia</span></span></a><nav class="site-nav" data-nav aria-label="Primary">{nav}</nav><button class="index-toggle" type="button" data-menu-toggle aria-expanded="false" aria-controls="site-index"><span class="index-toggle-lines" aria-hidden="true"><i></i><i></i><i></i></span><span class="index-toggle-label">Index</span></button></header>
<main id="main">{section_nav}{body}</main>
<footer class="site-footer"><div><p>P4A is currently a proposed movement and drafting project. Content is exploratory unless explicitly marked as adopted policy.</p><p>p4a.xyz - Less splash, more class. A civic workbench, started on Minjerribah.</p><p class="participation-research-date">Latest source checks {pretty_date(CHECKED)}. Individual records retain their own dates. {link(page,'sources/','Coverage and source limits')}.</p></div><nav class="footer-links" aria-label="Footer links">{link(page,'pages/site-map.html','Site map')}{link(page,P4A+'pages/site-map.html','All P4A pages')}{link(page,'LICENCE.md','Strange But True licence')}{link(page,REPO,'Committees source',cue=False)}{link(page,'robots.txt','robots.txt')}</nav></footer><a class="back-top" href="#main" aria-label="Back to top">↑ Top</a></body></html>'''

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
        content+=f'<tr><th scope="row">{link(page,c["sourceUrl"],label)}<br><small>Checked {e(c.get("checked","2026-11-06"))}</small></th><td>{e(c.get("status","partial"))}'+(f'<br>{count} open calls in reviewed index' if count is not None else '')+f'</td><td>{e(c["note"])}</td></tr>'
    return '<div class="coverage-table-wrap"><table class="coverage-table"><caption>Official source coverage and individual review dates</caption><thead><tr><th>Jurisdiction / source</th><th>Review status</th><th>What this covers</th></tr></thead><tbody>'+content+'</tbody></table></div>'

def filters(page, records, default='all', scope_label='this jurisdiction'):
    jurisdictions=sorted({r['jurisdiction'] for r in records},key=lambda j:list(NAMES).index(j))
    status_options=[('all','All records'),('available','Open & upcoming'),('open','Open'),('upcoming','Upcoming'),('ongoing','Standing routes'),('unverified','Uncertain'),('closed','Closed')]
    def status_count(value):
        return len(records) if value=='all' else len([r for r in records if r['status'] in ('open','upcoming')]) if value=='available' else len([r for r in records if r['status']==value])
    assert len(jurisdictions)<=1, 'A human view must have a single jurisdiction'
    selected=jurisdictions[0] if jurisdictions else ''
    levels={r['participationLevel'] for r in records};level=next(iter(levels)) if len(levels)==1 else ''
    statuses=''.join('<button type="button" data-status-choice="'+v+'" aria-pressed="'+('true' if v==default else 'false')+'">'+e(t)+' <span>'+str(status_count(v))+'</span></button>' for v,t in status_options if v!='available' and (v=='all' or status_count(v)))
    topic_options=''.join('<option value="'+t+'">'+e(label)+' ('+str(sum(t in topic_keys(r) for r in records))+')</option>' for t,label in TOPICS.items() if any(t in topic_keys(r) for r in records))
    methods=dict(participation_method(r) for r in records)
    method_options=''.join('<option value="'+key+'">'+e(label)+' ('+str(sum(participation_method(r)[0]==key for r in records))+')</option>' for key,label in sorted(methods.items(),key=lambda item:item[1]))
    bodies=sorted({r['body'] for r in records});body_options=''.join('<option>'+e(b)+'</option>' for b in bodies)
    body_filter='<label>Responsible body<select name="body" data-default=""><option value="">All bodies in this view</option>'+body_options+'</select></label>' if len(bodies)>1 else '<input type="hidden" name="body" value="" data-default="">'
    return f'''<form class="filter-panel" id="participation-search" data-filters data-level="{e(level)}" data-scope-label="{e(scope_label)}" hidden><input type="hidden" name="jurisdiction" value="{selected}" data-default="{selected}"><input type="hidden" name="status" value="{default}" data-default="{default}"><label class="filter-search">Search in {e(scope_label)}<input type="search" name="search" placeholder="Search an issue, inquiry or committee" autocomplete="off" data-default=""></label><div class="status-choices" role="group" aria-label="Participation status">{statuses}</div><div class="filter-toolbar"><label>Sort by<select name="order" data-default="priority"><option value="priority">P4A matches first</option><option value="deadline">Closing soonest</option><option value="checked">Recently checked</option><option value="title">A to Z</option></select></label><label class="connected-filter"><input type="checkbox" name="connected"> P4A matches only</label><button type="button" data-reset>Clear filters</button></div><details class="filter-refinements"><summary>Choose a topic, way to participate or responsible body</summary><div class="filter-grid"><label>Topic<select name="topic" data-default=""><option value="">All topics</option>{topic_options}</select></label><label>How to take part<select name="method" data-default=""><option value="">All participation routes</option>{method_options}</select></label>{body_filter}</div></details></form><p class="results-count" data-results-count aria-live="polite">{len(records)} records in {e(scope_label)}. All records in this view are shown by default, including uncertainty.</p><noscript><p class="notice">All records for this view are shown below with status and participation details. Browser filters are available with JavaScript.</p></noscript><div class="participation-grid" data-records>{''.join(card(page,r) for r in ordered(records))}</div><p class="notice" data-empty hidden>No matching records in this view. Clear filters or check the official source for gaps.</p>'''

def build():
    OUT.mkdir(exist_ok=True)
    for path in ['styles.css','assets/participation.css','assets/participation.js','assets/site-nav.js','assets/site-map.css','assets/site-map.js','assets/external-links.js','assets/favicon.svg','assets/fonts/archivo-var.woff2','assets/fonts/jetbrains-mono-var.woff2','assets/fonts/archivo-OFL.txt','assets/fonts/jetbrains-mono-OFL.txt','LICENCE.md']:
        dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
    (OUT/'.nojekyll').write_text('',encoding='utf-8')
    (OUT/'data').mkdir(exist_ok=True)
    for name,data in [('registry',DATA),('councils',COUNCIL_DATA),('redland-committees',REDLAND_COMMITTEES),('committees',COMMITTEE_DATA),('council-pathways',COUNCIL_PATHWAY_DATA)]:
        (OUT/('data/'+name+'.json')).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    local=[r for r in RECORDS if 'homelands' in r.get('groups',[])]
    available=[r for r in RECORDS if r['status'] in ('open','upcoming')]
    parliament=[r for r in available if r.get('parliamentary') and r['status']=='open']
    page='index.html'
    body=hero('Have your say. Follow it through.','P4A’s founder and designer lives on North Stradbroke Island / Minjerribah. This starting path follows the layers of community and government that bind or influence his life: Redland City, Queensland and the Commonwealth. Use the navigation to explore participation across the rest of Australia.',side='<p class="eyebrow">Committees & inquiries</p><strong>All topics. Meaningful priorities.</strong><p>Open and upcoming opportunities are gathered across Australia. Genuine matches with existing P4A Twinkles and systems are highlighted, with the reason shown.</p>')
    body+='<p class="prose">To map the rules and public responsibilities that touch your own life, start with '+link(page,'https://auraofintelligence.github.io/australian-law-2012-lukes-relevance/pages/your-relevance.html','Your Relevance in Luke’s law workbench')+'.</p>'
    body+='<div class="button-row">'+link(page,'homelands/','Begin with Minjerribah & Redland','button')+'</div>'
    body+=f'<div class="status-strip"><span>Checked {pretty_date(CHECKED)}</span><span>'+link(page,'sources/','Coverage, gaps & verification')+'</span></div>'
    routes=[('homelands/','01 · Homelands','Committees affecting home','Committees and inquiries for Redland City, Queensland and Australia, each in its own view.'),('queensland/','02 · State','Queensland','Queensland Parliament and state-government opportunities. Search within this state level.'),('australia/','03 · Commonwealth','Australia','Federal Parliament and Commonwealth opportunities. Search within the national level.')]
    routes.append(('councils/','04 · Councils','Find another council','Choose a state, then your council. Checked participation rules and current invitations stay with that council.'))
    body+=section('Choose the body you want to influence','Each level has its own list and search. P4A topic matches are highlighted within the selected level. Use Inquiries & participation and choose a parliament for another jurisdiction.','<div class="route-grid">'+''.join('<a class="route-card feature-panel" href="'+e(rel(page,p))+'"><p class="eyebrow">'+e(t)+'</p><h3>'+e(title)+'</h3><p>'+e(d)+'</p></a>' for p,t,title,d in routes)+'</div>')
    body+='<p>'+link(page,'committees/','Browse every reviewed committee directory','button button-secondary')+'</p>'
    write(page,'Committees, inquiries & participation',body,'Open and upcoming public participation, beginning with Minjerribah and Redland City, with meaningful P4A connections highlighted.')

    page='councils/qld/redland/index.html'
    body=hero('Redland City participation.','Start with the decisions and community work that touch island life, alongside Redland City’s actual consultation, petition and meeting processes.','The homelands · Minjerribah & Redland City')
    body+='<div class="prose"><p>Minjerribah / North Stradbroke Island is on Quandamooka Country. Country, community governance, a council boundary and a parliamentary electorate have distinct roles. The island’s participation routes include community-led work as well as government decisions about land, water, services and access.</p><p>Follow '+link(page,'https://qyac.net.au/','Quandamooka Yoolooburrabee Aboriginal Corporation')+' for its own governance and community notices. A general council consultation does not convey Traditional Owners’ consent. Nation or member-specific processes keep their own eligibility.</p></div>'
    body+=section('Open invitations and upcoming community participation','Each card explains whether it is an inquiry, consultation, community expression of interest or event.',cards(page,[r for r in local if r['status'] in ('open','upcoming')]))
    body+=section('Use the council and community routes','Public addresses require approval. Petitions have their own rules. Watching a livestream is observation; no public remote-speaking entitlement has been verified.',cards(page,[r for r in local if r['status']=='ongoing']))
    uncertain_local=[r for r in local if r['status']=='unverified']
    if uncertain_local:body+=section('Uncertain invitations','These records remain visible with their source limitations.',cards(page,uncertain_local))
    body+=archive_link(page,'councils/qld/redland/','Minjerribah & Redland')
    body+=section('The connected P4A place journeys','Return to existing context and keep the participation record alongside the place.','<nav class="button-row" aria-label="P4A places">'+link(page,P4A+'pages/minjerribah.html','Minjerribah','button button-secondary')+link(page,P4A+'states/qld/councils/redland/index.html','Redland City','button button-secondary')+link(page,P4A+'states/qld/index.html','Queensland','button button-secondary')+link(page,P4A+'states/qld/places/federal/index.html','Federal representation','button button-secondary')+'</nav>')
    write(page,'Redland City participation',body)

    for j,route in [('qld','queensland'),('federal','australia')]:
        page=route+'/index.html';rs=[r for r in RECORDS if r['jurisdiction']==j and r['participationLevel'] in ('state','federal') and r['status']!='closed']
        description='Public submission calls, relevant state consultations and clearly labelled standing routes.' if j=='qld' else 'Senate, House and joint committee invitations, alongside relevant federal consultations.'
        body=hero('Queensland participation.' if j=='qld' else 'Have a say nationally.',description,cls='directory-hero')
        body+='<div class="notice">Every record for this level is shown by default. Status and uncertainty tags explain what is known. '+link(page,'sources/','Review source coverage and gaps')+'.</div>'
        body+=filters(page,rs,scope_label='Australia' if j=='federal' else NAMES[j])
        body+=archive_link(page,route+'/', 'Australian' if j=='federal' else NAMES[j])
        body+=section('Back to P4A’s place context','Existing council, state and federal journeys remain in P4A.','<div class="button-row">'+link(page,P4A+'states/qld/index.html','Queensland portal','button button-secondary')+link(page,P4A+'states/qld/places/federal/index.html','Queensland federal areas','button button-secondary')+link(page,P4A+'pages/places.html','All councils and electorates','button button-secondary')+'</div>')
        write(page,NAMES[j]+' participation',body)

    for j,name in NAMES.items():
        if j in ('qld','federal'): continue
        page='states/'+j+'/index.html'; rs=[r for r in RECORDS if r['jurisdiction']==j and r['participationLevel']=='state' and r['status']!='closed']
        body=hero(name+'.','Find a way to contribute, or browse this parliament’s complete reviewed committee directory.',cls='directory-hero')
        rows=[c for c in DATA['coverage'] if c['jurisdiction']==j]
        body+=filters(page,rs,scope_label=name) if rs else '<p class="notice">No open or upcoming call has been verified in this review. This does not establish that no participation opportunity exists. Use the official source below or the committee directory.</p>'
        body+='<details class="participation-method"><summary>Source coverage for '+e(name)+'</summary>'+coverage_table(page,rows)+'</details>'
        body+=archive_link(page,'states/'+j+'/',name)
        body+='<p>'+link(page,P4A+'states/'+j+'/index.html','P4A '+name+' portal','text-link')+' · '+link(page,P4A+'states/'+j+'/places/state/index.html','State / territory representation','text-link')+' · '+link(page,P4A+'states/'+j+'/places/federal/index.html','Federal representation','text-link')+'</p>'
        write(page,name+' participation',body)

    scopes=[('councils/qld/redland/','Minjerribah & Redland')]+[('australia/' if j=='federal' else 'queensland/' if j=='qld' else 'states/'+j+'/', 'Australian' if j=='federal' else name) for j,name in NAMES.items()]
    for route,label in scopes:
        page=archive_route(route)+'index.html'
        archived=[r for r in RECORDS if jurisdiction_route(r)==route and r['status']=='closed']
        description='Closed Commonwealth (federal) participation records, retaining their original sources and check dates.' if route=='australia/' else 'Closed participation records for this jurisdiction, retaining their original sources and check dates.'
        body=hero(label+' archive.',description,cls='archive-hero')
        body+='<p>'+link(page,route,'Return to current '+label+' opportunities','text-link')+'</p>'
        body+=filters(page,archived,scope_label=label+' archive') if archived else '<p class="notice">There are no closed records in this jurisdiction’s archive yet.</p>'
        body+='<p class="prose">A closed submission round can be followed by hearings, a report or another consultation. Use each original record to follow verified developments. Moving a record here does not refresh its source date or assert an outcome.</p>'
        write(page,label+' archive',body)

    page='archive/homelands/index.html'
    write(page,'Redland archive',hero('Redland archive.','Closed local participation rounds remain with Redland City and Minjerribah.',cls='archive-hero')+'<p>'+link(page,'archive/councils/qld/redland/','Open the Redland and Minjerribah archive','button')+'</p>')

    for r in RECORDS:
        page='opportunities/'+r['id']+'/index.html'
        body=hero(r['title'],r['purpose'],NAMES[r['jurisdiction']]+' · '+r['kind'])+badges(r)
        if r['status']=='unverified': body+='<p class="notice"><strong>Unverified invitation.</strong> This record is a lead to check. It is not presented as a confirmed open call.</p>'
        if r['status']=='closed': body+='<p class="notice"><strong>The recorded feedback round has closed.</strong> Follow the official source for outcomes or any new invitation.</p>'
        if r.get('statusNote'): body+='<p class="notice">'+e(r['statusNote'])+'</p>'
        facts=[('Responsible body',r['body']),('Place / scope',r.get('place',NAMES[r['jurisdiction']])),('How to take part',r['method']),('Deadline / next stage',deadline(r,True)),('Eligibility and restrictions',r['eligibility']),('What may become public',r['disclosure']),('What was checked',r['verification']),('Date checked',pretty_date(r['checked']))]
        body+='<div class="detail-layout"><div><dl class="fact-list">'+''.join('<dt>'+e(k)+'</dt><dd>'+e(v)+'</dd>' for k,v in facts)+'</dl>'
        if r.get('events'):body+='<section class="participation-section"><h2>Scheduled hearings</h2><p class="prose">A scheduled public hearing is separate from an invitation to give evidence. Check the official programme for attendance, access and witness arrangements.</p><ul>'+''.join('<li>'+e(pretty_date(event['date']))+' · '+e(event.get('label','Scheduled hearing'))+'</li>' for event in r['events'])+'</ul></section>'
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
    body+='<p class="notice">Latest source checks '+pretty_date(CHECKED)+'. Individual records retain their own review dates. Rebuilding does not refresh sources. Use the current official invitation before acting.</p>'
    body+='<div class="prose"><h2>Committees, inquiries and invitations</h2><p>The parliamentary directory contains '+str(len(COMMITTEES))+' entries from the reviewed official directories. A committee can have several inquiries, and an inquiry can continue after submissions close. Directory totals therefore describe bodies and listed roles, not open calls.</p><p>'+link(page,'committees/','Choose a parliament and browse its committees')+'. Each parliament’s Inquiries &amp; participation view keeps checked invitations separate and shows every current record, including uncertainty.</p><h2>Council coverage</h2><p>'+link(page,'councils/','The council chooser')+' includes 536 council identities and 16 separately labelled local bodies or unincorporated areas from existing P4A data. Redland retains its dedicated homeland path. '+str(sum(bool(c.get('review')) for c in COUNCILS))+' other councils have individually reviewed procedures. New pathway audits separately identify official destinations, indexed-only leads and source gaps. Detailed conditions remain unverified unless expressly reviewed. National consultation coverage remains incomplete.</p></div>'
    body+=coverage_table(page)
    from council_pathways import coverage_table as council_coverage_table
    body+=council_coverage_table(SimpleNamespace(**globals()),page)
    body+='<div class="prose"><h2>What the labels mean</h2><ul><li><strong>Open:</strong> a directly checked official invitation is accepting participation at the research date.</li><li><strong>Upcoming:</strong> an official source announces a future opening or a participation event, with restrictions shown.</li><li><strong>Standing route:</strong> a continuing mechanism with its own eligibility and application rules.</li><li><strong>Closed:</strong> the specific contribution round ended; a later project stage may continue.</li><li><strong>Unverified:</strong> a lead, inaccessible detail or ambiguous invitation that needs follow-up.</li></ul><h2>Coverage and evidence</h2><p>Every entry from an enumerated open-call index is represented, even where there is no P4A match. Current-inquiry lists can include closed submission windows, ongoing institutional scrutiny and hearings with invited witnesses. Those are reviewed separately. The directory does not assert coverage of every council, community organisation, government consultation or unpublished future inquiry.</p><p>Short summaries are original paraphrases. Each detail page retains its official links, field-level limits, eligibility, publication conditions and check date. Source-page copies, contact lists and browser material are not published.</p></div>'
    body+='<p>'+link(page,'data/registry.json','Download the dated public records','text-link')+' · '+link(page,'data/council-pathways.json','Council pathway audit','text-link')+' · '+link(page,REPO+'/blob/main/content/research-notes.md','Research and maintenance notes','text-link')+'</p>'
    write(page,'Sources & coverage',body)
    from directory_pages import build_directories
    build_directories(SimpleNamespace(**globals()))
    page='pages/site-map.html'
    intro='<section class="human-map-intro"><p class="eyebrow">P4A · Find your way</p><h1>Where would you like to go?</h1><p class="human-lead">Choose a public body, then search its participation opportunities. The directory below keeps each jurisdiction separate.</p><p class="human-map-date">Navigation reviewed '+pretty_date(CHECKED)+'. Source facts keep their own check dates.</p><div class="human-start-grid"><article><h2>Choose a jurisdiction</h2><p>Start with the public body whose decisions you want to influence.</p>'+link(page,'index.html','Choose your starting place')+'</article><article><h2>Follow the local path</h2><p>Minjerribah community and Redland City Council participation.</p>'+link(page,'homelands/','Open the local path')+'</article><article><h2>Keep exploring P4A</h2><p>The main site map connects the wider workbench.</p>'+link(page,P4A+'pages/site-map.html','Every P4A room')+'</article></div><div class="human-filter" hidden data-site-filter><label for="site-map-search">Find a page or topic</label><div><input id="site-map-search" type="search" placeholder="Try Redland, housing, health…" autocomplete="off"><button type="button" data-site-clear>Clear</button></div><p role="status" aria-live="polite" data-site-search-status></p></div></section>'
    groups=[('start','Start here',[('index.html','Committees and inquiries'),('homelands/index.html','Homelands committees and inquiries'),('inquiries/index.html','Choose a parliament for inquiries'),('committees/index.html','Choose a parliament for committees'),('take-part/index.html','How to take part'),('sources/index.html','Sources and coverage')])]
    for key,label,route in [('local','Minjerribah & Redland City','councils/qld/redland/')]+[(j,'Australia · Commonwealth' if j=='federal' else name,'australia/' if j=='federal' else 'queensland/' if j=='qld' else 'states/'+j+'/') for j,name in NAMES.items()]:
        rs=[r for r in RECORDS if ('homelands' in r.get('groups',[]) if key=='local' else r['jurisdiction']==key and r['participationLevel'] in ('state','federal'))]
        groups.append((key,label,[(route+'index.html',label+' participation'),(archive_route(route)+'index.html',label+' archive')]+[('opportunities/'+r['id']+'/index.html',r['title']) for r in ordered(rs)]))
    groups.append(('body-choices','Find a public body',[('councils/index.html','Council chooser'),('committees/index.html','Committee chooser'),('committees/redland/index.html','Redland committees')]))
    for j,name in NAMES.items():
        if j!='federal':
            council_items=[('councils/'+j+'/index.html',name+' council directory')]
            for c in COUNCILS:
                if c['jurisdiction']!=j or c['id']=='qld-council-6250':continue
                route=council_route(c);records=council_records(c['id'])
                council_items.append((route+'index.html',c['name']))
                if records:
                    council_items.append((archive_route(route)+'index.html',c['name']+' archive'))
                    council_items.extend(('opportunities/'+r['id']+'/index.html',r['title']) for r in records)
            groups.append(('councils-'+j,name+' councils',council_items))
        groups.append(('committees-'+j,('Australia' if j=='federal' else name)+' committees',[('committees/'+j+'/index.html',name+' committee directory')]+[(committee_route(c)+'index.html',c['name']) for c in COMMITTEES if c['jurisdiction']==j]))
    for key,label,items in groups:
        intro+='<details class="human-directory" id="map-'+key+'" data-site-group'+(' open' if key=='start' else '')+'><summary><strong>'+label+'</strong><span>'+str(len(items))+' pages</span></summary><ul>'+''.join('<li data-site-page data-search="'+e((t+' '+p+' '+label).lower())+'">'+link(page,p,t)+'</li>' for p,t in items)+'</ul></details>'
    write(page,'Find your way', '<div class="human-site-map">'+intro+'</div>')
    write('404.html','Page not found',hero('Find your way back.','This participation page could not be found.')+'<div class="button-row">'+link('404.html','index.html','Home','button')+link('404.html','index.html','Choose a jurisdiction','button button-secondary')+'</div>')
    urls=[BASE+('' if p=='index.html' else p.removesuffix('index.html')) for p,t in PAGES if p!='404.html']
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(u)+'</loc></url>' for u in urls)+'</urlset>\n',encoding='utf-8')
    shutil.copyfile(ROOT/'content/robots-policy.txt',OUT/'robots.txt')
    (OUT/'llms.txt').write_text('# P4A committees and participation\n\nLatest source checks '+CHECKED+'; individual records retain their own dates. Coverage gaps: '+BASE+'sources/. Topic priority is P4A editorial context, not official endorsement. This voluntary guide grants no additional reuse or AI-training permission. Third-party material retains its own rights.\n\n'+''.join('- ['+t+']('+BASE+('' if p=='index.html' else p.removesuffix('index.html'))+')\n' for p,t in PAGES if p!='404.html'),encoding='utf-8')
    expected_pages={p for p,t in PAGES}
    for stale in OUT.rglob('*.html'):
        if stale.relative_to(OUT).as_posix() not in expected_pages:
            assert stale.resolve().is_relative_to(OUT.resolve())
            stale.unlink()
    size=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    print(json.dumps({'pages':len(PAGES),'records':len(RECORDS),'artifactBytes':size,'checked':CHECKED}))

if __name__=='__main__':
    build()
