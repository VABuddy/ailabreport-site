from pathlib import Path
import re,json

def normalize_archive(site):
    site=Path(site);p=site/'blog/index.html';s=p.read_text(encoding='utf-8')
    def normalize(match):
        block=match.group(0).replace('<h3>','<h2>').replace('</h3>','</h2>')
        block=re.sub(r'<img[^>]*>',lambda m:m.group(0) if 'width=' in m.group(0) else m.group(0).replace('loading="lazy"','width="480" height="270" loading="lazy" decoding="async"'),block)
        for rec in json.loads((site/'blog/posts.json').read_text(encoding='utf-8-sig')):
            local='assets/editorial/'+rec['slug']+'.webp'
            if (site/local).is_file():block=block.replace('https://i.ytimg.com/vi/'+rec['youtube_id']+'/hqdefault.jpg','/'+local)
        return block
    if s.count('<!-- POSTS_START -->')!=1 or s.count('<!-- POSTS_END -->')!=1:raise ValueError('Archive generation markers invalid')
    rendered=re.sub(r'<!-- POSTS_START -->.*?<!-- POSTS_END -->',normalize,s,flags=re.S)
    if rendered!=s:p.write_text(rendered,encoding='utf-8')
