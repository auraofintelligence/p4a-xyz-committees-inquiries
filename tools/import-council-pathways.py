"""Merge dated official council pathway audits without changing detailed reviews."""
from pathlib import Path
from datetime import date
import argparse,json,re

ROOT=Path(__file__).resolve().parents[1]

def clean(value):
    if isinstance(value,str):
        return re.sub(r'\s+',' ',value.replace(chr(8212),'; ').replace(chr(65533),'' )).strip()
    if isinstance(value,list):return [clean(v) for v in value]
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    return value

def merge(paths):
    target=ROOT/'data/council-pathways.json'
    data=json.loads(target.read_text(encoding='utf8')) if target.exists() else {'scope':'Official council participation destinations, separate from detailed procedure reviews and dated invitations. A verified link is not a verified open call.','audits':[]}
    prior={a['councilId']:a for a in data['audits']}
    identities={c['id']:c for c in json.loads((ROOT/'data/councils.json').read_text(encoding='utf8'))['councils']}
    for path in paths:
        staged=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        for row in staged.get('entries',staged.get('councils',[])):
            ident=row.get('councilId') or row.get('id')
            assert ident in identities,ident
            if ident=='qld-council-6250':continue
            checked=row['checked'];date.fromisoformat(checked)
            routes=[];seen=set()
            for route in row.get('pathways',row.get('routes',[])):
                url=route.get('url')
                if not url or url in seen:continue
                assert url.startswith(('https://','http://')),(ident,url)
                seen.add(url)
                source=route.get('sourceUrl') or route.get('officialSourceUrl') or row.get('officialSourceUrl')
                assert source and source.startswith(('https://','http://')),(ident,source)
                access=route.get('access')
                if not access:
                    access='indexed-only' if route.get('status')=='indexed-only' else 'page-read' if route.get('status')=='verified' or route.get('targetStatus',route.get('destinationStatus'))==200 or 'read successfully' in route.get('verification','') else 'official-link-verified'
                item={'type':route.get('type','participation-information'),'title':route['title'],'url':url,'sourceUrl':source,'checked':route.get('checked',checked),'access':access,'verification':route.get('verification','The official source identifies this participation destination. Detailed conditions need their own review.')}
                for field in ('method','timing','eligibility','disclosure'):
                    if route.get(field) and not route[field].startswith(('Not established','Not fully reviewed','No deadline or speaking entitlement','The route is not a verified dated invitation','Publication, recording')):item[field]=route[field]
                routes.append(item)
            audit={'councilId':ident,'checked':checked,'status':row.get('status','pathways-verified' if routes else 'no-pathway-confirmed'),'sourceUrl':row.get('resolvedOfficialUrl') or row.get('councilWebsite') or row.get('officialSourceUrl') or identities[ident]['officialUrl'],'pathways':routes}
            if row.get('websiteDirectorySource'):audit['websiteDirectorySource']=row['websiteDirectorySource']
            gaps=row.get('accessGaps',row.get('gaps',[]))
            audit['limits']=[g for g in gaps if not any(term in g for term in ['complete list of current','every individual invitation','every speaking'])]
            prior[ident]=clean(audit)
    data['audits']=sorted(prior.values(),key=lambda x:x['councilId'])
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'auditedAreas':len(prior),'withPathways':sum(bool(a['pathways']) for a in prior.values()),'pathways':sum(len(a['pathways']) for a in prior.values())}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('audits',nargs='+');merge(parser.parse_args().audits)
