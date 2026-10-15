#!/usr/bin/env python3
"""Build-time featured episode refresh from a reviewed public-content ledger.
Offline, no API spend, no Git actions. Never reads drafts or generator queues.
Use after an approved publication updates the manifest AND publication ledger.
"""
from pathlib import Path
import argparse,datetime,json,re,html,hashlib,tempfile,os
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def select_feature(site,ledger,as_of):
    posts=json.loads((site/'blog/posts.json').read_text(encoding='utf-8-sig'))
    if len({p['slug'] for p in posts})!=len(posts):raise ValueError('Duplicate manifest slug')
    entries=ledger.get('entries',[])
    if len({e['slug'] for e in entries})!=len(entries):raise ValueError('Duplicate publication approval')
    if len({e['youtube_id'] for e in entries})!=len(entries):raise ValueError('Duplicate approved episode ID')
    byslug={p['slug']:p for p in posts};eligible=[];excluded=[]
    for entry in entries:
        slug=entry['slug'];reason=None;video_only=entry.get('article_slug','default') is None;post=byslug.get(slug)
        if video_only:post={'slug':slug,'title':entry.get('episode_title',''),'youtube_id':entry.get('youtube_id',''),'video_only':True}
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):raise ValueError('Unsafe approved slug')
        if not post:reason='not in authoritative manifest'
        elif entry.get('approval_status')!='approved':reason='not approved'
        elif entry.get('publication_status')!='public' or entry.get('public_verified') is not True:reason='not verified public'
        elif entry.get('episode_format')!='long-form':reason='not confirmed long-form'
        elif entry.get('youtube_id')!=post['youtube_id'] or not re.fullmatch(r'[A-Za-z0-9_-]{11}',post['youtube_id']):reason='episode identity mismatch'
        if reason:excluded.append({'slug':slug,'reason':reason});continue
        try:date=datetime.date.fromisoformat(entry['public_episode_date'])
        except (ValueError,KeyError):excluded.append({'slug':slug,'reason':'missing/invalid episode publication date'});continue
        if date>as_of:excluded.append({'slug':slug,'reason':'future publication date'});continue
        if video_only:
            if not post['title'] or len(post['title'])>160 or not re.fullmatch(r'[a-f0-9]{64}',entry.get('content_approval_sha256','')) or not entry.get('evidence',{}).get('approved_site_release'):
                excluded.append({'slug':slug,'reason':'episode-only approval metadata missing'});continue
            eligible.append((date,slug,post,entry));continue
        article=site/'blog/posts'/(slug+'.html')
        if not article.is_file():excluded.append({'slug':slug,'reason':'article missing'});continue
        s=article.read_bytes().decode('utf-8',errors='replace')
        canonical='https://theailabreport.com/blog/posts/'+slug+'.html'
        if sha(article)!=entry.get('article_sha256'):excluded.append({'slug':slug,'reason':'article approval hash mismatch'});continue
        canonicals=re.findall(r'<link\s+[^>]*rel=[\"\']canonical[\"\'][^>]*href=[\"\']([^\"\']+)[\"\'][^>]*>',s,re.I)
        if canonicals!=[canonical] or re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex',s,re.I) or '{{' in s:
            excluded.append({'slug':slug,'reason':'article metadata not public-ready'});continue
        if not entry.get('evidence') or not entry['evidence'].get('approved_site_release'):
            excluded.append({'slug':slug,'reason':'approval provenance missing'});continue
        eligible.append((date,slug,post,entry))
    if not eligible:raise ValueError('No approved verified public long-form episode; refusing to overwrite homepage')
    eligible.sort(key=lambda x:(x[0],x[1]),reverse=True)
    newest=[row for row in eligible if row[0]==eligible[0][0]]
    if len(newest)>1:
        timed=[]
        for row in newest:
            try:
                stamp=datetime.datetime.fromisoformat(row[3]['public_episode_published_at'])
                if stamp.tzinfo is None or stamp.date()!=row[0]:raise ValueError('Ambiguous publication time')
            except (KeyError,ValueError):raise ValueError('Same-day episodes require reviewed timezone-aware publication timestamps; refusing to guess')
            timed.append((stamp,row))
        timed.sort(key=lambda pair:pair[0],reverse=True)
        if len(timed)>1 and timed[0][0]==timed[1][0]:raise ValueError('Publication timestamp tie requires editorial review')
        selected=timed[0][1]
    else:selected=eligible[0]
    return selected[2],selected[3],{'eligible_count':len(eligible),'excluded':excluded}
def render_feature(site,post,entry):
    esc=lambda s:html.escape(str(s),quote=True)
    rel=('https://www.youtube.com/watch?v='+post['youtube_id']) if post.get('video_only') else '/blog/posts/'+post['slug']+'.html'
    image=entry.get('image_path')
    if image:
        p=(site/image).resolve()
        if not p.is_relative_to(site.resolve()) or not p.is_file():raise ValueError('Approved image missing or unsafe')
        source='/'+image;dimensions='width="1200" height="675"'
    else:source='https://i.ytimg.com/vi/'+post['youtube_id']+'/hqdefault.jpg';dimensions='width="480" height="270"'
    date=datetime.date.fromisoformat(entry['public_episode_date'])
    display=date.strftime('%B ')+str(date.day)+date.strftime(', %Y')
    return '<article class="feature"><p class="kicker">Latest long-form episode</p><a class="feature-image" href="'+rel+'"><img src="'+esc(source)+'" alt="'+esc(post['title'])+'" '+dimensions+' fetchpriority="high" loading="eager"></a><h2><a href="'+rel+'">'+esc(post['title'])+'</a></h2><p class="feature-meta"><time datetime="'+entry['public_episode_date']+'">Episode · '+display+'</time><span aria-hidden="true">·</span><span>By Jeremy Magruder</span></p><a class="text-link" href="https://www.youtube.com/watch?v='+post['youtube_id']+'" target="_blank" rel="noopener">Watch the episode <span aria-hidden="true">↗</span></a></article>'
def refresh(site,as_of,ledger_path=None):
    site=Path(site).resolve();path=Path(ledger_path) if ledger_path else site/'tools/public-content.json'
    ledger=json.loads(path.read_text(encoding='utf-8'))
    post,entry,audit=select_feature(site,ledger,as_of)
    template=(site/'tools/homepage-template.html').read_text(encoding='utf-8')
    if template.count('<!-- FEATURED_START -->')!=1 or template.count('<!-- FEATURED_END -->')!=1:raise ValueError('Featured markers invalid')
    rendered=re.sub(r'<!-- FEATURED_START -->.*?<!-- FEATURED_END -->',lambda m:'<!-- FEATURED_START -->'+render_feature(site,post,entry)+'<!-- FEATURED_END -->',template,flags=re.S)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=site,prefix='.featured-',suffix='.tmp',delete=False) as f:f.write(rendered);temporary=f.name
    os.replace(temporary,site/'index.html')
    return {'selected_slug':post['slug'],'youtube_id':entry['youtube_id'],'episode_date':entry['public_episode_date'],'manifest_sha256':sha(site/'blog/posts.json'),'ledger_sha256':sha(path),**audit}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--site',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--as-of',required=True,type=datetime.date.fromisoformat);p.add_argument('--ledger',type=Path);args=p.parse_args()
    print(json.dumps(refresh(args.site,args.as_of,args.ledger),indent=2))
