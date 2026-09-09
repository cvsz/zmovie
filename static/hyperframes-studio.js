(()=>{
  'use strict';

  let templates=[];
  let installed=false;

  function byId(id){return document.getElementById(id)}

  function selectedTemplate(){
    const select=byId('hyperframeTemplate');
    if(!select||!select.value)return null;
    return templates.find(item=>item.id===select.value)||null;
  }

  function renderPreview(){
    const target=byId('hyperframePreview');
    if(!target)return;
    const item=selectedTemplate();
    if(!item){
      target.innerHTML='<div class="small">No template selected. Storyboard generation will use the free-form content brief.</div>';
      return;
    }
    const notes=(item.safety_notes||[]).map(note=>`<li>${window.esc?window.esc(note):String(note)}</li>`).join('');
    const tags=(item.tags||[]).join(', ');
    target.innerHTML=`<div class="scene"><img src="${item.preview_image}" alt="${item.title}" style="display:block;width:100%;height:auto;border-radius:10px;border:1px solid var(--line);margin-bottom:10px"><strong>${item.title}</strong><p class="small">${item.description}</p><div class="small">${item.category} · ${item.default_platform} · ${item.default_aspect_ratio} · ${item.default_duration_seconds}s</div><div class="small">Tags: ${tags}</div><details style="margin-top:8px"><summary>Template safety notes</summary><ul>${notes}</ul></details></div>`;
  }

  function applyDefaults(){
    const item=selectedTemplate();
    if(!item)return;
    const aspect=byId('aspect');
    const duration=byId('duration');
    if(aspect&&[...aspect.options].some(option=>option.value===item.default_aspect_ratio||option.text===item.default_aspect_ratio)){
      aspect.value=item.default_aspect_ratio;
    }
    if(duration)duration.value=String(Math.max(10,Number(item.default_duration_seconds)||10));
    renderPreview();
  }

  async function loadTemplates(){
    if(typeof window.api!=='function')return;
    try{
      const data=await window.api('/api/v2/hyperframes/templates');
      templates=Array.isArray(data.items)?data.items:[];
      const select=byId('hyperframeTemplate');
      if(!select)return;
      const current=select.value;
      select.innerHTML='<option value="">Free-form / no Hyperframes preset</option>'+templates.map(item=>`<option value="${item.id}">${item.title} · ${item.default_aspect_ratio} · ${item.default_duration_seconds}s</option>`).join('');
      if(current&&templates.some(item=>item.id===current))select.value=current;
      renderPreview();
    }catch(error){
      const target=byId('hyperframePreview');
      if(target)target.innerHTML=`<div class="bad small">Hyperframes unavailable: ${String(error.message||error)}</div>`;
    }
  }

  function install(){
    if(installed)return;
    const panel=byId('createPanel');
    const mark=panel&&panel.querySelector('.productionMark');
    if(!panel||!mark)return;
    installed=true;

    const block=document.createElement('div');
    block.id='hyperframesPanel';
    block.innerHTML=`<label>Hyperframes creative template<select id="hyperframeTemplate"><option value="">Loading templates…</option></select></label><div id="hyperframePreview" class="help">Loading Hyperframes template library…</div>`;
    mark.insertAdjacentElement('afterend',block);
    byId('hyperframeTemplate').addEventListener('change',applyDefaults);

    const original=window.contentPayload;
    if(typeof original==='function'){
      window.contentPayload=function(){
        const payload=original();
        const select=byId('hyperframeTemplate');
        payload.template_id=select?select.value:'';
        return payload;
      };
    }

    loadTemplates();
    ['loginBtn','bootstrapBtn'].forEach(id=>{
      const button=byId(id);
      if(button)button.addEventListener('click',()=>setTimeout(loadTemplates,500));
    });
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);
  else install();
})();
