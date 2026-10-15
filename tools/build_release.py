#!/usr/bin/env python3
"""Offline public artifact builder. Never commits, pushes, or deploys.
Run after each approved generator publication to refresh discovery files.
Output must be a NEW directory; existing trees are never deleted/overwritten.
"""
from pathlib import Path
import argparse, json, re, shutil, datetime, sys, xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
from refresh_featured import refresh
from normalize_archive import normalize_archive
from html.parser import HTMLParser

class Meta(HTMLParser):
    def __init__(self): super().__init__(); self.canon=[]; self.noindex=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='link' and a.get('rel')=='canonical': self.canon.append(a.get('href'))
        if tag=='meta' and a.get('name','').lower()=='robots' and 'noindex' in a.get('content','').lower(): self.noindex=True

def build(site, output=None, preview=False, as_of=None):
    site=Path(site).resolve()
    cfg=json.loads((site/'tools/public-release.json').read_text(encoding='utf-8'))
    # Refresh only from the approved public ledger; no API or generator publication.
    feature=refresh(site,as_of or datetime.date.today())
    normalize_archive(site)
    manifest=json.loads((site/cfg['manifest']).read_text(encoding='utf-8-sig'))
    slugs=[p['slug'] for p in manifest]
    if len(slugs)!=len(set(slugs)) or not slugs: raise ValueError('Invalid/duplicate manifest')
    if any(not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',s) for s in slugs): raise ValueError('Unsafe slug')
    articles=['blog/posts/'+s+'.html' for s in slugs]
    pages=cfg['approved_pages']+articles
    origin=cfg['origin']
    urls=[]
    for rel in pages:
        s=(site/rel).read_text(encoding='utf-8-sig')
        meta=Meta();meta.feed(s)
        url=origin+('/' if rel=='index.html' else '/'+rel[:-10] if rel.endswith('/index.html') else '/'+rel)
        if meta.canon!=[url] or meta.noindex or '{{' in s: raise ValueError('Unapproved metadata: '+rel)
        urls.append(url)
    xml=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for url in urls: ET.SubElement(ET.SubElement(xml,'url'),'loc').text=url
    ET.indent(xml)
    sitemap=ET.tostring(xml,encoding='utf-8',xml_declaration=True)+b'\n'
    robots=('User-agent: *\nAllow: /\n\nSitemap: '+origin+'/sitemap.xml\n').encode('utf-8')
    # Validate every source first, then write generated discovery files.
    files=pages+cfg['legacy_pages']+cfg['redirects']+cfg['assets']+[cfg['manifest'],'CNAME']
    files=list(dict.fromkeys(files))
    # Legacy Pages builds the repository root. Reject any exposed file outside
    # the reviewed allowlist, even though this offline copier would omit it.
    exclusions=[line.strip()[2:] for line in (site/'_config.yml').read_text().splitlines() if line.strip().startswith('- ')]
    projected={p.relative_to(site).as_posix() for p in site.rglob('*') if p.is_file() and not p.relative_to(site).parts[0].startswith(('_','.')) and p.relative_to(site).parts[0] not in exclusions}
    unknown=projected-set(files)-{'sitemap.xml','robots.txt'}
    if unknown:raise ValueError('Unapproved files would be exposed by legacy Pages: '+', '.join(sorted(unknown)))
    for rel in files:
        p=(site/rel).resolve()
        if not p.is_relative_to(site) or not p.is_file(): raise ValueError('Missing/unsafe source: '+rel)
    if output:
        output=Path(output).resolve()
        if output.exists() or output.is_relative_to(site): raise ValueError('Output must be new and outside source')
    (site/'sitemap.xml').write_bytes(sitemap);(site/'robots.txt').write_bytes(robots)
    if output:
        output.mkdir(parents=True)
        for rel in files:
            src=site/rel; dest=output/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            if preview and src.suffix=='.html':
                try: s=src.read_text(encoding='utf-8-sig')
                except UnicodeDecodeError: s=src.read_bytes().decode('utf-8',errors='replace')
                s=re.sub(r'<!-- (?:GOOGLE ANALYTICS|={5,}).*?<script[^>]*(?:googletagmanager|/assets/analytics[.]js).*?</script>\s*<script>.*?</script>','',s,flags=re.S)
                if 'googletagmanager' in s or "gtag('config'" in s: raise ValueError('Preview contains analytics: '+rel)
                s=s.replace('</head>','<meta name="robots" content="noindex,nofollow">\n</head>')
                dest.write_text(s,encoding='utf-8')
            else: shutil.copyfile(src,dest)
        (output/'sitemap.xml').write_bytes(sitemap);(output/'robots.txt').write_bytes(b'User-agent: *\nDisallow: /\n' if preview else robots)
        # Artifact is already built; bypass a second Jekyll processing pass.
        (output/'.nojekyll').write_text('',encoding='utf-8')
    return {'canonical_urls':len(urls),'public_source_files':len(files),'preview':preview,'featured':feature}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--site',type=Path,default=Path(__file__).resolve().parents[1]);a.add_argument('--output',type=Path);a.add_argument('--preview',action='store_true');a.add_argument('--as-of',type=datetime.date.fromisoformat);args=a.parse_args()
    if args.preview and not args.output: a.error('--preview requires --output')
    print(json.dumps(build(args.site,args.output,args.preview,args.as_of),indent=2))
