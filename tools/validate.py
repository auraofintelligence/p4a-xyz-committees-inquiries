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
        self.section_navigation=None;self.legacy_level_tabs=0
        self._navigation_stack=[];self._navigation_link=None;self._parliament_summary=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        classes=a.get('class','').split()
        if 'level-tabs' in classes:self.legacy_level_tabs+=1
        if tag=='nav' and 'participation-nav' in classes:
            assert self.section_navigation is None, 'Repeated committees navigation'
            self.section_navigation={'links':[],'browse':[],'parliaments':[],'summaries':[]}
            self._navigation_stack.append((tag,a))
        elif self._navigation_stack:
            ancestor_classes={c for _,attributes in self._navigation_stack for c in attributes.get('class','').split()}
            if tag=='a':
                self._navigation_link={**a,'label':''}
                self.section_navigation['links'].append(self._navigation_link)
                if 'committee-browse' in ancestor_classes:self.section_navigation['browse'].append(self._navigation_link)
                if 'participation-parliament-menu' in ancestor_classes:self.section_navigation['parliaments'].append(self._navigation_link)
            if tag=='summary' and 'participation-parliament-menu' in ancestor_classes:
                self._parliament_summary={'label':''}
                self.section_navigation['summaries'].append(self._parliament_summary)
            if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
                self._navigation_stack.append((tag,a))
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

    def handle_data(self,text):
        if self._navigation_link is not None:self._navigation_link['label']+=text
        if self._parliament_summary is not None:self._parliament_summary['label']+=text

    def handle_endtag(self,tag):
        if not self._navigation_stack:return
        if tag=='a':self._navigation_link=None
        if tag=='summary':self._parliament_summary=None
        for i in range(len(self._navigation_stack)-1,-1,-1):
            if self._navigation_stack[i][0]==tag:
                self._navigation_stack=self._navigation_stack[:i]
                break


def validate_navigation(parsed,pages,committees,records):
    """Check that task and parliament switches keep a visitor in one scope."""
    def destination(page,link):
        target=urlsplit(link['href'])
        assert not target.scheme and not target.netloc,(page,'Section navigation leaves this P4A section')
        result=(pages[page].parent/unquote(target.path)).resolve()
        assert result.is_relative_to(OUT.resolve()),(page,link['href'])
        if result.is_dir():result/='index.html'
        return result.relative_to(OUT).as_posix()
    jurisdictions=('federal','qld','nsw','vic','wa','sa','tas','act','nt')
    participation={'federal':'australia/index.html','qld':'queensland/index.html',**{j:'states/'+j+'/index.html' for j in jurisdictions if j not in ('federal','qld')}}
    committee_routes={j:'committees/'+j+'/index.html' for j in jurisdictions}
    participation['redland']='councils/qld/redland/index.html';committee_routes['redland']='committees/redland/index.html'
    for page,document in parsed.items():
        navigation=document.section_navigation
        assert navigation is not None,page+': missing committees navigation'
        assert not document.legacy_level_tabs,page+': duplicated task navigation'
        labels=[' '.join(a['label'].split()) for a in navigation['browse']]
        assert labels==['Inquiries & participation','All committees'],page+': task choices are unclear'
        assert len(navigation['parliaments'])==10,page+': committee-scope choices are missing or duplicated'
        assert len(navigation['summaries'])==1 and 'Parliament' in navigation['summaries'][0]['label'],page+': missing parliament label'
        assert sum(a.get('aria-current')=='location' for a in navigation['browse'])<=1,page+': multiple current tasks'
        assert sum(a.get('aria-current')=='location' for a in navigation['parliaments'])<=1,page+': multiple current parliaments'
        for link in navigation['links']:
            route=destination(page,link)
            assert (not route.startswith('councils/') or route==participation['redland'] or (route=='councils/index.html' and ' '.join(link['label'].split())=='Council participation')) and '/places/' not in route,page+': unrelated place navigation in committees menu'
    for chooser in ('inquiries/index.html','committees/index.html','homelands/index.html'):
        assert chooser in parsed and not parsed[chooser].records,chooser+': chooser combines participation records'
    cases=[('inquiries/index.html','inquiries',None),('committees/index.html','committees',None)]
    for j in ('nsw','qld','federal'):
        cases.extend([(participation[j],'inquiries',j),(committee_routes[j],'committees',j)])
        committee=next(c for c in committees if c['jurisdiction']==j)
        cases.append(('committees/'+j+'/'+committee['id']+'/index.html','committees',j))
        opportunity=next(r for r in records if r['jurisdiction']==j and r.get('parliamentary') and r['status']!='closed')
        cases.append(('opportunities/'+opportunity['id']+'/index.html','inquiries',j))
    cases.extend([(participation['redland'],'inquiries','redland'),(committee_routes['redland'],'committees','redland')])
    for page,task,jurisdiction in cases:
        navigation=parsed[page].section_navigation
        browse=navigation['browse'];parliaments=navigation['parliaments']
        selected=[a for a in browse if a.get('aria-current')=='location']
        assert len(selected)==1 and ' '.join(selected[0]['label'].split())==('All committees' if task=='committees' else 'Inquiries & participation'),page+': current task is not stated'
        expected=committee_routes if task=='committees' else participation
        assert {destination(page,a) for a in parliaments}==set(expected.values()),page+': changing parliament loses the selected task'
        assert destination(page,browse[0])==(participation[jurisdiction] if jurisdiction else 'inquiries/index.html'),page+': inquiry switch loses the selected parliament'
        assert destination(page,browse[1])==(committee_routes[jurisdiction] if jurisdiction else 'committees/index.html'),page+': committee switch loses the selected parliament'
        selected_parliaments=[a for a in parliaments if a.get('aria-current')=='location']
        assert len(selected_parliaments)==(1 if jurisdiction else 0),page+': selected parliament is ambiguous'
        if jurisdiction:assert destination(page,selected_parliaments[0])==expected[jurisdiction],page+': wrong selected parliament'
    for page,document in parsed.items():
        if page.startswith('councils/') and page!=participation['redland']:
            assert not any(a.get('aria-current')=='location' for a in document.section_navigation['parliaments']),page+': council profile pretends a parliament is selected'

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
    pathway_file=ROOT/'data/council-pathways.json'
    pathways=json.loads(pathway_file.read_text(encoding='utf8'))['audits'] if pathway_file.exists() else []
    assert len({a['councilId'] for a in pathways})==len(pathways)
    for audit in pathways:
        assert audit['councilId'] in council_ids and audit['councilId']!='qld-council-6250'
        assert date.fromisoformat(audit['checked'])<=checked
        assert audit['sourceUrl'].startswith(('https://','http://'))
        assert len({p['url'] for p in audit['pathways']})==len(audit['pathways'])
        for pathway in audit['pathways']:
            assert all(pathway.get(k) for k in ('title','type','url','sourceUrl','verification','access','checked'))
            assert pathway['url'].startswith(('https://','http://')) and pathway['sourceUrl'].startswith(('https://','http://'))
            assert date.fromisoformat(pathway['checked'])<=checked
            assert 'evidenceExcerpt' not in pathway and 'html' not in pathway
    body_audits=json.loads((ROOT/'data/council-bodies.json').read_text(encoding='utf8'))['audits']
    from council_bodies import REVIEW_OUTCOMES
    assert len({a['councilId'] for a in body_audits})==len(body_audits)
    for audit in body_audits:
        assert audit['councilId'] in council_ids and audit['councilId']!='qld-council-6250'
        assert date.fromisoformat(audit['checked'])<=checked
        assert audit.get('coverageStatus')
        if audit.get('reviewOutcome'):assert audit['reviewOutcome'] in REVIEW_OUTCOMES,audit['councilId']+': unknown research outcome'
        if audit.get('sourceUrl'):assert audit['sourceUrl'].startswith(('https://','http://'))
        else:assert next(c for c in councils if c['id']==audit['councilId'])['kind']!='council' and not audit['committees'] and not audit['standingInvitations'] and audit['gaps']
        assert len({(b['name'].casefold(),b['url']) for b in audit['committees']})==len(audit['committees'])
        for body in audit['committees']:
            assert all(body.get(k) for k in ('name','url','participation','verification'))
            assert body['url'].startswith(('https://','http://'))
            assert not any(k in body for k in ('html','evidenceExcerpt'))
        for invitation in audit['standingInvitations']:
            assert all(invitation.get(k) for k in ('title','url','method','verification'))
            assert invitation['url'].startswith(('https://','http://'))
            for source in invitation.get('relatedSources',[]):assert source['title'] and source['url'].startswith(('https://','http://'))
    from build import source_key
    from council_bodies import CORRECTIONS,procedure_key
    rejected={source_key(e['url']) for e in CORRECTIONS['excludeStanding']}
    for audit in body_audits:
        assert all(source_key(i['url']) not in rejected for i in audit['standingInvitations']),audit['councilId']+': excluded source returned as invitation'
        for group in CORRECTIONS['equivalentProcedures']:
            if group['councilId']==audit['councilId']:
                assert sum(procedure_key(source_key,audit['councilId'],i['url'])==source_key(group['primaryUrl']) for i in audit['standingInvitations'])<=1,audit['councilId']+': equivalent procedures counted twice'
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
    validate_navigation(parsed,pages,committees,records)
    views=['queensland/index.html','australia/index.html']+['states/'+j+'/index.html' for j in ('nsw','vic','wa','sa','tas','act','nt')]
    active_views=list(views)
    for council in councils:
        route='councils/'+council['jurisdiction']+'/'+council['slug']+'/index.html'
        assert route in parsed,route
        active_views.append(route)
        if council['id']=='qld-council-6250':
            local_ids={r['id'] for r in records if r.get('councilId')==council['id'] or 'homelands' in r.get('groups',[])}
            assert all(r['data-id'] in local_ids and r['data-level'] in ('council','community') for r in parsed[route].records),route+': unrelated local participation'
        else:
            assert all(r['data-council']==council['id'] and r['data-level']=='council' for r in parsed[route].records),route+': another council appears here'
        audit=next((a for a in body_audits if a['councilId']==council['id']),None)
        if audit:
            source=pages[route].read_text(encoding='utf8')
            assert source.count('<li data-council-body>')==len(audit['committees']),route+': a named body is missing'
            from build import source_key
            from council_bodies import procedure_key,uncertain_body
            body_section=re.search(r'<section id="council-committees"[^>]*>.*?</section>',source,re.S)
            assert body_section,route+': missing council body section'
            assert body_section[0].count('class="status-badge status-unverified"')==sum(uncertain_body(b) for b in audit['committees']),route+': uncertainty labels do not match source status'
            procedure_sources={procedure_key(source_key,council['id'],m['sourceUrl']) for m in council.get('review',{}).get('mechanisms',[])}
            extras=[i for i in audit['standingInvitations'] if procedure_key(source_key,council['id'],i['url']) not in procedure_sources]
            assert source.count('data-standing-invitation')==len(extras),route+': a standing invitation is missing'
        directory='councils/'+council['jurisdiction']+'/index.html'
        assert not parsed[directory].records,directory+': council chooser must not combine opportunity records'
    views=list(active_views)
    archive_views=['archive/'+view for view in active_views if 'archive/'+view in parsed]
    views+=archive_views
    all_view_records=[r for view in views for r in parsed[view].records]
    assert len(all_view_records)==len(records), 'A record is missing or repeated across jurisdiction views'
    assert {r['data-id'] for r in all_view_records}==ids
    assert not parsed['councils/index.html'].records and not parsed['committees/index.html'].records
    assert not parsed['archive/homelands/index.html'].records,'Legacy homeland archive must point to the scoped Redland archive without duplicating records'
    assert not parsed['committees/redland/index.html'].records,'A council committee listing must not imply a public invitation'
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
