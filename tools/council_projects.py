"""Live-project research is separate from body inventories and procedure links."""

def render(s,page,council):
    audit=s.COUNCIL_PROJECTS.get(council['id'])
    if not audit:
        return '<p class="notice" data-project-coverage><strong>Current consultation catalogue not yet systematically reviewed.</strong> Committee and procedure research below does not establish which projects are accepting input. Check the official sources for further invitations.</p>'
    body='<section class="council-project-review" data-project-coverage><h2>Current contribution research</h2><p class="status-strip">Checked '+s.pretty_date(audit['checked'])+' · '+s.e(audit['coverageStatus'])+'</p><p>'+s.e(audit['summary'])+'</p>'
    body+='<details class="participation-method"><summary>Scope, source checks and remaining gaps</summary><p>'+s.e(audit['scope'])+'</p>'
    if audit.get('enumeration'):
        body+='<dl class="fact-list">'+''.join('<dt>'+s.e(k)+'</dt><dd>'+s.e(v)+'</dd>' for k,v in audit['enumeration'].items())+'</dl>'
    if audit.get('sectionsReviewed'):body+='<p><strong>Sections checked:</strong> '+s.e('; '.join(audit['sectionsReviewed']))+'</p>'
    for label,key in [('Findings','findings'),('Coverage gaps','gaps'),('Excluded past rounds','closedExclusions')]:
        if audit.get(key):body+='<h3>'+label+'</h3><ul>'+''.join('<li>'+s.e(v)+'</li>' for v in audit[key])+'</ul>'
    if audit.get('sources'):
        body+='<ul class="source-list">'+''.join('<li>'+s.link(page,v['url'],v.get('title','Official source'))+('<small>'+s.e(v['note'])+'</small>' if v.get('note') else '')+'</li>' for v in audit['sources'])+'</ul>'
    body+='</details>'
    if audit.get('otherLeads'):
        body+='<details class="participation-method"><summary>Other uncertain leads and planned processes</summary><ul>'+''.join('<li>'+s.link(page,v['url'],v['title'])+'<p>'+s.e(v['note'])+'</p>' for v in audit['otherLeads'])+'</ul></details>'
    if audit.get('referrals'):
        body+='<h3>Related processes with another responsible body</h3><ul>'+''.join('<li>'+s.link(page,v['url'],v['title'])+'<p>'+s.e(v['note'])+'</p></li>' for v in audit['referrals'])+'</ul>'
    return body+'</section>'

def coverage(s,page):
    rows=list(s.COUNCIL_PROJECTS.values())
    counts={}
    for audit in rows:
        status=audit['coverageStatus'];counts[status]=counts.get(status,0)+1
    body='<section class="participation-section"><h2>Current council consultations</h2><p>'+str(len(rows))+' local areas have a separately recorded project-level review. This is distinct from finding a consultation portal, standing procedure or committee list. A partial review or blocked source is not a finding of zero opportunities. Redland and Brisbane retain their earlier dated project reviews.</p><ul>'+''.join('<li>'+s.e(status)+': '+str(count)+'</li>' for status,count in sorted(counts.items()))+'</ul><p>Other council pages state that current-project enumeration remains unchecked. Future refreshes must revisit current lists, pagination, individual contribution tools, dates and collection notices, rather than treating a published project as an open invitation.</p><p>'+s.link(page,s.REPO+'/blob/main/data/council-project-audits.json','Council project research and source-access gaps')+'</p></section>'
    return body
