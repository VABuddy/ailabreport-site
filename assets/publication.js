document.documentElement.classList.add('has-js');
/* Small progressive enhancements; every content destination remains an HTML link. */
document.querySelectorAll('.mobile-menu').forEach(menu=>{
  menu.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>{menu.open=false;}));
  menu.addEventListener('keydown',event=>{if(event.key==='Escape'){menu.open=false;menu.querySelector('summary').focus();}});
});
const search=document.querySelector('#article-search');
const topic=document.querySelector('#article-topic');
const cards=[...document.querySelectorAll('.archive-list .post-card')];
if(search&&topic){
  function filterArticles(){
    const term=search.value.trim().toLowerCase(),selected=topic.value;
    let count=0;
    cards.forEach(card=>{const matches=card.textContent.toLowerCase().includes(term)&&(!selected||(card.dataset.topic||card.querySelector('.tag')?.textContent.trim())===selected);card.hidden=!matches;if(matches)count++;});
    document.querySelector('#search-status').textContent=count===cards.length?'All published articles':count+' matching '+(count===1?'article':'articles');
    document.querySelector('#empty-results').hidden=count!==0;
  }
  search.addEventListener('input',filterArticles);topic.addEventListener('change',filterArticles);
  document.querySelector('#clear-search').addEventListener('click',()=>{search.value='';topic.value='';filterArticles();search.focus();});
}

const searchForm=document.querySelector('.archive-tools');if(searchForm)searchForm.addEventListener('submit',e=>e.preventDefault());
