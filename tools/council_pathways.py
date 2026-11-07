"""Present source-verified pathways separately from fully reviewed procedures."""

def pathway_count(s,council):
    audit=s.COUNCIL_PATHWAYS.get(council['id'],{})
    return sum(p['access']!='indexed-only' for p in audit.get('pathways',[]))

def coverage(s,rows):
    audited=[s.COUNCIL_PATHWAYS[c['id']] for c in rows if c['id'] in s.COUNCIL_PATHWAYS]
    known=sum(bool(c.get('review')) or c['id']=='qld-council-6250' or any(p['access']!='indexed-only' for p in s.COUNCIL_PATHWAYS.get(c['id'],{}).get('pathways',[])) for c in rows)
    rules=sum(bool(c.get('review')) or c['id']=='qld-council-6250' for c in rows)
    if not audited:return ''
    return '<p class="notice">Official participation pathways found for '+str(known)+' of '+str(len(rows))+' local areas. '+str(len(audited))+' source audits recorded; profiles show access gaps and routes still needing follow-up. '+str(rules)+' profiles also have separately reviewed participation procedures. This is not a count of open consultations.</p>'

def coverage_table(s,page):
    body='<div class="coverage-table-wrap"><table class="coverage-table"><caption>Council pathway coverage; counts are local areas, not open invitations</caption><thead><tr><th>Location</th><th>Areas</th><th>Located routes or prior procedures</th><th>New source audits</th></tr></thead><tbody>'
    for j,name in s.NAMES.items():
        if j=='federal':continue
        rows=[c for c in s.COUNCILS if c['jurisdiction']==j]
        located=sum(bool(c.get('review')) or c['id']=='qld-council-6250' or bool(s.COUNCIL_PATHWAYS.get(c['id'],{}).get('pathways')) for c in rows)
        audited=sum(c['id'] in s.COUNCIL_PATHWAYS for c in rows)
        body+='<tr><th scope="row">'+s.link(page,'councils/'+j+'/',name)+'</th><td>'+str(len(rows))+'</td><td>'+('No separate local council' if j=='act' else str(located))+'</td><td>'+str(audited)+'</td></tr>'
    return body+'</tbody></table></div><p class="prose">Located routes include explicitly uncertain indexed leads. Conditions remain unverified unless individually reviewed. Redland’s existing work and the ACT’s separate governance explanation are retained.</p>'

def render(s,page,council):
    audit=s.COUNCIL_PATHWAYS.get(council['id'])
    if not audit:return ''
    routes=audit['pathways']
    body='<section id="participation-pathways" class="council-pathways" data-council-pathways="'+s.e(council['id'])+'"><h2>Official participation pathways</h2><p class="prose">Sources checked '+s.pretty_date(audit['checked'])+'. Each route has its own eligibility, timing, publication and recording rules. Conditions not expressly reviewed below remain unverified. A link does not establish an open invitation or permission to speak.</p>'
    if routes:
        labels={'consultation':'Consultations and feedback','consultation-project':'Consultation project; status unverified','petitions':'Petitions','meeting-participation':'Questions and speaking','meeting-information':'Meetings and agendas','community-reference':'Community reference groups'}
        body+='<ul class="council-pathway-list">'
        for route in routes:
            label=labels.get(route['type'],route['type'].replace('-',' ').capitalize())
            body+='<li><span class="eyebrow">'+s.e(label)+'</span><h3>'+s.link(page,route['url'],route['title'])+'</h3>'
            method=route.get('method','')
            if method.startswith('Use this official engagement'):method='Browse project invitations and follow each project’s participation steps.'
            elif method.startswith('Use the official meeting page'):method='Check meeting dates, agendas and access arrangements. Observation does not confer permission to speak.'
            if method:body+='<p>'+s.e(method)+'</p>'
            if route['access']=='indexed-only':body+='<p class="pathway-limits"><strong>Uncertain:</strong> official indexed source only. The current destination could not be read.</p>'
            elif route['access'] not in ('page-read','directly-reviewed','direct-read'):body+='<p class="pathway-limits">Official link verified; destination access or detailed conditions remain limited.</p>'
            body+='<details class="participation-method"><summary>Source and conditions checked</summary><p>'+s.e(route['verification'])+'</p>'
            for field,label in [('timing','Timing'),('eligibility','Eligibility'),('disclosure','What may become public')]:
                if route.get(field):body+='<p><strong>'+label+':</strong> '+s.e(route[field])+'</p>'
            source=s.link(page,route['sourceUrl'],'Official source identifying this route') if s.source_key(route['sourceUrl'])!=s.source_key(route['url']) else 'Official page linked above'
            body+='<p>'+source+' · checked '+s.pretty_date(route['checked'])+'</p></details></li>'
        body+='</ul>'
    else:
        body+='<p class="notice">No direct participation pathway was confirmed in this source check. This does not mean no route exists. Use the council’s published source and the access notes below.</p>'
    if audit['limits']:body+='<details class="participation-method"><summary>Source access and remaining gaps</summary><ul>'+''.join('<li>'+s.e(note)+'</li>' for note in audit['limits'])+'</ul></details>'
    if audit.get('contactDirectory'):
        directory=audit['contactDirectory']
        body+='<p class="notice">'+s.link(page,directory['url'],directory['title'])+' can help you find the council’s published contact details and ask which participation process applies. This is a contact lookup, not a verified speaking or submission invitation.</p>'
    return body+'</section>'
