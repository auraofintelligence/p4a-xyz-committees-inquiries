"""Import local-area identities from P4A without copying elections or maps."""
from pathlib import Path
from datetime import date
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',required=True)
parser.add_argument('--routes',required=True)
parser.add_argument('--revision',required=True)
parser.add_argument('--imported-on',required=True)
args=parser.parse_args()
date.fromisoformat(args.imported_on)
source=Path(args.source);raw=source.read_bytes()
data=json.loads(raw.decode('utf-8-sig'))
routes={r['id']:r['url'] for r in json.loads(Path(args.routes).read_text(encoding='utf-8-sig'))['places']}
destination=ROOT/'data/councils.json'
prior={r['id']:r for r in json.loads(destination.read_text(encoding='utf-8'))['councils']} if destination.exists() else {}
rows=[]
for p in data['places']:
 if p['kind']=='ward':continue
 assert p['kind'] in ('council','special-local-body','unincorporated-area')
 row={key:p[key] for key in ('id','name','slug','jurisdiction','kind','officialUrl')}
 row['p4aUrl']='https://p4a.xyz/'+routes[p['id']]
 row['directoryChecked']=data['checked']
 if p['id'] in prior and prior[p['id']].get('review'):row['review']=prior[p['id']]['review']
 rows.append(row)
result={'sourceRepository':'auraofintelligence/p4a-xyz-cinema','sourceRevision':args.revision,
 'sourcePath':'content/places/councils.json','sourceSha256':hashlib.sha256(raw).hexdigest(),
 'importedOn':args.imported_on,'directoryChecked':data['checked'],
 'limits':'These are existing P4A local-area identities and published official links. Importing them is not a new check of participation rules, current legal status or every council consultation. Wards are not duplicated as councils. Special bodies and unincorporated areas retain their separate kinds.',
 'councils':sorted(rows,key=lambda r:(r['jurisdiction'],r['name']))}
destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'localAreas':len(rows),'councils':sum(r['kind']=='council' for r in rows),'sourceRevision':args.revision}))
