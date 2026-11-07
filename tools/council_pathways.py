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

def render(s,page,council):
    audit=s.COUNCIL_PATHWAYS.get(council['id'])
    if not audit:return ''
    routes=audit['pathways']
    body='<section class="council-pathways" data-council-pathways="'+s.e(council['id'])+'"><h2>Official participation pathways</h2><p class="prose">Sources checked '+s.pretty_date(audit['checked'])+'. These links show where to look or apply. They do not establish that a project is open or that a person has permission to speak.</p>'
    if routes:
        labels={'consultation':'Consultations and feedback','petitions':'Petitions','meeting-participation':'Questions and speaking','meeting-information':'Meetings and agendas','community-reference':'Community reference groups'}
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
            body+='<p>'+s.link(page,route['sourceUrl'],'Official source identifying this route')+' · checked '+s.pretty_date(route['checked'])+'</p></details></li>'
        body+='</ul><p class="prose">Check each current invitation or procedure for eligibility, cutoffs, publication, names and recording conditions. Details not explicitly reviewed here remain unverified. A meeting-information link alone does not establish a speaking right.</p>'
    else:
        body+='<p class="notice">No direct participation pathway was confirmed in this source check. This does not mean no route exists. Use the council’s published source and the access notes below.</p>'
    if audit['limits']:body+='<details class="participation-method"><summary>Source access and remaining gaps</summary><ul>'+''.join('<li>'+s.e(note)+'</li>' for note in audit['limits'])+'</ul></details>'
    return body+'</section>'
