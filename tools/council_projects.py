"""Live-project research is separate from body inventories and procedure links."""

def fact(s,value):
    if value is None:return 'Not confirmed'
    if isinstance(value,bool):return 'Yes' if value else 'No'
    if isinstance(value,dict):return '; '.join(s.e(str(k).replace('_',' ').capitalize())+': '+fact(s,v) for k,v in value.items())
    if isinstance(value,list):return '; '.join(fact(s,v) for v in value)
    return s.e(value)


def item(s,page,value):
    if not isinstance(value,dict):return s.e(value)
    title=value.get('title') or value.get('label') or value.get('body') or value.get('name') or ''
    note=value.get('note') or value.get('reason') or value.get('finding') or value.get('purpose') or ''
    extra=' '.join(str(value[k]) for k in ('scope','disclosure') if value.get(k))
    text=s.link(page,value['url'],title or 'Official source') if value.get('url') else s.e(title)
    if note:text+=('<p>' if text else '')+s.e(note)+('</p>' if text else '')
    if extra:text+='<p>'+s.e(extra)+'</p>'
    return text


def render(s,page,council):
    audit=s.COUNCIL_PROJECTS.get(council['id'])
    if not audit:
        return '<p class="notice" data-project-coverage><strong>Current consultation catalogue not yet systematically reviewed.</strong> Committee and procedure research below does not establish which projects are accepting input. Check the official sources for further invitations.</p>'
    body='<section class="council-project-review" data-project-coverage><h2>Current contribution research</h2><p class="status-strip">Checked '+s.pretty_date(audit['checked'])+' · '+s.e(audit['coverageStatus'])+'</p><p>'+s.e(audit['summary'])+'</p>'
    body+='<details class="participation-method"><summary>Scope, source checks and remaining gaps</summary><p>'+s.e(audit['scope'])+'</p>'
    if audit.get('enumeration'):
        body+='<dl class="fact-list">'+''.join('<dt>'+s.e(k)+'</dt><dd>'+fact(s,v)+'</dd>' for k,v in audit['enumeration'].items())+'</dl>'
    if audit.get('sectionsReviewed'):body+='<p><strong>Sections checked:</strong> '+s.e('; '.join(audit['sectionsReviewed']))+'</p>'
    for label,key in [('Findings','findings'),('Coverage gaps','gaps'),('Excluded past rounds','closedExclusions')]:
        if audit.get(key):body+='<h3>'+label+'</h3><ul>'+''.join('<li>'+item(s,page,v)+'</li>' for v in audit[key])+'</ul>'
    if audit.get('sources'):
        body+='<ul class="source-list">'+''.join('<li>'+s.link(page,v['url'],v.get('title','Official source'))+('<small>'+s.e(v['note'])+'</small>' if v.get('note') else '')+'</li>' for v in audit['sources'])+'</ul>'
    body+='</details>'
    if audit.get('otherLeads'):
        body+='<details class="participation-method"><summary>Other uncertain leads and planned processes</summary><ul>'+''.join('<li>'+item(s,page,v)+'</li>' for v in audit['otherLeads'])+'</ul></details>'
    if audit.get('referrals'):
        body+='<h3>Related processes with another responsible body</h3><ul>'+''.join('<li>'+item(s,page,v)+'</li>' for v in audit['referrals'])+'</ul>'
    return body+'</section>'

def coverage(s,page):
    rows=list(s.COUNCIL_PROJECTS.values())
    counts={}
    for audit in rows:
        status=audit['coverageStatus'];counts[status]=counts.get(status,0)+1
    body='<section class="participation-section"><h2>Current council consultations</h2><p>'+str(len(rows))+' local areas have a separately recorded project-level review. This is distinct from finding a consultation portal, standing procedure or committee list. A partial review or blocked source is not a finding of zero opportunities. Redland and Brisbane retain their earlier dated project reviews.</p><ul>'+''.join('<li>'+s.e(status)+': '+str(count)+'</li>' for status,count in sorted(counts.items()))+'</ul><p>Other council pages state that current-project enumeration remains unchecked. Future refreshes must revisit current lists, pagination, individual contribution tools, dates and collection notices, rather than treating a published project as an open invitation.</p><p>'+s.link(page,s.REPO+'/blob/main/data/council-project-audits.json','Council project research and source-access gaps')+'</p></section>'
    body+='<p>'+s.link(page,s.REPO+'/blob/main/content/remaining-council-research.md','Remaining council research: exact areas and known leads')+'</p>'
    return body
