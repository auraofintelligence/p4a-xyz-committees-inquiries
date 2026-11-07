"""Validate source records, rendered routes, dates, theme assets and small artifact."""
from pathlib import Path
from datetime import date
from html.parser import HTMLParser
import hashlib
import json
import re
from urllib.parse import unquote,urlsplit
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'_site'

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.links=[];self.ids=[];self.h1=0;self.records=[];self.title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='h1':self.h1+=1
        if tag=='title':self.title=True
        if 'data-record' in a:self.records.append(a)
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag in ('script','img','link'):
            target=a.get('src') or a.get('href')
            if target:self.links.append(target)
        if tag=='a' and a.get('href','').startswith('https://') and not a['href'].startswith('https://p4a.xyz/'):
            assert a.get('target')=='_blank' and 'noopener' in a.get('rel',''), 'External link policy'

def validate():
    data=json.loads((ROOT/'data/registry.json').read_text(encoding='utf-8'))
    checked=date.fromisoformat(data['checked']);records=data['records'];ids=set()
    councils=json.loads((ROOT/'data/councils.json').read_text(encoding='utf-8'))['councils']
    committee_data=json.loads((ROOT/'data/committees.json').read_text(encoding='utf-8'))
    committees=committee_data['committees']
    assert len({c['id'] for c in councils})==len(councils)
    assert len({(c['jurisdiction'],c['slug']) for c in councils})==len(councils)
    assert len({c['id'] for c in committees})==len(committees)
    council_ids={c['id'] for c in councils};committee_ids={c['id'] for c in committees}
    for c in committees:
        assert re.fullmatch('[a-z0-9-]+',c['id']),c['id']
        assert c['name'] and c['sourceUrl'].startswith('https://')
        assert date.fromisoformat(c['checked'])<=checked
        for inquiry in c.get('inquiries',[]):assert inquiry['title'] and inquiry['sourceUrl'].startswith('https://')
    for directory in committee_data['directories']:
        assert directory['listedCount']==sum(c['jurisdiction']==directory['jurisdiction'] for c in committees),directory
    for r in records:
        ident=r['id'];assert ident not in ids and re.fullmatch('[a-z0-9-]+',ident),ident;ids.add(ident)
        for field in ('title','body','purpose','method','eligibility','disclosure','sourceUrl','verification','checked'):
            assert r.get(field),f'{ident}: missing {field}'
        assert r['status'] in {'open','upcoming','closed','unverified','ongoing'},ident
        assert r['jurisdiction'] in {'qld','nsw','vic','wa','sa','tas','act','nt','federal'}
        assert r['participationLevel'] in {'council','community','state','federal'}
        if r.get('councilId'):assert r['councilId'] in council_ids and r['participationLevel']=='council'
        if r.get('committeeId'):assert r['committeeId'] in committee_ids and r['participationLevel'] in ('state','federal')
        assert date.fromisoformat(r['checked'])<=checked
        d=r['deadline'];assert all(k in d for k in ('date','time','timezone')),ident
        if d.get('date'):
            assert date.fromisoformat(d['date']).isoformat()==d['date']
            assert not (r['status']=='open' and date.fromisoformat(d['date'])<checked),ident+': stale open deadline'
        if d.get('time'):assert re.fullmatch(r'\d\d:\d\d',d['time']),ident
        if d.get('precision')=='date':assert not d.get('time'),ident+': invented date-only time'
        assert r['sourceUrl'].startswith('https://') and r.get('sources')
        assert r['priority']==0 if not r.get('connections') else r['priority']>0
        for c in r.get('connections',[]):
            assert c['url'].startswith('https://p4a.xyz/') and c['reason'] and c['type'] in ('system','twinkle')
        assert '\ufffd' not in json.dumps(r,ensure_ascii=False),ident+': damaged Unicode'
    pages={p.relative_to(OUT).as_posix():p for p in OUT.rglob('*.html')}
    parsed={}
    for name,path in pages.items():
        parser=Page();parser.feed(path.read_text(encoding='utf-8'));parsed[name]=parser
        assert parser.h1==1 and parser.title,name+': heading/title'
        assert len(parser.ids)==len(set(parser.ids)),name+': duplicate IDs'
    broken=[];local_links=0;external=set()
    for name,p in parsed.items():
        for target in p.links:
            u=urlsplit(target)
            if u.scheme or u.netloc:
                if u.scheme in ('https','http'):external.add(target)
                continue
            local_links+=1
            dest=(pages[name].parent/unquote(u.path)).resolve() if u.path else pages[name]
            assert dest.is_relative_to(OUT.resolve()),(name,target)
            if dest.is_dir():dest=dest/'index.html'
            if not dest.is_file():broken.append((name,target));continue
            if u.fragment and dest.suffix=='.html':
                dest_name=dest.relative_to(OUT).as_posix()
                if unquote(u.fragment) not in parsed[dest_name].ids:broken.append((name,target))
    assert not broken,broken[:10]
    views=['homelands/index.html','queensland/index.html','australia/index.html']+['states/'+j+'/index.html' for j in ('nsw','vic','wa','sa','tas','act','nt')]
    active_views=list(views)
    for council in councils:
        if council['id']=='qld-council-6250':continue
        route='councils/'+council['jurisdiction']+'/'+council['slug']+'/index.html'
        assert route in parsed,route
        active_views.append(route)
        assert all(r['data-council']==council['id'] and r['data-level']=='council' for r in parsed[route].records),route+': another council appears here'
        directory='councils/'+council['jurisdiction']+'/index.html'
        assert not parsed[directory].records,directory+': council chooser must not combine opportunity records'
    views=list(active_views)
    archive_views=['archive/'+view for view in active_views if 'archive/'+view in parsed]
    views+=archive_views
    all_view_records=[r for view in views for r in parsed[view].records]
    assert len(all_view_records)==len(records), 'A record is missing or repeated across jurisdiction views'
    assert {r['data-id'] for r in all_view_records}==ids
    assert not parsed['councils/index.html'].records and not parsed['committees/index.html'].records
    for committee in committees:
        route='committees/'+committee['jurisdiction']+'/'+committee['id']+'/index.html'
        assert route in parsed,route
        assert all(r['data-jurisdiction']==committee['jurisdiction'] and r['data-level'] in ('state','federal') and (not r.get('data-committee') or r['data-committee']==committee['id']) for r in parsed[route].records),route+': unrelated body records'
    assert not parsed['index.html'].records, 'Home must offer jurisdiction choices, not a combined opportunity list'
    assert all(r['data-level']=='federal' for r in parsed['australia/index.html'].records), 'Australia contains a state or council record'
    assert all(r['data-level']=='federal' for r in parsed['archive/australia/index.html'].records), 'Australia archive contains a state or council record'
    assert all(r['data-status']!='closed' for view in active_views for r in parsed[view].records), 'A closed record remains in a current view'
    assert all(r['data-status']=='closed' for view in archive_views for r in parsed[view].records), 'An archive contains a current record'
    # Every official enumerated open index has at least its recorded count in the
    # jurisdiction catalogue; additional direct invitations may be outside it.
    for c in data['coverage']:
        count=c.get('observedOpenCount')
        if count is not None:
            assert len([r for r in records if r['jurisdiction']==c['jurisdiction'] and r['status'] in ('open','unverified')])>=count,c
    for route in ['queensland/index.html']+['states/'+j+'/index.html' for j in ('nsw','vic','wa','sa','tas','act','nt')]:
        assert all(r['data-level']=='state' for r in parsed[route].records), route+': council/community record in state view'
    for font in ('archivo-var.woff2','jetbrains-mono-var.woff2'):
        assert (OUT/'assets/fonts'/font).stat().st_size>10000
    assert hashlib.sha256((ROOT/'styles.css').read_bytes()).hexdigest()==data['theme']['sha256'], 'P4A theme differs from its reviewed punctuation-normalised copy'
    for url in re.findall(r'url\("([^"]+)"\)',(OUT/'styles.css').read_text(encoding='utf-8')):
        if not url.startswith(('data:','http')):assert (OUT/url).is_file(),url
    files=[p for p in OUT.rglob('*') if p.is_file()]
    assert all(p.suffix not in ('.png','.jpg','.webp','.py','.map') for p in files),'Unnecessary internal artifact'
    assert not any(p.name in ('AGENTS.md','README.md') for p in files)
    forbidden = [chr(8212), '&m'+'dash;', '&#'+'8212;', '&#x'+'2014;', chr(92)+'u'+'2014']
    for path in ROOT.rglob('*'):
        if not path.is_file() or '.git' in path.parts:continue
        try:text=path.read_text(encoding='utf-8')
        except UnicodeError:continue
        assert not any(token.lower() in text.lower() for token in forbidden), 'Forbidden punctuation in '+str(path)
    size=sum(p.stat().st_size for p in files);assert size<10_000_000, 'Pages artifact over the small national-directory budget'
    ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls=[n.text for n in ET.parse(OUT/'sitemap.xml').findall('s:url/s:loc',ns)]
    assert len(urls)==len(pages)-1 and len(urls)==len(set(urls))
    print(json.dumps({'records':len(records),'htmlPages':len(pages),'localLinksChecked':local_links,'externalURLs':len(external),'artifactBytes':size,'theme':'P4A; comment punctuation normalised','emDashCount':0,'result':'PASS'}))

if __name__=='__main__':validate()
