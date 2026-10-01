import json, hashlib, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
mp = root / 'evidence/chunk-manifest.json'
m = json.loads(mp.read_text(encoding='utf-8'))
lp = root / 'evidence/chunk-evidence.json'
ordinal = int(sys.argv[1])
c = m['chunks'][ordinal - 1]
ledger = json.loads(lp.read_text(encoding='utf-8')) if lp.exists() else dict(schema_version=1, manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(), source_sha256=m['source']['sha256'], entries=[])
assert len(ledger['entries']) == ordinal - 1
content = c['content']; raw = content.encode('utf-8')
assert hashlib.sha256(raw).hexdigest() == c['content_sha256']
spans=[]; offset=0
if c['locator'].get('atomic_kind'):
    spans=[dict(text=content,chunk_byte_start=0,chunk_byte_end=len(raw))]
else:
    for line in content.splitlines(keepends=True):
        n=len(line.encode('utf-8'))
        if line.strip(): spans.append(dict(text=line,chunk_byte_start=offset,chunk_byte_end=offset+n))
        offset += n
for s in spans: assert raw[s['chunk_byte_start']:s['chunk_byte_end']].decode('utf-8') == s['text']
ledger['entries'].append(dict(chunk_id=c['id'],ordinal=ordinal,chunk_sha256=c['content_sha256'],outcome='evidence',assertions=spans,constraints=[]))
lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
rp=root/'run.json'; run=json.loads(rp.read_text(encoding='utf-8'))
run['events'].append(dict(type='chunk_verified',chunk_id=c['id'],ordinal=ordinal,node='traverse'))
rp.write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f"Verified ordinal {ordinal}: {c['id']} ({len(spans)} exact extractive spans)")
