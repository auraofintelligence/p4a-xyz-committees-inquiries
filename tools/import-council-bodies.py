"""Import council body audits, preserving identities, Redland and dated calls."""
from pathlib import Path
from datetime import date
import argparse,json,re
from council_bodies import CORRECTIONS,procedure_key
from build import source_key

ROOT=Path(__file__).resolve().parents[1]

def clean(value):
    if isinstance(value,str):return re.sub(r'\s+',' ',value.replace(chr(8212),'; ').replace(chr(65533),'')).strip()
    return value

def merge(paths):
    file=ROOT/'data/council-bodies.json'
    data=json.loads(file.read_text(encoding='utf8'))
    identities={c['id'] for c in json.loads((ROOT/'data/councils.json').read_text(encoding='utf8'))['councils']}
    prior={a['councilId']:a for a in data['audits']}
    for path in paths:
        staged=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        rows=staged if isinstance(staged,list) else staged.get('audits',staged.get('entries',staged.get('councils',[])))
        for row in rows:
            ident=row['councilId'];assert ident in identities,ident
            if ident=='qld-council-6250':continue
            date.fromisoformat(row['checked'])
            audit={k:clean(row[k]) for k in ('councilId','checked','sourceUrl','coverageStatus','reviewOutcome') if row.get(k)}
            audit['gaps']=[clean(v) for v in row.get('gaps',[])]
            audit['directories']=[]
            for entry in row.get('committeeDirectories',row.get('directories',[])):
                if entry.get('url') and entry['url']!=audit.get('sourceUrl'):
                    audit['directories'].append({'title':clean(entry.get('title','Official committee directory')),'url':clean(entry['url']),'access':clean(entry.get('verificationLevel',entry.get('access','unverified')))})
            for group,fields,title in [('committees',('name','url','purpose','kind','status','participation','verification'),'name'),('standingInvitations',('title','url','method','timing','eligibility','disclosure','verification'),'title')]:
                audit[group]=[];seen=set()
                for entry in row.get(group,[]):
                    item={k:clean(entry[k]) for k in fields if entry.get(k)}
                    assert item.get(title) and item.get('url','').startswith(('https://','http://')),(ident,entry)
                    if group=='standingInvitations' and source_key(item['url']) in {source_key(e['url']) for e in CORRECTIONS['excludeStanding']}:continue
                    key=(item[title].casefold(),item['url'])
                    if key in seen:continue
                    seen.add(key)
                    if group=='committees':
                        item.setdefault('participation','Public contribution or membership invitation not verified. Check this body’s current official rules.')
                    else:item.setdefault('method','Use the official participation guide; detailed conditions need confirmation.')
                    item.setdefault('verification','Official source checked; limits are recorded at council level.')
                    audit[group].append(item)
            merged={}
            for invitation in audit['standingInvitations']:
                key=procedure_key(source_key,ident,invitation['url'])
                equivalence=next((g for g in CORRECTIONS['equivalentProcedures'] if g['councilId']==ident and key==source_key(g['primaryUrl'])),None)
                if equivalence:
                    original={'title':invitation['title'],'url':invitation['url']}
                    invitation['title']=equivalence['title'];invitation['url']=equivalence['primaryUrl']
                    if original['url']!=invitation['url']:invitation['relatedSources']=[original]
                merge_key=key if equivalence else (invitation['title'].casefold(),key)
                if merge_key not in merged:merged[merge_key]=invitation
                else:
                    related=invitation.get('relatedSources',[])+[{'title':invitation['title'],'url':invitation['url']}]
                    for source in related:
                        if source['url']!=merged[merge_key]['url'] and source not in merged[merge_key].setdefault('relatedSources',[]):merged[merge_key]['relatedSources'].append(source)
            audit['standingInvitations']=list(merged.values())
            prior[ident]=audit
    data['audits']=sorted(prior.values(),key=lambda a:a['councilId'])
    file.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'auditedAreas':len(prior),'namedBodies':sum(len(a['committees']) for a in prior.values()),'standingInvitations':sum(len(a['standingInvitations']) for a in prior.values())}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('audits',nargs='+');merge(p.parse_args().audits)
