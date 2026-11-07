"""Merge dated official council pathway audits without changing detailed reviews."""
from pathlib import Path
from datetime import date
import argparse,json,re
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode

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
                if url:
                    parsed=urlsplit(url);url=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,urlencode([(k,v) for k,v in parse_qsl(parsed.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid','msclkid')]),parsed.fragment))
                if not url or url in seen:continue
                if route.get('type')=='petitions' and not re.search(r'\bpetition',route['title']+' '+urlsplit(url).path,re.I):continue
                assert url.startswith(('https://','http://')),(ident,url)
                seen.add(url)
                source=route.get('sourceUrl') or route.get('officialSourceUrl') or row.get('officialSourceUrl')
                assert source and source.startswith(('https://','http://')),(ident,source)
                access=route.get('verificationLevel') or route.get('access')
                if 'indexed' in route.get('status','').lower():access='indexed-only'
                if access:
                    access='indexed-only' if 'indexed' in access.lower() else 'page-read' if access in ('official-page-read','page-read','direct official page reviewed') or 'page text read' in access.lower() else 'official-link-verified' if 'link' in access.lower() else access
                if not access:
                    access='indexed-only' if 'indexed' in route.get('status','').lower() else 'page-read' if route.get('status')=='verified' or route.get('status','').startswith('route verified;') or route.get('targetStatus',route.get('destinationStatus'))==200 or 'read successfully' in route.get('verification','') else 'official-link-verified'
                if any(term in route.get('pageTitle','').lower() for term in ('one moment','just a moment','checking your browser','access denied')):access='official-link-verified'
                item={'type':route.get('type','participation-information'),'title':route.get('title') or ('Official consultation portal' if route.get('type')=='consultation' else 'Official participation route'),'url':url,'sourceUrl':source,'checked':route.get('checked',checked),'access':access,'verification':route.get('verification','The official source identifies this participation destination. Detailed conditions need their own review.')}
                item['type']={'meeting information':'meeting-information','public participation':'meeting-participation','authority feedback':'authority-feedback'}.get(item['type'],item['type'])
                if re.search(r'community reference groups?',item['title'],re.I):item['type']='community-reference'
                if item['verification'].startswith(('The official council website linked this page, and its page title','Official page text read. This is a continuing navigation route','The official council website directly links this participation destination. The linked page was read','Official council participation destination opened and read on')) and access=='page-read':item['verification']='Official participation page read. Individual project invitations and detailed procedures remain partial.'
                for field in ('method','timing','eligibility','disclosure'):
                    value=route.get(field,'')
                    if not value or value.startswith(('Not established','Not fully reviewed','No deadline or speaking entitlement','The route is not a verified dated invitation','This route is not a verified dated invitation','Publication, recording','Publication and recording conditions require','Publication, privacy and recording conditions require','Eligibility and restrictions vary by procedure')):continue
                    if any(term in value for term in ('not independently reviewed in this route-level check','not independently confirmed in this route-level check','not enumerated in this route-level check')):continue
                    item[field]=value
                routes.append(item)
            status='pathways-verified' if any(p['access']!='indexed-only' for p in routes) else 'indexed-pathways-only' if routes else 'non-council-area' if identities[ident]['kind']!='council' else 'no-pathway-confirmed'
            audit={'councilId':ident,'checked':checked,'status':status,'sourceUrl':row.get('resolvedOfficialSourceUrl') or row.get('resolvedOfficialUrl') or row.get('councilWebsite') or row.get('websiteUrl') or row.get('officialSourceUrl') or identities[ident]['officialUrl'],'pathways':routes}
            if row.get('websiteDirectorySource'):audit['websiteDirectorySource']=row['websiteDirectorySource']
            if row.get('officialContactDirectory'):audit['contactDirectory']=row['officialContactDirectory']
            gaps=row.get('accessGaps',row.get('gaps',[]))
            audit['limits']=[g for g in gaps if not any(term in g for term in ['complete list of current','every individual invitation','every speaking']) and not g.startswith(('This is a route-level audit.','The consultation gateway and selected participation sources were checked.','Official detail sources were recovered separately','No dedicated usable participation route was confirmed','Some destinations could not be read in full.'))]
            prior[ident]=clean(audit)
    data['audits']=sorted(prior.values(),key=lambda x:x['councilId'])
    data['defaultConditions']='Unless a pathway explicitly records a reviewed condition, timing, eligibility, publication, names and recording requirements remain unverified and must be checked in the current official invitation or procedure.'
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'auditedAreas':len(prior),'withPathways':sum(bool(a['pathways']) for a in prior.values()),'pathways':sum(len(a['pathways']) for a in prior.values())}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('audits',nargs='+');merge(parser.parse_args().audits)
