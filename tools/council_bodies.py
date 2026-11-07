"""Named local bodies and continuing invitations, separate from dated calls."""
from collections import Counter
from pathlib import Path
import json
import re

CORRECTIONS=json.loads((Path(__file__).resolve().parents[1]/'data/council-route-corrections.json').read_text(encoding='utf8'))

REVIEW_OUTCOMES={
    'current-directory':'Current published directory reviewed; other bodies may sit outside it.',
    'current-records-partial':'Published records reviewed; the current inventory remains partial.',
    'historical-only':'Historical records found; current operation remains unverified.',
    'indexed-only':'Indexed official material found; source details remain unverified.',
    'source-blocked':'Source access prevented a current inventory check.',
    'no-current-names':'No current named bodies confirmed in the sources checked.',
    'authority-mapped':'Responsible authority identified; ordinary council structures do not apply.'
}

def uncertain_body(entry):
    status=entry.get('status','').lower()
    return status.startswith('historical') or bool(re.search(r'unverified|unread|unconfirmed|not independently (?:read|confirmed)|proposed|being formed',status))

def procedure_key(source_key,council_id,url):
    key=source_key(url)
    for group in CORRECTIONS['equivalentProcedures']:
        if group['councilId']==council_id and key in {source_key(u) for u in [group['primaryUrl'],*group['aliases']]}:return source_key(group['primaryUrl'])
    return key

def extra_invitations(s,council,audit):
    covered={procedure_key(s.source_key,council['id'],m['sourceUrl']) for m in council.get('review',{}).get('mechanisms',[])}
    represented={(v['title'].casefold(),procedure_key(s.source_key,council['id'],v['url'])) for r in s.council_records(council['id']) for v in r.get('replacesStandingInvitations',[])}
    return [i for i in audit.get('standingInvitations',[]) if procedure_key(s.source_key,council['id'],i['url']) not in covered and (i['title'].casefold(),procedure_key(s.source_key,council['id'],i['url'])) not in represented]

def coverage_table(s,page):
    body='<div class="coverage-table-wrap"><table class="coverage-table"><caption>Council body inventories and additional standing methods; these are not open-call counts</caption><thead><tr><th>Location</th><th>Audited areas</th><th>Body entries</th><th>Uncertain or historical</th><th>Additional methods</th></tr></thead><tbody>'
    for j,name in s.NAMES.items():
        if j in ('federal','act'):continue
        councils=[c for c in s.COUNCILS if c['jurisdiction']==j]
        audits=[s.COUNCIL_BODIES[c['id']] for c in councils if c['id'] in s.COUNCIL_BODIES]
        bodies=[b for a in audits for b in a['committees']]
        extra=sum(len(extra_invitations(s,c,s.COUNCIL_BODIES[c['id']])) for c in councils if c['id'] in s.COUNCIL_BODIES)
        values=[len(audits),len(bodies),sum(uncertain_body(b) for b in bodies),extra]
        body+='<tr><th scope="row">'+s.link(page,'councils/'+j+'/',name)+'</th>'+''.join('<td>'+str(v)+'</td>' for v in values)+'</tr>'
    body+='</tbody></table></div><p>Standing methods already covered by a detailed procedure review appear once on that council’s page. Redland retains its separate existing committee research. Uncertain and historical entries remain visible with labels; current operation and public speaking rights are not assumed.</p>'
    outcomes=Counter(a.get('reviewOutcome') for a in s.COUNCIL_BODIES.values() if a.get('reviewOutcome'))
    if outcomes:
        body+='<details class="participation-method"><summary>Follow-up research depth: '+str(sum(outcomes.values()))+' local areas</summary><ul>'+''.join('<li>'+str(outcomes[k])+': '+s.e(label)+'</li>' for k,label in REVIEW_OUTCOMES.items() if outcomes[k])+'</ul><p>A nonempty list is not a complete council inventory. Other profiles retain the limits of their earlier source check.</p></details>'
    return body

def render(s,page,council):
    audit=s.COUNCIL_BODIES.get(council['id'])
    if not audit:return ''
    bodies=audit.get('committees',[])
    invites=extra_invitations(s,council,audit)
    body='<section id="council-committees" class="council-pathways"><h2>Committees and advisory bodies</h2>'
    body+='<p>Sources checked '+s.pretty_date(audit['checked'])+'. Lists may be partial; current membership and participation rights require explicit confirmation.</p>'
    if any(uncertain_body(b) for b in bodies):body+='<p>Uncertain entries need current confirmation.</p>'
    if audit.get('reviewOutcome') in REVIEW_OUTCOMES:body+='<p class="status-strip">'+s.e(REVIEW_OUTCOMES[audit['reviewOutcome']])+'</p>'
    if bodies:
        shared_urls={url for url,count in Counter(b['url'] for b in bodies).items() if count>=2}
        body+='<form class="directory-search" data-council-body-search hidden><label>Find a committee or advisory body<input type="search" name="search" autocomplete="off" placeholder="Type a name or subject"></label><button type="reset">Clear</button></form><p data-body-count aria-live="polite">'+str(len(bodies))+' body entries recorded; inventory may be incomplete.</p>'
        groups={}
        for entry in bodies:
            groups.setdefault(entry['url'] if entry['url'] in shared_urls else None,[]).append(entry)
        for shared_url,entries in groups.items():
            body+='<div data-body-group>'
            if shared_url:body+='<p>'+s.link(page,shared_url,'Official listing referenced for the following bodies')+'</p>'
            common={text for text,count in Counter(b['participation'] for b in entries).items() if count==len(entries) and count>=2}
            for text in sorted(common):
                displayed='Council lists these bodies. Observation and applications to address Council are separate routes. A right to address a committee has not been verified.' if text.startswith('Council lists this body.') else text
                body+='<p class="notice">'+s.e(displayed)+'</p>'
            repeated={key:{text for text,count in Counter(b.get(key,'') for b in entries).items() if text and text not in ('unverified','historical-source') and count==len(entries) and count>=2} for key in ('purpose','status')}
            for key in ('purpose','status'):
                for text in sorted(repeated[key]):
                    if text!='listed':body+='<p>'+s.e(text)+'</p>'
            body+='<ul class="council-pathway-list">'
            for entry in entries:
                body+='<li data-council-body><h3>'+(s.e(entry['name']) if shared_url else s.link(page,entry['url'],entry['name']))+'</h3>'
                if uncertain_body(entry):body+='<p><span class="status-badge status-unverified">Uncertain</span>'+(' Historical source.' if entry.get('status','').startswith('historical') else '')+'</p>'
                kind=entry.get('kind','').replace('-',' ')
                if kind and not all(word in entry['name'].lower() for word in kind.lower().split()):body+='<p class="eyebrow">'+s.e(kind)+'</p>'
                if entry.get('purpose') and entry['purpose'] not in repeated['purpose']:body+='<p>'+s.e(entry['purpose'])+'</p>'
                if entry['participation'] not in common:body+='<p><strong>Taking part:</strong> '+s.e(entry['participation'])+'</p>'
                if entry.get('status') and entry['status'] not in ('listed','unverified','historical-source') and entry['status'] not in repeated['status']:body+='<p>'+s.e(entry['status'])+'</p>'
                body+='</li>'
            body+='</ul></div>'
    else:body+='<p class="notice">No named committee inventory was confirmed in this check. This is a coverage gap, not a finding that the council has no committees.</p>'
    if audit.get('sourceUrl') and (not bodies or s.source_key(audit['sourceUrl']) not in {s.source_key(u) for u in shared_urls}):body+='<p>'+s.link(page,audit['sourceUrl'],'Official committee or governance source')+'</p>'
    for directory in audit.get('directories',[]):
        body+='<p>'+s.link(page,directory['url'],directory['title'])+(' · destination details unverified' if directory.get('access') not in ('official-page-read','page-read','direct-read','directly-reviewed') else '')+'</p>'
    redundant={'This is an incomplete catalogue. Current membership, every working group, recruitment windows and body-specific public participation rights have not been exhaustively checked.'}
    if not bodies:redundant.update({'No current named committee inventory was verified in the official pages available during this pass. This does not mean that the council has no committees.','No current named-body inventory was verified in the accessible official sources. This does not establish that the council has no committees.'})
    gaps=[note for note in audit.get('gaps',[]) if note not in redundant]
    if gaps:body+='<details class="participation-method"><summary>Committee coverage and access limits</summary><ul>'+''.join('<li>'+s.e(note)+'</li>' for note in gaps)+'</ul></details>'
    body+='</section>'
    if invites:
        body+='<section id="standing-invitations" class="council-pathways"><h2>Standing invitations to take part</h2><p>Timing, eligibility and publication rules remain unverified unless shown below. A committee listing does not by itself invite public contributions.</p><ul class="council-pathway-list">'
        for entry in invites:
            body+='<li data-standing-invitation><h3>'+s.link(page,entry['url'],entry['title'])+'</h3><p>'+s.e(entry['method'])+'</p>'
            for key,label in [('timing','When'),('eligibility','Who can take part'),('disclosure','What may become public')]:
                if entry.get(key):body+='<p><strong>'+label+':</strong> '+s.e(entry[key])+'</p>'
            for source in entry.get('relatedSources',[]):body+='<p>'+s.link(page,source['url'],source['title'])+'</p>'
            body+='</li>'
        body+='</ul></section>'
    return body
