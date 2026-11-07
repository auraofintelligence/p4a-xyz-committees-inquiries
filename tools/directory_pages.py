"""Separate public-body directories, with participation kept on its own path."""

def chooser(s,page,title,description,items):
 body=s.hero(title,description,cls='directory-hero')
 body+='<div class="route-grid">'+''.join('<a class="route-card feature-panel" href="'+s.e(s.rel(page,url))+'"><h2>'+s.e(name)+'</h2><p>'+s.e(note)+'</p></a>' for url,name,note in items)+'</div>'
 s.write(page,title,body)

def parliament_chooser(s,view):
 page=view+'/index.html'
 title='Find an inquiry.' if view=='inquiries' else 'Find a committee.'
 description='Choose one parliament to see its inquiries, submissions and other participation routes.' if view=='inquiries' else 'Choose one parliament to browse its committee directory.'
 body=s.hero(title,description,cls='directory-hero')
 body+='<div class="parliament-grid">'
 for j in ['federal','qld','nsw','vic','wa','sa','tas','act','nt']:
  name='Australian' if j=='federal' else s.NAMES[j]
  count=sum(c['jurisdiction']==j for c in s.COMMITTEES) if view=='committees' else sum(r['jurisdiction']==j and r['participationLevel'] in ('state','federal') and r['status']!='closed' for r in s.RECORDS)
  note=str(count)+(' committee directory entries' if view=='committees' else ' current participation records')
  if j=='vic' and view=='committees':note='Parliament has expired; official past committees linked'
  body+='<a class="parliament-choice'+(' is-federal' if j=='federal' else '')+'" href="'+s.e(s.rel(page,s.browse_route(view,j)))+'"><h2>'+s.e(name)+'</h2><p>'+s.e(note)+'</p><span aria-hidden="true">›</span></a>'
 body+='</div><p class="prose">'+('A committee listing does not mean submissions are open.' if view=='committees' else 'Every current record is visible in its chosen jurisdiction, including clearly tagged uncertainty.')+' '+s.link(page,'homelands/','For Minjerribah: Redland, Queensland and Australian committees and inquiries')+'.</p>'
 s.write(page,title,body)

def homelands(s):
 page='homelands/index.html'
 body=s.hero('Committees affecting home.','P4A’s founder and designer lives on North Stradbroke Island / Minjerribah. These are the local, state and Australian bodies whose committees and inquiries can bind or influence his life.',cls='directory-hero')
 body+='<p class="prose">Choose one level below. Its committees and participation opportunities stay in their own view.</p><div class="homelands-path">'
 for j,label,note in [('redland','Redland City','Local council committees and participation affecting Minjerribah and the wider Redland area.'),('qld','Queensland','Queensland Parliament’s committees, inquiries and state participation routes.'),('federal','Australian','Federal parliamentary committees, inquiries and public submissions.')]:
  body+='<article class="homelands-body feature-panel"><h2>'+s.e(label)+'</h2><p>'+s.e(note)+'</p><div class="button-row">'+s.link(page,s.browse_route('inquiries',j),'Inquiries & participation','button button-secondary')+s.link(page,s.browse_route('committees',j),'All committees','button button-secondary')+'</div></article>'
 body+='</div><p class="prose">For other Australian jurisdictions, use the parliament selector in this committees and inquiries menu.</p>'
 s.write(page,'Homelands committees and inquiries',body)

def redland_committees(s):
 page='committees/redland/index.html';data=s.REDLAND_COMMITTEES
 body=s.hero('Redland committees.','Council committees and working-group listings relevant to Minjerribah and Redland City. Listing, current operation and a public invitation are separate facts.',cls='directory-hero')
 body+='<p class="notice">'+s.e(data['note'])+'</p><div class="homelands-path">'
 for entry in data['entries']:
  if 'not a committee' in entry['kind']:continue
  body+='<article class="homelands-body feature-panel"><p class="eyebrow">'+s.e(entry['status'])+'</p><h2>'+s.e(entry['name'])+'</h2><p>'+s.e(entry['purpose'])+'</p><p><strong>Participation:</strong> '+s.e(entry['participation'])+'</p><p><strong>Uncertainty:</strong> '+s.e(entry['uncertainty'])+'</p><details class="participation-method"><summary>Sources and verification</summary><p>'+s.e(entry['verification'])+'</p><p>'+s.link(page,entry['sourceUrl'],'Official committee source')+'</p>'
  for source in entry.get('relatedSources',[]):body+='<p>'+s.link(page,source['url'],source['label'])+'<br>'+s.e(source['note'])+'</p>'
  body+='<p>Checked '+s.pretty_date(entry['checked'])+'.</p></details></article>'
 body+='</div><h2>Related arrangements</h2>'
 for entry in data['entries']:
  if 'not a committee' not in entry['kind']:continue
  body+='<details class="participation-method"><summary>'+s.e(entry['name'])+'</summary><p><strong>'+s.e(entry['kind'])+'.</strong> '+s.e(entry['purpose'])+'</p><p>'+s.e(entry['verification'])+' '+s.e(entry['uncertainty'])+'</p><p>'+s.link(page,entry['sourceUrl'],'Official agreement listing')+'</p></details>'
 body+='<div class="prose"><h2>Council meeting participation</h2><p>General Meetings have their own public-address, deputation and petition rules. They are not committee inquiry hearings. '+s.link(page,'councils/qld/redland/','See Redland participation and current local invitations')+'.</p></div><details class="participation-method"><summary>Coverage and access limits</summary><ul>'+''.join('<li>'+s.e(gap)+'</li>' for gap in data['gaps'])+'</ul><p>'+s.link(page,data['sourceUrl'],'Official committees and working groups directory')+'</p></details>'
 s.write(page,'Redland committees',body)

def searchable_list(s,page,label,rows,kind):
 total=len(rows)
 controls='<form class="directory-search" id="directory-search" data-directory-search hidden><label>Find '+s.e(label)+'<input type="search" name="search" placeholder="Type a name, subject or participation route" autocomplete="off"></label><label>Sort<select name="sort"><option value="name">A to Z</option><option value="participation">Participation recorded first</option><option value="priority">P4A matched invitations first</option></select></label><button type="reset">Clear</button></form><p data-directory-count aria-live="polite">'+str(total)+' '+s.e(label)+'.</p>'
 items=[]
 for row in rows:
  if kind=='council':
   url=s.council_route(row);review=row.get('review');records=s.council_records(row['id'])
   count=len([r for r in records if r['status'] in ('open','upcoming','ongoing')])
   status='Participation rules checked '+s.pretty_date(review['checked']) if review else 'Participation sources not yet checked'
   if row['id']=='qld-council-6250':status='Minjerribah and Redland participation path'
   type_label={'council':'Council','special-local-body':'Special local body','unincorporated-area':'Unincorporated area'}[row['kind']]
   note=type_label+' · '+status
   search=row['name']+' '+type_label+' '+(' '.join(m['title']+' '+m['type']+' '+m['method'] for m in review['mechanisms']) if review else '')
  else:
   url=s.committee_route(row);records=s.committee_records(row)
   count=len([r for r in records if r['status'] in ('open','upcoming','ongoing')])
   note=(row.get('house') or row.get('administeringHouse') or '')+' · '+(row.get('type') or 'Committee')
   search=' '.join([row['name'],row.get('purpose',''),note]+[i.get('title','') for i in row.get('inquiries',[])]+[r['title']+' '+r['kind'] for r in records if r['status']!='closed'])
  uncertain=sum(r['status']=='unverified' for r in records)
  search+=' '+' '.join(' '.join([r['title'],r['purpose'],r['method']]+[s.TOPICS[k] for k in s.topic_keys(r)]+[c['reason'] for c in r.get('connections',[])]) for r in records if r['status']!='closed')
  priority=max((r.get('priority',0) for r in records if r['status'] in ('open','upcoming','ongoing')),default=0)
  action=str(count)+' participation record'+('s' if count!=1 else '') if count else str(uncertain)+' participation record'+('s' if uncertain!=1 else '')+' to confirm' if uncertain else str(len(review['mechanisms']))+' checked participation procedures' if kind=='council' and review else 'Participation not yet checked' if kind=='council' else 'No current invitation recorded'
  items.append('<li class="body-directory-row" data-directory-row data-name="'+s.e(row['name'].lower())+'" data-search="'+s.e(search.lower())+'" data-participation="'+str(count)+'" data-priority="'+str(priority)+'"><div><h2>'+s.link(page,url,row['name'])+'</h2><p>'+s.e(note)+'</p></div><div><span class="directory-status">'+s.e(action)+'</span>'+s.link(page,url,'Open '+('local area' if kind=='council' and row['kind']!='council' else kind),'text-link')+'</div></li>')
 return controls+'<ul class="body-directory">'+''.join(items)+'</ul><p data-directory-empty class="notice" hidden>No matching '+s.e(label)+'. Try fewer words.</p>'

def build_directories(s):
 homelands(s)
 redland_committees(s)
 parliament_chooser(s,'inquiries')
 parliament_chooser(s,'committees')
 jurisdictions=[j for j in s.NAMES if j!='federal']
 items=[]
 for j in jurisdictions:
  rows=[r for r in s.COUNCILS if r['jurisdiction']==j]
  count=sum(r['kind']=='council' for r in rows)
  note=str(count)+' existing P4A council profiles' if j!='act' else 'Territory government performs local government functions; no separate local council.'
  items.append(('councils/'+j+'/',s.NAMES[j],note))
 chooser(s,'councils/index.html','Find your council.','Choose a state or territory, then a council. Participation records and archives stay with the selected council.',items)
 for j in jurisdictions:
  page='councils/'+j+'/index.html';rows=[r for r in s.COUNCILS if r['jurisdiction']==j]
  body=s.hero(s.NAMES[j]+' councils.','Search the existing P4A local-area directory, then open one council to see its checked participation routes.',cls='directory-hero')
  body+='<p class="notice">Council identities and published official links come from P4A’s existing directory. A directory entry is not a verified open consultation. Each profile says whether participation sources have been checked. Special local bodies and unincorporated areas are labelled separately.</p>'
  if j=='act':body+='<p class="notice">The ACT has no separate elected local councils. The Assembly and ACT Government perform territory and local functions. '+s.link(page,'states/act/','ACT participation')+' · '+s.link(page,'https://www.parliament.act.gov.au/visit-and-learn/learn/resources/fs/levels-of-gov','Official explanation')+'.</p>'
  body+=searchable_list(s,page,'local areas in '+s.NAMES[j],rows,'council')
  body+='<p>'+s.link(page,'councils/','Choose another state or territory')+'</p>'
  s.write(page,s.NAMES[j]+' councils',body)
 for council in s.COUNCILS:
  if council['id']=='qld-council-6250':continue
  route=s.council_route(council);page=route+'index.html';review=council.get('review');records=s.council_records(council['id'])
  body=s.hero(council['name']+'.','Participation in this local area, with each route’s own rules and source limits.',s.NAMES[council['jurisdiction']]+' · local participation',cls='directory-hero')
  body+='<p>'+s.link(page,'councils/'+council['jurisdiction']+'/','Choose another local area in '+s.NAMES[council['jurisdiction']])+'</p>'
  if council['kind']!='council':body+='<p class="notice">This is an '+('unincorporated area' if council['kind']=='unincorporated-area' else 'area with a special local body')+'. It is not presented as an ordinary elected council. Use the official source to identify the responsible authority.</p>'
  if review:
   body+='<p class="prose">'+s.e(review['summary'])+'</p><p class="status-strip">Participation sources checked '+s.pretty_date(review['checked'])+'.</p>'
   if review.get('consultationUrl'):body+='<p>'+s.link(page,review['consultationUrl'],'Official consultation portal','button button-secondary')+'</p><p class="prose">'+s.e(review['consultationNote'])+'</p>'
   current=[r for r in records if r['status']!='closed']
   body+=s.section('Current invitations','Participation and uncertainty labels describe the checked invitation, not the council’s general activity.',s.filters(page,current,scope_label=council['name'])) if current else '<p class="notice">No dated invitation has been verified for this council in this review. Use its official portal for other projects. The standing procedures below may still provide a way to take part.</p>'
   body+='<section class="participation-section"><h2>Ways to take part</h2><p class="prose">These are standing procedures, each with its own eligibility, approval and publication rules.</p>'
   for m in review['mechanisms']:
    body+='<details class="participation-method"><summary>'+s.e(m['title'])+'</summary><dl class="fact-list">'+''.join('<dt>'+s.e(label)+'</dt><dd>'+s.e(m[key])+'</dd>' for label,key in [('How it works','method'),('Timing and limits','timing'),('Eligibility','eligibility'),('What may become public','disclosure'),('What was checked','verification')])+'</dl>'
    if m.get('sourceUrl'):body+='<p>'+s.link(page,m['sourceUrl'],'Official procedure')+'</p>'
    body+='</details>'
   body+='</section>'
   if review['gaps']:body+='<aside class="notice"><strong>Coverage and access limits</strong><ul>'+''.join('<li>'+s.e(gap)+'</li>' for gap in review['gaps'])+'</ul></aside>'
  else:
   body+='<p class="notice"><strong>Participation sources not yet checked.</strong> This council or local area is included so you can find it. Current consultations, petition rules, public questions and speaking procedures have not been verified here. This does not mean no opportunities exist.</p>'
  body+='<div class="button-row">'+s.link(page,council['officialUrl'],'Published official source','button button-secondary')+s.link(page,council['p4aUrl'],'Existing P4A place context','button button-secondary')+'</div><p class="prose">Directory source checked '+s.pretty_date(council['directoryChecked'])+'. Importing its name and links does not refresh that source date.</p>'
  if records:
   body+=s.archive_link(page,route,council['name'])
   closed=[r for r in records if r['status']=='closed'];archive='archive/'+route+'index.html'
   archive_body=s.hero(council['name']+' archive.','Closed participation rounds for this council only.',cls='archive-hero')+'<p>'+s.link(archive,route,'Return to current '+council['name']+' participation')+'</p>'
   archive_body+=s.filters(archive,closed,scope_label=council['name']) if closed else '<p class="notice">There are no closed records in this council’s archive yet.</p>'
   s.write(archive,council['name']+' archive',archive_body)
  s.write(page,council['name']+' participation',body)
 for j,name in s.NAMES.items():
  page='committees/'+j+'/index.html';committees=[c for c in s.COMMITTEES if c['jurisdiction']==j]
  body=s.hero(('Australian' if j=='federal' else name)+' committees.','Browse all committee entries from this parliament’s reviewed official directory, separately from invitations to participate.',cls='directory-hero')
  audit=next((a for a in s.COMMITTEE_DATA.get('directories',[]) if a['jurisdiction']==j),{})
  body+='<p class="notice">'+s.e(audit.get('note','Directory review is still incomplete; no complete coverage claim is made.'))
  if audit.get('sourceUrl'):body+=' '+s.link(page,audit['sourceUrl'],'Official committee directory')
  if audit.get('archiveUrl'):body+=' · '+s.link(page,audit['archiveUrl'],'Official past committees and inquiries')
  body+='</p>'
  body+=searchable_list(s,page,'committees in '+('Australia' if j=='federal' else name),committees,'committee') if committees else '<p class="notice">'+('Victorian committees ceased when Parliament expired on 3 November 2026. Earlier committees remain in the official archive.' if j=='vic' else 'Committee directory entries have not been fully verified for this parliament yet.')+'</p>'
  s.write(page,name+' committees',body)
 for committee in s.COMMITTEES:
  page=s.committee_route(committee)+'index.html';j=committee['jurisdiction'];records=s.committee_records(committee)
  body=s.hero(committee['name']+'.',committee.get('purpose') or 'A committee entry in this parliament’s official directory. Use the official source for its remit and powers.',s.NAMES[j]+' · committee',cls='directory-hero')
  body+='<dl class="fact-list">'+''.join('<dt>'+s.e(label)+'</dt><dd>'+s.e(value)+'</dd>' for label,value in [('House / administering house',committee.get('house') or committee.get('administeringHouse') or 'Not confirmed'),('Committee type',committee.get('type') or 'Not confirmed'),('Directory / activity status',committee.get('status') or 'Listed in the reviewed directory; current operation not independently confirmed'),('What was checked',committee.get('verification') or 'Name and official link from the parliamentary directory. Listing is not a public invitation.'),('Checked',s.pretty_date(committee['checked']))])+'</dl>'
  if committee.get('houseNote'):body+='<p class="prose">'+s.e(committee['houseNote'])+'</p>'
  if committee.get('currentName') and committee['currentName']!=committee['name']:body+='<p class="notice">The directory lists this body as '+s.e(committee['name'])+'. Its separately verified current name is '+s.e(committee['currentName'])+'. The source naming difference is retained.</p>'
  if committee.get('pairNote'):body+='<p class="prose">'+s.e(committee['pairNote'])+'</p>'
  body+='<p>'+s.link(page,committee['sourceUrl'],'Official committee page','button button-secondary')+'</p>'
  current=[r for r in records if r['status']!='closed']
  if current:body+=s.section('Participation recorded here','Use the invitation’s own method and restrictions.',s.filters(page,current,scope_label=committee['name']))
  else:body+='<p class="notice">No current public participation invitation is recorded for this committee in our checked data. This is not proof that none exists. Use the committee’s official inquiry list.</p>'
  inquiries=committee.get('inquiries',[])
  if inquiries:
   body+='<section class="participation-section"><h2>Inquiry and review links</h2><p class="prose">An inquiry can continue after submissions close. These source links keep the inquiry’s activity separate from permission to contribute.</p><ul class="inquiry-source-list">'
   for inquiry in inquiries:
    body+='<li>'+s.link(page,inquiry['sourceUrl'],inquiry['title'])+'<p>'+s.e(inquiry.get('statusReason') or inquiry.get('status') or 'Participation status not independently confirmed.')+'</p></li>'
   body+='</ul></section>'
  body+='<p>'+s.link(page,'committees/'+j+'/','All '+('Australian' if j=='federal' else s.NAMES[j])+' committees')+'</p>'
  s.write(page,committee['name'],body)
