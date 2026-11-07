"""Import reviewed project records and council-specific audit evidence."""
from pathlib import Path
from datetime import date
import argparse,json,re

ROOT=Path(__file__).resolve().parents[1]

def check_text(value):
    text=json.dumps(value,ensure_ascii=False)
    assert chr(8212) not in text and not re.search(r'&(?:mdash|#8212|#x2014);',text,re.I),'Forbidden punctuation'

def normalize(row,record_ids):
    status=row.get('coverageStatus') or row.get('enumerationStatus') or row.get('reviewStatus') or 'partial-discovery'
    labels={'current-list-reviewed':'Current project list reviewed','complete-current-list':'Current project list reviewed','reviewed-visible-catalogue':'Visible project catalogue reviewed','portal-projects-enumerated':'Public project catalogue enumerated','project-level-audit':'Project details reviewed; scope remains partial','partial-discovery':'Partial discovery; current list incomplete'}
    labels.update({'partial-project-review':'Project sources reviewed; coverage remains partial','source-limited-project-review':'Source access limited; project review incomplete','partial-authority-review':'Special-area authority reviewed; coverage remains partial','scoped-project-review':'Project sources reviewed; scope recorded','authority-mapped':'Responsible authority identified'})
    summary=row.get('summary') or row.get('finding') or row.get('scope') or 'The named official sources were checked for actual contribution invitations. Coverage remains partial.'
    enumeration={re.sub(r'([a-z])([A-Z])',r'\1 \2',key).replace('_',' ').capitalize():value for key,value in row.get('enumeration',{}).items()}
    for key,label in [('catalogueEntries','Public project entries'),('detailPagesRead','Project detail pages read'),('currentListingEntries','Current listing entries'),('listedCount','Entries counted in this review'),('totalCurrentProjectsKnown','Current projects known'),('enumeratedProjectCount','Project entries enumerated'),('currentResponseProjects','Projects with current response routes')]:
        if row.get(key) is not None:enumeration[label]=row[key]
    sources=[]
    for v in row.get('sources',[])+row.get('additionalSources',[])+row.get('directoriesReviewed',[]):
        if isinstance(v,str):v={'url':v}
        url=v.get('url') or v.get('sourceUrl')
        if url and not any(s['url']==url for s in sources):
            sources.append({'url':url,'title':v.get('title') or v.get('label') or 'Official source reviewed','note':v.get('finding') or v.get('note') or '', 'access':v.get('access','not separately recorded')})
    if row.get('portalUrl') and not any(s['url']==row['portalUrl'] for s in sources):sources.insert(0,{'url':row['portalUrl'],'title':'Official participation source'})
    audit={'councilId':row['councilId'],'checked':row['checked'],'portalUrl':row.get('portalUrl'),'coverageStatus':labels.get(status,status.replace('-',' ').capitalize()),'summary':summary,'scope':row.get('scope') or 'Official public consultation pages and identified invitations. This is not a complete survey of every development application, procurement or third-party process affecting the area.','enumeration':enumeration,'findings':row.get('findings',[]),'gaps':row.get('gaps',[]),'closedExclusions':row.get('closedExclusions',[]),'sources':sources,'recordIds':record_ids}
    for key in ('sectionsReviewed','projects','otherLeads'):
        if row.get(key):audit[key]=row[key]
    if row.get('referrals'):audit['referrals']=row['referrals']
    return audit

def merge(paths):
    registry_path=ROOT/'data/registry.json';data=json.loads(registry_path.read_text(encoding='utf-8-sig'))
    councils={c['id']:c for c in json.loads((ROOT/'data/councils.json').read_text(encoding='utf8'))['councils']}
    records={r['id']:r for r in data['records']}
    audit_path=ROOT/'data/council-project-audits.json'
    projects=json.loads(audit_path.read_text(encoding='utf8')) if audit_path.exists() else {'scope':'Current project invitations, separately from committees, general source links and standing procedures.','audits':[]}
    audits={a['councilId']:a for a in projects['audits']}
    # Keep previously published empty archive URLs stable. New archives appear on first closure.
    data.setdefault('publishedCouncilArchives',sorted({r['councilId'] for r in data['records'] if r.get('councilId')}))
    for path in paths:
        staged=json.loads(Path(path).read_text(encoding='utf-8-sig'));check_text(staged)
        added=staged.get('records',[])
        for r in added:
            assert r['councilId'] in councils and r['councilId']!='qld-council-6250',r['id']
            assert r['participationLevel']=='council' and r['jurisdiction']==councils[r['councilId']]['jurisdiction']
            assert re.fullmatch('[a-z0-9-]+',r['id'])
            date.fromisoformat(r['checked'])
            if r['id'] in records:assert records[r['id']].get('councilId')==r['councilId']
            records[r['id']]=r
        for row in staged.get('projectAudits',[]):
            assert row['councilId'] in councils and row['councilId']!='qld-council-6250'
            declared=row.get('recordIds',row.get('stagedRecordIds',row.get('recordsAdded',[])))
            ids=list(dict.fromkeys([*declared,*[r['id'] for r in added if r['councilId']==row['councilId']]]))
            assert all(ident in records and records[ident]['councilId']==row['councilId'] for ident in ids)
            audits[row['councilId']]=normalize(row,ids)
    data['records']=list(records.values());check_text(data)
    projects['checked']=max(a['checked'] for a in audits.values());projects['audits']=sorted(audits.values(),key=lambda a:a['councilId'])
    registry_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    audit_path.write_text(json.dumps(projects,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'records':len(records),'projectAudits':len(audits)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('staging',nargs='+');merge(parser.parse_args().staging)
