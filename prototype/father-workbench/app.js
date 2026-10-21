const fallbackRegistry={projects:[]};
const fallbackProviders={providers:[]};
const fallbackGit={snapshot_kind:"FALLBACK",repository:"",default_branch:"main",branches:[]};

let model={
  registry:fallbackRegistry,
  providers:fallbackProviders,
  providerRuntime:{providers:[]},
  providerConnections:{},
  git:fallbackGit,
  stageStates:{},
  liveStates:{},
  evidenceStates:{},
  manufacturingEvents:{},
  traceability:{},
  devsecopsStates:{},
  evidencePacks:{},
  providerBindings:{},
  migrationSecurity:{},
  migrationCutover:{},
  migrationPlans:{},
  migrationVerifications:{}
};
let selectedProject=null;
let selectedStage=null;
let activeTab="overview";

const byId=(id)=>document.getElementById(id);
const esc=(value)=>String(value??"")
  .replaceAll("&","&amp;")
  .replaceAll("<","&lt;")
  .replaceAll(">","&gt;")
  .replaceAll('"',"&quot;");

function stateClass(value){
  const v=String(value||"").toUpperCase();
  if(["PASS","MERGED","CONNECTED","READY_FOR_MERGE"].includes(v))return"pass";
  if(["IN_PROGRESS","SECURITY_INTAKE","PRODUCT_DISCOVERY","AHEAD","RETURN"].includes(v))return"progress";
  if(["FAIL","BLOCKED","DIVERGED"].includes(v))return"blocked";
  if(["WAITING","NOT_READY","IN_REVIEW","READY","HOLD"].includes(v))return"waiting";
  return"idle";
}

async function readFirst(paths,fallback){
  for(const path of paths){
    try{
      const response=await fetch(path,{cache:"no-store"});
      if(response.ok)return await response.json();
    }catch(_error){}
  }
  return fallback;
}

function projectById(id){
  return (model.registry.projects||[]).find((item)=>item.project_id===id)||null;
}

function stageState(projectId){
  return model.stageStates[projectId]||null;
}

function branchState(project){
  if(!project)return null;
  return (model.git.branches||[]).find((item)=>item.branch===project.branch)||null;
}

function providerById(id){
  return (model.providers.providers||[]).find((item)=>item.id===id)||null;
}

function providerRuntimeById(id){
  return (model.providerRuntime.providers||[]).find((item)=>item.id===id)||null;
}

function providerSupportsAction(id,action){
  const provider=providerById(id);
  return (provider?.write_capabilities||[]).includes(action);
}

function activeDevBinding(project){
  if(!project)return null;
  const tracked=model.providerBindings[project.project_id]?.bindings?.primary;
  if(tracked?.provider && tracked?.repository && tracked?.branch){
    return tracked;
  }
  const dev=project.dev_platform||{};
  return{
    provider:dev.primary_provider||"github",
    repository:dev.repository||project.repository,
    branch:dev.branch||project.branch,
    status:"REGISTRY_FALLBACK"
  };
}

function stageById(projectId,stageId){
  const state=stageState(projectId);
  return state?.stages?.find((item)=>item.id===stageId)||null;
}

async function loadRuntimeHistory(project){
  if(!project)return;
  const projectId=encodeURIComponent(project.project_id);
  const evidence=await readFirst(
    ["/api/projects/"+projectId+"/evidence"],
    {evidence:[]}
  );
  const events=await readFirst(
    ["/api/projects/"+projectId+"/manufacturing-events"],
    {events:[]}
  );
  const traceability=await readFirst(
    ["/api/projects/"+projectId+"/traceability"],
    null
  );
  const devsecops=await readFirst(
    ["/api/projects/"+projectId+"/devsecops/current"],
    null
  );
  const packs=await readFirst(
    ["/api/projects/"+projectId+"/evidence-packs"],
    {packs:[]}
  );
  const bindings=await readFirst(
    ["/api/projects/"+projectId+"/dev-platform/bindings"],
    {status:"BLOCKED",bindings:null,etag:null}
  );
  const migrationSecurity=await readFirst(
    ["/api/projects/"+projectId+"/dev-platform/migration-security"],
    {status:"BLOCKED",reviews:[],etag:null}
  );
  const migrationCutover=await readFirst(
    ["/api/projects/"+projectId+"/dev-platform/cutover"],
    {status:"BLOCKED",approvals:[],etag:null}
  );
  model.evidenceStates[project.project_id]=evidence.evidence||[];
  model.manufacturingEvents[project.project_id]=events.events||[];
  model.traceability[project.project_id]=traceability;
  model.devsecopsStates[project.project_id]=devsecops?.devsecops||null;
  model.evidencePacks[project.project_id]=packs.packs||[];
  model.providerBindings[project.project_id]=bindings;
  model.migrationSecurity[project.project_id]=migrationSecurity;
  model.migrationCutover[project.project_id]=migrationCutover;
}

async function loadLiveState(project){
  if(!project)return null;
  try{
    const response=await fetch(
      "/api/projects/"+encodeURIComponent(project.project_id)+"/dev-platform/live",
      {cache:"no-store"}
    );
    if(!response.ok)return null;
    const payload=await response.json();
    model.liveStates[project.project_id]=payload.live||null;
    return payload.live||null;
  }catch(_error){
    return null;
  }
}

async function loadStageState(project){
  if(!project)return null;
  const ref=project.stage_state_ref;
  const fallbackPath=ref?("../../"+ref):null;
  const paths=["/api/projects/"+encodeURIComponent(project.project_id)+"/stages"];
  if(fallbackPath)paths.push(fallbackPath);
  const state=await readFirst(paths,null);
  if(state)model.stageStates[project.project_id]=state;
  return state;
}

async function load(){
  model.registry=await readFirst(
    ["/api/projects","../../projects/registry.json"],
    fallbackRegistry
  );
  model.providers=await readFirst(
    ["/api/providers","../../config/dev_platform/providers.json"],
    fallbackProviders
  );
  model.providerRuntime=await readFirst(
    ["/api/providers/runtime"],
    {providers:[]}
  );
  model.git=await readFirst(
    ["/api/git-snapshot","../../docs/git/current_workspace.snapshot.json"],
    fallbackGit
  );

  for(const project of model.registry.projects||[]){
    await loadStageState(project);
  }

  if(!selectedProject){
    selectedProject=model.registry.projects?.[0]?.project_id||null;
  }
  if(selectedProject && !selectedStage){
    selectedStage=stageState(selectedProject)?.current_stage||null;
  }

  if(selectedProject){
    const selected=projectById(selectedProject);
    await loadLiveState(selected);
    await loadRuntimeHistory(selected);
  }

  byId("snapshot").textContent=
    model.git.snapshot_kind==="POINT_IN_TIME"
      ?"Dev Platform snapshot"
      :"prototype / fallback";

  render();
}

function mini(label,value){
  return '<div class="mini"><span>'+esc(label)+'</span><b>'+esc(value||"—")+'</b></div>';
}

function render(){
  renderProjects();
  renderWorkspace();
  renderGitMap();
  renderProviderMatrix();
}

function renderProjects(){
  const host=byId("projects");
  host.innerHTML="";

  for(const project of model.registry.projects||[]){
    const branch=effectiveBranchState(project);
    const state=stageState(project.project_id);
    const card=document.createElement("article");
    card.className="project"+(project.project_id===selectedProject?" selected":"");
    card.innerHTML=
      '<div class="projectHead">'+
        '<div><h3>'+esc(project.name)+'</h3><div class="id">'+esc(project.project_id)+'</div></div>'+
        '<span class="chip '+stateClass(project.status)+'">'+esc(project.status)+'</span>'+
      '</div>'+
      '<div class="miniGrid">'+
        mini("Stage",state?.current_stage||project.current_stage)+
        mini("Product Gate",project.product_gate)+
        mini("Security",project.security_gate)+
        mini("Dev Platform",branch?.relation_to_main||project.dev_platform?.provider_status||"NO SNAPSHOT")+
      '</div>';

    card.onclick=async()=>{
      selectedProject=project.project_id;
      selectedStage=state?.current_stage||state?.stages?.[0]?.id||null;
      activeTab="overview";
      await loadLiveState(project);
      await loadRuntimeHistory(project);
      render();
    };
    host.appendChild(card);
  }
}

function renderWorkspace(){
  const project=projectById(selectedProject);
  const state=stageState(selectedProject);
  if(!project||!state)return;

  if(!stageById(selectedProject,selectedStage)){
    selectedStage=state.current_stage||state.stages?.[0]?.id||null;
  }

  const branch=branchState(project);
  byId("projectId").textContent=project.project_id;
  byId("projectName").textContent=project.name;
  byId("projectDescription").textContent=state.description||"—";
  byId("projectStatus").textContent=project.status||"UNKNOWN";
  byId("projectStatus").className="chip "+stateClass(project.status);
  const activeBinding=activeDevBinding(project);
  byId("projectBranch").textContent=
    (activeBinding?.provider||"provider TBD")+" · "+
    (activeBinding?.branch||"branch TBD");

  renderKpis(project,state,branch);
  renderConveyor(state);
  renderInspector(state);
  renderScorecards(state);
  renderDevPlatformPanel(project,branch);
  renderScmActions(project,state,branch);
  renderChecks(state);
}

function effectiveBranchState(project){
  const live=model.liveStates[project?.project_id];
  if(live?.branch && live?.compare){
    return{
      branch:live.branch.name,
      head_sha:live.branch.head_sha,
      relation_to_main:String(live.compare.status||"LIVE").toUpperCase(),
      ahead_by:live.compare.ahead_by,
      behind_by:live.compare.behind_by,
      open_pull_request:(live.change_requests||[]).length>0,
      live:true
    };
  }
  return branchState(project);
}

function renderKpis(project,state,branch){
  const docs=state.document_summary||{done:0,total:0};
  const rows=[
    ["Product Gate",project.product_gate||"—","PM decision"],
    ["Security Gate",project.security_gate||"—","InfoSec + DevSecOps"],
    ["Documents",docs.done+" / "+docs.total,"project projection"],
    ["Evidence",
      String((model.evidenceStates[project.project_id]||[]).length),
      (model.evidencePacks[project.project_id]||[]).length+
        " durable pack(s) · "+(state.evidence_status||"no evidence → no pass")],
    ["SCM",branch?.relation_to_main||project.dev_platform?.provider_status||"—",
      branch?("+"+(branch.ahead_by||0)+" / -"+(branch.behind_by||0)):"provider state"]
  ];
  byId("kpis").innerHTML=rows.map((row)=>
    '<div class="kpi"><span>'+esc(row[0])+'</span><b>'+esc(row[1])+
    '</b><small>'+esc(row[2])+'</small></div>'
  ).join("");
}

function renderConveyor(state){
  const host=byId("conveyor");
  host.innerHTML="";
  for(const stage of state.stages||[]){
    const node=document.createElement("button");
    node.className="stage "+stateClass(stage.status)+(stage.id===selectedStage?" active":"");
    node.innerHTML=
      '<small>'+esc(stage.id)+'</small>'+
      '<b>'+esc(stage.short||stage.name)+'</b>'+
      '<i>'+esc(stage.status)+'</i>'+
      '<div class="stageMeta"><span>DOCS</span><span>'+
        (stage.documents?.done||0)+"/"+(stage.documents?.total||0)+
      '</span></div>'+
      '<div class="stageMeta"><span>GATE</span><span>'+esc(stage.gate||"—")+'</span></div>';
    node.onclick=()=>{
      selectedStage=stage.id;
      activeTab="overview";
      renderConveyor(state);
      renderInspector(state);
    };
    host.appendChild(node);
  }
}

function detail(label,value){
  return '<div class="detail"><span>'+esc(label)+'</span><b>'+esc(value)+'</b></div>';
}

function renderInspector(state){
  const stage=stageById(selectedProject,selectedStage);
  if(!stage)return;

  byId("stageTitle").textContent=(stage.short||stage.id)+" · "+stage.name;
  byId("stageStatus").textContent=stage.status;
  byId("stageStatus").className="chip "+stateClass(stage.status);

  document.querySelectorAll(".tab").forEach((tab)=>{
    tab.classList.toggle("active",tab.dataset.tab===activeTab);
    tab.onclick=()=>{
      activeTab=tab.dataset.tab;
      renderInspector(state);
    };
  });

  const host=byId("stageContent");
  if(activeTab==="documents")host.innerHTML=documentsHtml(stage);
  else if(activeTab==="analysis")host.innerHTML=analysisHtml(stage);
  else if(activeTab==="decisions")host.innerHTML=decisionsHtml(stage);
  else if(activeTab==="risks")host.innerHTML=risksHtml(stage);
  else if(activeTab==="security")host.innerHTML=securityHtml(stage,state);
  else if(activeTab==="traceability")host.innerHTML=traceabilityHtml(selectedProject,stage.id);
  else if(activeTab==="history")host.innerHTML=historyHtml(stage,selectedProject);
  else host.innerHTML=overviewHtml(stage);

  wireGateControls(state,stage);
  wireArtifactControls(state,stage);
  wireProductionRecordControls(state,stage);
}

function overviewHtml(stage){
  return '<div class="details">'+
    detail("Owner",stage.owner||"—")+
    detail("Gate",stage.gate||"—")+
    detail("Documents",(stage.documents?.done||0)+" / "+(stage.documents?.total||0))+
    detail("Open risks",stage.open_risks??"—")+
    detail("Cost impact",stage.cost_impact||"—")+
    detail("Lessons",(stage.lessons||[]).length)+
  '</div>'+
  '<div class="analysis">'+esc(stage.analysis||"No specialist analysis yet.")+'</div>'+
  '<div class="gateControl">'+
    '<div><em>GATE ENGINE</em><div class="gateHint">Mechanical checks never auto-PASS a stage.</div></div>'+
    '<div class="gateButtons">'+
      (stage.status==="READY"
        ?'<button class="gateBtn" data-stage-action="start">Start Stage</button>'
        :'')+
      '<button class="gateBtn" data-gate-action="recalculate">Recalculate Gate</button>'+
      '<button class="gateBtn" data-gate-action="decide">Human Gate Decision</button>'+
    '</div>'+
    '<div class="gateOutput" id="gateOutput">No gate recalculation in this session.</div>'+
  '</div>';
}

async function submitStageStart(projectId,payload){
  try{
    const response=await fetch("/api/stages/start",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        confirm:true,
        ...payload
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function handleStageStart(state,stage){
  if(stage.status!=="READY")return;
  const rationale=(window.prompt(
    "Why is this stage starting now? (required)",
    ""
  )||"").trim();
  if(!rationale)return;

  const inventory=await loadArtifactState(selectedProject);
  const expectedEtag=inventory?.state_etag;
  if(!expectedEtag){
    window.alert("Cannot start stage: project state ETag unavailable.");
    return;
  }

  const confirmed=window.confirm(
    "Start "+stage.id+" · "+stage.name+
    "? READY will become IN_PROGRESS and the decision will be recorded."
  );
  if(!confirmed)return;

  const result=await submitStageStart(
    selectedProject,
    {
      stage_id:stage.id,
      rationale,
      started_by:"HUMAN_LOCAL_OPERATOR",
      expected_etag:expectedEtag
    }
  );
  if(result.status!=="STARTED"){
    window.alert(
      (result.status||"BLOCKED")+": "+
      (result.errors||["UNKNOWN_ERROR"]).join(", ")
    );
    return;
  }

  const project=projectById(selectedProject);
  await loadStageState(project);
  await loadRuntimeHistory(project);
  renderWorkspace();
  renderProjects();
}

async function recalculateGate(projectId,stageId){
  try{
    const response=await fetch("/api/gates/recalculate",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        project_id:projectId,
        stage_id:stageId
      })
    });
    return await response.json();
  }catch(_error){
    return{
      mechanical_status:"ERROR",
      blockers:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function submitGateDecision(projectId,stageId,payload){
  try{
    const response=await fetch("/api/gates/decide",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        stage_id:stageId,
        confirm:true,
        ...payload
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      http_status:0,
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

function wireGateControls(state,stage){
  if(activeTab!=="overview")return;
  const output=byId("gateOutput");
  const recalc=document.querySelector('[data-gate-action="recalculate"]');
  const decide=document.querySelector('[data-gate-action="decide"]');
  const start=document.querySelector('[data-stage-action="start"]');
  if(!output||!recalc||!decide)return;
  if(start)start.onclick=()=>handleStageStart(state,stage);

  let lastEvaluation=null;

  const showEvaluation=(evaluation)=>{
    lastEvaluation=evaluation;
    const blockers=evaluation.blockers||[];
    output.textContent=
      "mechanical: "+(evaluation.mechanical_status||"UNKNOWN")+
      " · current gate: "+(evaluation.current_gate||stage.gate||"—")+
      " · accepted docs: "+(evaluation.accepted_required_document_count??"—")+
      "/"+(evaluation.required_document_count??"—")+
      (blockers.length?" · blockers: "+blockers.join(", "):"")+
      " · auto-pass: NO";
    output.className="gateOutput "+(
      evaluation.review_candidate?"ok":"block"
    );
  };

  recalc.onclick=async()=>{
    output.textContent="Recalculating gate…";
    output.className="gateOutput";
    showEvaluation(
      await recalculateGate(selectedProject,stage.id)
    );
  };

  decide.onclick=async()=>{
    const evaluation=lastEvaluation||
      await recalculateGate(selectedProject,stage.id);
    showEvaluation(evaluation);

    const decision=(window.prompt(
      "Gate decision: PASS / FAIL / HOLD / RETURN",
      evaluation.review_candidate?"PASS":"HOLD"
    )||"").trim().toUpperCase();
    if(!decision)return;

    const rationale=(window.prompt(
      "Decision rationale (required)",
      ""
    )||"").trim();
    if(!rationale)return;

    let evidenceRefs=[];
    if(decision==="PASS"){
      const evidence=(window.prompt(
        "Evidence refs, comma separated (required for PASS)",
        ""
      )||"").trim();
      evidenceRefs=evidence
        ?evidence.split(",").map((item)=>item.trim()).filter(Boolean)
        :[];
    }else{
      const evidence=(window.prompt(
        "Evidence refs, comma separated (optional)",
        ""
      )||"").trim();
      evidenceRefs=evidence
        ?evidence.split(",").map((item)=>item.trim()).filter(Boolean)
        :[];
    }

    const confirmed=window.confirm(
      "Apply human gate decision '"+decision+"' to "+stage.id+
      "? This changes tracked project-state and requires a Git commit."
    );
    if(!confirmed)return;

    output.textContent="Applying gate decision…";
    output.className="gateOutput";

    const result=await submitGateDecision(
      selectedProject,
      stage.id,
      {
        decision,
        rationale,
        evidence_refs:evidenceRefs,
        decided_by:"HUMAN_LOCAL_OPERATOR",
        expected_etag:evaluation.state_etag||""
      }
    );

    if(result.status!=="APPLIED"){
      output.textContent=
        (result.status||"BLOCKED")+" · "+
        (result.errors||["UNKNOWN_ERROR"]).join(", ");
      output.className="gateOutput block";
      return;
    }

    const project=projectById(selectedProject);
    await loadStageState(project);
    await loadRuntimeHistory(project);
    renderWorkspace();
    renderProjects();
    const refreshed=byId("gateOutput");
    if(refreshed){
      refreshed.textContent=
        "APPLIED · "+decision+
        " · evidence "+(result.evidence?.evidence_id||"—")+
        " · current stage "+(result.lifecycle?.current_stage||"—")+
        " · tracked state changed · Git commit required";
      refreshed.className="gateOutput ok";
    }
  };
}

function documentsHtml(stage){
  const docs=stage.documents?.items||[];
  const rows=docs.length
    ?'<div class="rows">'+docs.map((item)=>
      '<div class="row artifactRow">'+
        '<span class="code">'+esc(item.id)+'</span>'+
        '<span>'+esc(item.title)+'</span>'+
        '<span class="artifactActions">'+
          '<span class="pill '+esc(item.status)+'">'+esc(item.status)+'</span>'+
          (item.source_ref
            ?'<button class="miniAction" data-artifact-content="'+esc(item.id)+'">Content</button>'
            :'')+
          '<button class="miniAction" data-artifact-edit="'+esc(item.id)+'">Status</button>'+
        '</span>'+
      '</div>'
    ).join("")+'</div>'
    :'<div class="empty">Документы этапа ещё не созданы.</div>';
  return '<div class="artifactToolbar">'+
      '<button class="gateBtn" data-artifact-add="1">+ Register artifact</button>'+
      '<span>PASS требует rationale + evidence refs</span>'+
    '</div>'+rows;
}

async function loadArtifactState(projectId){
  return await readFirst(
    ["/api/projects/"+encodeURIComponent(projectId)+"/artifacts"],
    null
  );
}

async function submitArtifactUpdate(projectId,payload){
  try{
    const response=await fetch("/api/artifacts/upsert",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        confirm:true,
        ...payload
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function loadDocumentContent(projectId,stageId,artifactId){
  try{
    const path="/api/projects/"+encodeURIComponent(projectId)+
      "/stages/"+encodeURIComponent(stageId)+
      "/artifacts/"+encodeURIComponent(artifactId)+"/content";
    const response=await fetch(path,{cache:"no-store"});
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function saveDocumentContent(projectId,payload){
  try{
    const response=await fetch("/api/documents/write",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        confirm:true,
        ...payload
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

function renderDocumentEditor(stage,artifact,payload){
  const host=byId("stageContent");
  if(!host)return;

  host.querySelector(".documentEditor")?.remove();
  const wrapper=document.createElement("div");
  wrapper.className="documentEditor";

  const head=document.createElement("div");
  head.className="documentEditorHead";
  const title=document.createElement("div");
  title.innerHTML="<em>DOCUMENT EDITOR</em><strong></strong><small></small>";
  title.querySelector("strong").textContent=artifact.title||artifact.id;
  title.querySelector("small").textContent=
    payload.document.source_ref+" · SHA "+payload.document.sha256.slice(0,12);
  const close=document.createElement("button");
  close.className="miniAction";
  close.textContent="Close";
  close.onclick=()=>wrapper.remove();
  head.append(title,close);

  const textarea=document.createElement("textarea");
  textarea.className="documentTextarea";
  textarea.value=payload.document.content||"";
  textarea.spellcheck=false;

  const foot=document.createElement("div");
  foot.className="documentEditorFoot";
  const status=document.createElement("span");
  status.className="documentSaveState";
  status.textContent=payload.document.exists
    ?"Loaded "+payload.document.size+" bytes"
    :"New file";
  const save=document.createElement("button");
  save.className="gateBtn";
  save.textContent="Save document";
  save.onclick=async()=>{
    const rationale=(window.prompt(
      "Why are you changing this document? (required)",
      ""
    )||"").trim();
    if(!rationale)return;

    const confirmed=window.confirm(
      "Save "+payload.document.source_ref+
      "? This changes the tracked worktree and requires a Git commit."
    );
    if(!confirmed)return;

    save.disabled=true;
    status.textContent="Saving…";
    const result=await saveDocumentContent(
      selectedProject,
      {
        stage_id:stage.id,
        artifact_id:artifact.id,
        content:textarea.value,
        expected_sha256:payload.document.sha256,
        rationale,
        decided_by:"HUMAN_LOCAL_OPERATOR"
      }
    );
    save.disabled=false;

    if(!["UPDATED","NO_CHANGE"].includes(result.status)){
      status.textContent=
        (result.status||"BLOCKED")+" · "+
        (result.errors||["UNKNOWN_ERROR"]).join(", ");
      status.className="documentSaveState failText";
      return;
    }

    status.className="documentSaveState okText";
    if(result.status==="UPDATED"){
      payload.document.sha256=result.document.new_sha256;
      status.textContent=
        "UPDATED · SHA "+result.document.new_sha256.slice(0,12)+
        " · evidence "+(result.evidence?.evidence_id||"—")+
        " · Git commit required";
      await loadRuntimeHistory(projectById(selectedProject));
    }else{
      status.textContent="NO CHANGE";
    }
  };

  foot.append(status,save);
  wrapper.append(head,textarea,foot);
  host.appendChild(wrapper);
}

async function openDocumentEditor(stage,artifact){
  const payload=await loadDocumentContent(
    selectedProject,
    stage.id,
    artifact.id
  );
  if(payload.status!=="OK"){
    window.alert(
      (payload.status||"BLOCKED")+": "+
      (payload.errors||["UNKNOWN_ERROR"]).join(", ")
    );
    return;
  }
  renderDocumentEditor(stage,artifact,payload);
}

function wireArtifactControls(state,stage){
  if(activeTab!=="documents")return;

  const apply=async(existing)=>{
    const artifactId=(window.prompt(
      "Artifact / document ID",
      existing?.id||""
    )||"").trim();
    if(!artifactId)return;

    const title=(window.prompt(
      "Artifact title",
      existing?.title||""
    )||"").trim();
    if(!title)return;

    const status=(window.prompt(
      "Status: DRAFT / IN_REVIEW / PASS / FAIL / BLOCKED / TBD",
      existing?.status||"DRAFT"
    )||"").trim().toUpperCase();
    if(!status)return;

    const rationale=(window.prompt(
      "Why is this status correct? (required)",
      ""
    )||"").trim();
    if(!rationale)return;

    const evidenceText=(window.prompt(
      "Evidence refs, comma separated"+(status==="PASS"?" (required for PASS)":" (optional)"),
      ""
    )||"").trim();
    const evidenceRefs=evidenceText
      ?evidenceText.split(",").map((item)=>item.trim()).filter(Boolean)
      :[];

    const sourceRef=(window.prompt(
      "Source/path/reference (optional)",
      existing?.source_ref||""
    )||"").trim();

    const inventory=await loadArtifactState(selectedProject);
    if(!inventory?.state_etag){
      window.alert("Cannot update artifact: project state ETag unavailable.");
      return;
    }

    const confirmed=window.confirm(
      "Apply "+status+" to "+artifactId+
      "? This changes tracked project-state and requires a Git commit."
    );
    if(!confirmed)return;

    const result=await submitArtifactUpdate(
      selectedProject,
      {
        stage_id:stage.id,
        artifact_id:artifactId,
        title,
        status,
        rationale,
        evidence_refs:evidenceRefs,
        source_ref:sourceRef||null,
        decided_by:"HUMAN_LOCAL_OPERATOR",
        expected_etag:inventory.state_etag
      }
    );

    if(result.status!=="APPLIED"){
      window.alert(
        (result.status||"BLOCKED")+": "+
        (result.errors||["UNKNOWN_ERROR"]).join(", ")
      );
      return;
    }

    const project=projectById(selectedProject);
    await loadStageState(project);
    await loadRuntimeHistory(project);
    renderWorkspace();
    renderProjects();
  };

  const add=document.querySelector("[data-artifact-add]");
  if(add)add.onclick=()=>apply(null);

  document.querySelectorAll("[data-artifact-edit]").forEach((button)=>{
    button.onclick=()=>{
      const existing=(stage.documents?.items||[]).find(
        (item)=>item.id===button.dataset.artifactEdit
      );
      apply(existing||null);
    };
  });

  document.querySelectorAll("[data-artifact-content]").forEach((button)=>{
    button.onclick=()=>{
      const existing=(stage.documents?.items||[]).find(
        (item)=>item.id===button.dataset.artifactContent
      );
      if(existing)openDocumentEditor(stage,existing);
    };
  });
}

function traceabilityHtml(projectId,stageId){
  const graph=model.traceability[projectId];
  if(!graph){
    return '<div class="empty">Traceability graph unavailable.</div>';
  }

  const kinds={};
  for(const node of graph.nodes||[]){
    kinds[node.kind]=(kinds[node.kind]||0)+1;
  }
  const stagePrefix="stage:"+stageId;
  const relatedEdges=(graph.edges||[]).filter((edge)=>
    edge.source===stagePrefix||
    edge.target===stagePrefix||
    edge.source.includes(":"+stageId+":")||
    edge.target.includes(":"+stageId+":")
  );

  return '<div class="details">'+
      detail("Integrity",graph.integrity_status||"—")+
      detail("Nodes",graph.node_count||0)+
      detail("Edges",graph.edge_count||0)+
    '</div>'+
    (graph.unresolved_evidence_refs?.length
      ?'<div class="traceWarning">UNRESOLVED EVIDENCE: '+
        esc(graph.unresolved_evidence_refs.join(", "))+'</div>'
      :'<div class="analysis">Traceability evidence references resolved.</div>')+
    '<div class="traceKinds">'+Object.entries(kinds).map(([kind,count])=>
      '<span><b>'+esc(kind)+'</b> '+count+'</span>'
    ).join("")+'</div>'+
    '<div class="traceEdges">'+
      '<em>STAGE RELATIONS</em>'+
      (relatedEdges.length
        ?relatedEdges.slice(0,40).map((edge)=>
          '<div class="traceEdge">'+
            '<span>'+esc(edge.source)+'</span>'+
            '<b>'+esc(edge.relation)+'</b>'+
            '<span>'+esc(edge.target)+'</span>'+
          '</div>'
        ).join("")
        :'<div class="empty">No direct stage relations yet.</div>')+
    '</div>';
}

function analysisHtml(stage){
  const records=stage.specialist_analyses||[];
  return '<div class="analysis">'+esc(stage.analysis||"No baseline specialist analysis.")+'</div>'+
    '<div class="recordToolbar"><button class="gateBtn" data-record-add="ANALYSIS">+ Specialist analysis</button></div>'+
    (records.length
      ?'<div class="rows">'+records.map((item)=>
        '<div class="row recordRow">'+
          '<span class="code">'+esc(item.analysis_id)+'</span>'+
          '<span><b>'+esc(item.title)+'</b><small>'+esc(item.role||"")+' · '+esc(item.summary||"")+'</small></span>'+
          '<span class="pill '+esc(item.status)+'">'+esc(item.status)+'</span>'+
        '</div>'
      ).join("")+'</div>'
      :'<div class="empty">No structured specialist analyses yet.</div>');
}

function decisionsHtml(stage){
  const records=stage.decision_records||[];
  const legacy=stage.decisions||[];
  return '<div class="recordToolbar"><button class="gateBtn" data-record-add="DECISION">+ Decision record</button></div>'+
    (records.length
      ?'<div class="rows">'+records.map((item)=>
        '<div class="row recordRow">'+
          '<span class="code">'+esc(item.decision_id)+'</span>'+
          '<span><b>'+esc(item.title)+'</b><small>'+esc(item.decision||"")+' · '+esc(item.rationale||"")+'</small></span>'+
          '<span class="pill '+esc(item.status)+'">'+esc(item.status)+'</span>'+
        '</div>'
      ).join("")+'</div>'
      :'<div class="empty">No structured decision records yet.</div>')+
    (legacy.length
      ?'<div class="legacyRecords"><em>LEGACY DECISIONS</em>'+legacy.map((item)=>
        '<div>'+esc(item)+'</div>'
      ).join("")+'</div>'
      :'');
}

function risksHtml(stage){
  const records=stage.risk_records||[];
  return '<div class="recordToolbar"><button class="gateBtn" data-record-add="RISK">+ Risk record</button></div>'+
    (records.length
      ?'<div class="rows">'+records.map((item)=>
        '<div class="row recordRow">'+
          '<span class="code">'+esc(item.risk_id)+'</span>'+
          '<span><b>'+esc(item.title)+'</b><small>'+esc(item.description||"")+' · '+esc(item.likelihood||"")+'/'+esc(item.impact||"")+'</small></span>'+
          '<span class="pill '+esc(item.status)+'">'+esc(item.status)+'</span>'+
        '</div>'
      ).join("")+'</div>'
      :'<div class="empty">No structured risks for this stage yet.</div>');
}

function commaList(value){
  return (value||"")
    .split(",")
    .map((item)=>item.trim())
    .filter(Boolean);
}

async function submitProductionRecord(projectId,payload){
  try{
    const response=await fetch("/api/records/upsert",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        confirm:true,
        ...payload
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function addSpecialistAnalysis(stage,etag){
  const id=(window.prompt("Analysis ID","AN-"+stage.id+"-"+Date.now().toString().slice(-6))||"").trim();
  if(!id)return;
  const role=(window.prompt("Specialist role",stage.owner||"SPECIALIST")||"").trim();
  const title=(window.prompt("Analysis title","Stage analysis")||"").trim();
  const summary=(window.prompt("Analysis summary","")||"").trim();
  const status=(window.prompt("Status: DRAFT / IN_REVIEW / VERIFIED / REJECTED","DRAFT")||"").trim().toUpperCase();
  const findings=commaList(window.prompt("Findings, comma separated","")||"");
  const recommendations=commaList(window.prompt("Recommendations, comma separated","")||"");
  const evidenceRefs=commaList(window.prompt("Evidence refs, comma separated"+(status==="VERIFIED"?" (required)":" (optional)"),"")||"");
  if(!window.confirm("Save specialist analysis "+id+"? Git commit will be required."))return;
  return submitProductionRecord(selectedProject,{
    stage_id:stage.id,
    record_type:"ANALYSIS",
    expected_etag:etag,
    record:{
      analysis_id:id,role,title,summary,status,
      findings,recommendations,evidence_refs:evidenceRefs,
      author:"HUMAN_LOCAL_OPERATOR"
    }
  });
}

async function addDecisionRecord(stage,etag){
  const id=(window.prompt("Decision ID","DEC-"+stage.id+"-"+Date.now().toString().slice(-6))||"").trim();
  if(!id)return;
  const title=(window.prompt("Decision title","")||"").trim();
  const context=(window.prompt("Context / problem","")||"").trim();
  const decision=(window.prompt("What was decided?","")||"").trim();
  const rationale=(window.prompt("Why this decision?","")||"").trim();
  const alternatives=commaList(window.prompt("Alternatives considered, comma separated","")||"");
  const rejectedReasons=commaList(window.prompt("Why alternatives were rejected, comma separated","")||"");
  const constraints=commaList(window.prompt("Important constraints, comma separated","")||"");
  const status=(window.prompt("Status: PROPOSED / APPROVED / REJECTED / SUPERSEDED","PROPOSED")||"").trim().toUpperCase();
  const evidenceRefs=commaList(window.prompt("Evidence refs"+(status==="APPROVED"?" (required)":"")+", comma separated","")||"");
  const revisit=commaList(window.prompt("Revisit triggers, comma separated","")||"");
  if(!window.confirm("Save decision "+id+"? Git commit will be required."))return;
  return submitProductionRecord(selectedProject,{
    stage_id:stage.id,
    record_type:"DECISION",
    expected_etag:etag,
    record:{
      decision_id:id,title,context,decision,rationale,
      alternatives,rejected_reasons:rejectedReasons,
      constraints,evidence_refs:evidenceRefs,
      owner:stage.owner||"HUMAN_LOCAL_OPERATOR",
      status,revisit_triggers:revisit
    }
  });
}

async function addRiskRecord(stage,etag){
  const id=(window.prompt("Risk ID","RISK-"+stage.id+"-"+Date.now().toString().slice(-6))||"").trim();
  if(!id)return;
  const title=(window.prompt("Risk title","")||"").trim();
  const description=(window.prompt("Risk description","")||"").trim();
  const likelihood=(window.prompt("Likelihood: LOW / MEDIUM / HIGH / CRITICAL","MEDIUM")||"").trim().toUpperCase();
  const impact=(window.prompt("Impact: LOW / MEDIUM / HIGH / CRITICAL","HIGH")||"").trim().toUpperCase();
  const treatment=(window.prompt("Treatment / mitigation","")||"").trim();
  const status=(window.prompt("Status: OPEN / MITIGATING / ACCEPTED / CLOSED","OPEN")||"").trim().toUpperCase();
  const evidenceRefs=commaList(window.prompt("Evidence refs"+(["ACCEPTED","CLOSED"].includes(status)?" (required)":"")+", comma separated","")||"");
  if(!window.confirm("Save risk "+id+"? Git commit will be required."))return;
  return submitProductionRecord(selectedProject,{
    stage_id:stage.id,
    record_type:"RISK",
    expected_etag:etag,
    record:{
      risk_id:id,title,description,likelihood,impact,treatment,
      owner:stage.owner||"HUMAN_LOCAL_OPERATOR",
      status,evidence_refs:evidenceRefs
    }
  });
}

function wireProductionRecordControls(state,stage){
  if(!["analysis","decisions","risks"].includes(activeTab))return;
  const button=document.querySelector("[data-record-add]");
  if(!button)return;
  button.onclick=async()=>{
    const inventory=await loadArtifactState(selectedProject);
    if(!inventory?.state_etag){
      window.alert("Project state ETag unavailable.");
      return;
    }
    let result=null;
    if(button.dataset.recordAdd==="ANALYSIS"){
      result=await addSpecialistAnalysis(stage,inventory.state_etag);
    }else if(button.dataset.recordAdd==="DECISION"){
      result=await addDecisionRecord(stage,inventory.state_etag);
    }else if(button.dataset.recordAdd==="RISK"){
      result=await addRiskRecord(stage,inventory.state_etag);
    }
    if(!result)return;
    if(result.status!=="APPLIED"){
      window.alert(
        (result.status||"BLOCKED")+": "+
        (result.errors||["UNKNOWN_ERROR"]).join(", ")
      );
      return;
    }
    const project=projectById(selectedProject);
    await loadStageState(project);
    await loadRuntimeHistory(project);
    renderWorkspace();
    renderProjects();
    if(result.quality_warnings?.length){
      window.alert("Saved with warnings: "+result.quality_warnings.join(", "));
    }
  };
}

function securityHtml(stage,state){
  const relevant=["PD-02","DS-02","ARCH","DEV","QA","OPS"].includes(stage.id);
  const devsec=model.devsecopsStates[selectedProject];
  let html='<div class="details">'+
    detail("Security status",relevant?stage.status:"UPSTREAM / N/A")+
    detail("Hard blocker",stage.status==="BLOCKED"?"YES":"NO")+
    detail("Evidence rule","NO EVIDENCE → NO PASS")+
    detail("Current HEAD CI",devsec?.ci_current_head||"UNKNOWN")+
    detail("DevSecOps artifact",devsec?.evidence_artifact||"UNKNOWN")+
    detail("Commit-bound state",devsec?.status||"UNKNOWN")+
  '</div>';
  if(devsec?.blockers?.length){
    html+='<div class="traceWarning">DEVSECOPS BLOCKERS: '+
      esc(devsec.blockers.join(", "))+'</div>';
  }
  if(!relevant){
    return html+'<div class="analysis">Исполняемые DevSecOps checks появляются по мере продвижения конвейера.</div>';
  }
  return html+checksRows(state.checks||[]);
}

function checksRows(checks){
  return '<div class="rows">'+checks.map((item)=>
    '<div class="row"><span class="code">CHECK</span><span>'+esc(item.name)+
    '</span><span class="pill '+esc(item.status)+'">'+esc(item.status)+'</span></div>'
  ).join("")+'</div>';
}

function historyHtml(stage,projectId){
  const history=stage.history||[];
  const lessons=stage.lessons||[];
  const runtimeEvents=(model.manufacturingEvents[projectId]||[]).slice(0,12);
  const events=history.length
    ?'<div class="rows">'+history.map((item,index)=>
      '<div class="row"><span class="code">EVT-'+(index+1)+
      '</span><span>'+esc(item)+'</span><span></span></div>'
    ).join("")+'</div>'
    :'<div class="empty">No stage events yet.</div>';
  const learned=lessons.length
    ?'<div class="rows">'+lessons.map((item,index)=>
      '<div class="row"><span class="code">LESSON-'+(index+1)+
      '</span><span>'+esc(item)+'</span><span class="pill DRAFT">OBSERVED</span></div>'
    ).join("")+'</div>'
    :'<div class="empty">No lessons yet.</div>';
  const manufacturing=runtimeEvents.length
    ?'<div class="rows">'+runtimeEvents.map((item)=>
      '<div class="row"><span class="code">'+esc(item.event_type||"EVENT")+
      '</span><span>'+esc((item.payload||{}).action||item.source_ref||item.event_id)+
      '</span><span class="pill DRAFT">'+esc((item.occurred_at||"").slice(0,19))+'</span></div>'
    ).join("")+'</div>'
    :'<div class="empty">No runtime manufacturing events yet.</div>';
  return '<em>HISTORY</em>'+events+
    '<div style="height:13px"></div><em>MANUFACTURING EVENTS</em>'+manufacturing+
    '<div style="height:13px"></div><em>LESSONS LEARNED</em>'+learned;
}

function renderScorecards(state){
  byId("scorecards").innerHTML=Object.entries(state.scorecards||{}).map(([name,value])=>
    '<div class="scoreRow"><span>'+esc(name)+'</span>'+
    '<div class="meter"><i style="width:'+Number(value||0)+'%"></i></div>'+
    '<b>'+esc(value)+'%</b></div>'
  ).join("");
}

function renderDevPlatformPanel(project,branch){
  const dev=project.dev_platform||{};
  const provider=providerById(dev.primary_provider||"github");
  const providerName=provider?.name||dev.primary_provider||"Provider TBD";
  const live=model.liveStates[project.project_id];
  if(live){
    const latestRun=(live.workflow_runs||[])[0];
    const head=(live.branch?.head_sha||"").slice(0,8)||"—";
    byId("gitPanel").innerHTML=
      '<div class="branch">'+esc(providerName)+' · '+esc(live.branch?.name||project.branch)+'</div>'+
      '<div class="gitStats">'+
        '<div><span>HEAD</span><b>'+esc(head)+'</b></div>'+
        '<div><span>AHEAD</span><b>'+esc(live.compare?.ahead_by??0)+'</b></div>'+
        '<div><span>BEHIND</span><b>'+esc(live.compare?.behind_by??0)+'</b></div>'+
      '</div>'+
      '<div class="warn">'+
        'LIVE · PR/MR '+(live.change_requests||[]).length+
        ' · checks '+(live.checks||[]).length+
        ' · workflow '+esc(latestRun?(latestRun.status+"/"+(latestRun.conclusion||"—")):"none")+
      '</div>';
    return;
  }
  if(!branch){
    byId("gitPanel").innerHTML=
      '<div class="branch">'+esc(providerName)+' · '+esc(project.branch||"No branch")+'</div>'+
      '<div class="warn" style="margin-top:10px">Live SCM snapshot for this repository was not refreshed.</div>';
    return;
  }
  const warning=branch.relation_to_main==="DIVERGED"
    ?"Ветка впереди и позади default branch. Evidence/merge-readiness требуют актуализации."
    :"Ветка не отстаёт от default branch в текущем snapshot.";
  byId("gitPanel").innerHTML=
    '<div class="branch">'+esc(providerName)+' · '+esc(branch.branch)+'</div>'+
    '<div class="gitStats">'+
      '<div><span>STATE</span><b>'+esc(branch.relation_to_main)+'</b></div>'+
      '<div><span>AHEAD</span><b>'+esc(branch.ahead_by||0)+'</b></div>'+
      '<div><span>BEHIND</span><b>'+esc(branch.behind_by||0)+'</b></div>'+
    '</div><div class="warn">'+esc(warning)+'</div>';
}

function renderScmActions(project,state,branch){
  const checks=state.checks||[];
  const required=["SAST","SCA","Secret scan","Security review"];
  const missing=required.filter((name)=>{
    const hit=checks.find((item)=>item.name===name);
    return !hit||hit.status!=="PASS";
  });
  const mergeBlocked=
    project.security_gate!=="PASS"||
    missing.length>0||
    !branch||
    branch.relation_to_main==="DIVERGED";

  const activeBinding=activeDevBinding(project);
  const providerId=activeBinding?.provider||"github";
  const actions=[
    ["Create branch",!providerSupportsAction(providerId,"SCM.CREATE_BRANCH"),"SCM.CREATE_BRANCH"],
    ["Open PR / MR",!providerSupportsAction(providerId,"SCM.OPEN_CHANGE_REQUEST"),"SCM.OPEN_CHANGE_REQUEST"],
    ["Request review",true,"SCM.REQUEST_REVIEW"],
    ["Run checks",true,"SCM.TRIGGER_PIPELINE"],
    ["Release draft",true,"SCM.CREATE_RELEASE_DRAFT"],
    ["Add mirror",true,"PROVIDER.ADD_MIRROR"],
    ["Migrate",true,"PROVIDER.MIGRATE_REPOSITORY"],
    ["Verify migration",true,"PROVIDER.VERIFY_MIGRATION"],
    ["Switch primary",true,"PROVIDER.SWITCH_PRIMARY"],
    ["Merge",true,"SCM.MERGE_CHANGE_REQUEST"]
  ];

  byId("scmActions").innerHTML=actions.map((item)=>
    '<button class="scmBtn '+(item[0]==="Merge"?"danger":"")+
    '" data-action="'+esc(item[2])+'" '+(item[1]?"disabled":"")+'>'+
    esc(item[0])+'<br><span class="code">'+esc(item[2])+'</span></button>'
  ).join("");

  const result=byId("actionResult");
  if(mergeBlocked){
    const reasons=[];
    if(project.security_gate!=="PASS")reasons.push("Security Gate != PASS");
    if(missing.length)reasons.push("missing checks: "+missing.join(", "));
    if(!branch)reasons.push("SCM snapshot unavailable");
    if(branch?.relation_to_main==="DIVERGED")reasons.push("branch diverged");
    result.textContent="Merge BLOCKED · "+reasons.join(" · ");
    result.className="actionResult block";
  }else{
    result.textContent="Merge prerequisites satisfied. Explicit approval is still required.";
    result.className="actionResult ok";
  }

  byId("scmActions").querySelectorAll("button:not(:disabled)").forEach((button)=>{
    button.onclick=async()=>{
      const action=button.dataset.action;
      result.textContent="Planning "+action+"…";
      result.className="actionResult";

      const plan=await planProviderAction(project.project_id,action);
      const reasons=(plan.reasons||[]).join(", ");
      result.textContent=
        plan.action_id+" · "+plan.action+" · "+plan.status+
        (reasons?" · "+reasons:"")+
        " · provider mutation: "+(plan.provider_mutation?"YES":"NO");
      result.className="actionResult "+(plan.allowed?"ok":"block");

      if(!plan.allowed)return;

      let params=null;
      let approved=false;

      if(action==="SCM.CREATE_BRANCH"){
        const branchName=window.prompt(
          "New branch name",
          "feature/"
        );
        if(!branchName)return;

        approved=window.confirm(
          "Create branch '"+branchName+"' from '"+activeBinding.branch+"' via FATHER?"
        );
        if(!approved)return;

        params={
          branch_name:branchName,
          base_ref:activeBinding.branch
        };
        result.textContent="Executing audited branch creation…";
      }else if(action==="SCM.OPEN_CHANGE_REQUEST"){
        const title=window.prompt(
          "Change request title",
          "FATHER: review current project changes"
        );
        if(!title)return;

        const baseRef=window.prompt(
          "Base branch",
          "main"
        );
        if(!baseRef)return;

        const providerConfig=providerById(
          activeBinding?.provider||"github"
        );
        const draftSupported=providerConfig?.draft_change_request_supported!==false;
        approved=window.confirm(
          "Open "+(draftSupported?"draft ":"")+"change request from '"+
          activeBinding.branch+"' to '"+baseRef+"'?"
        );
        if(!approved)return;

        params={
          title,
          head_ref:activeBinding.branch,
          base_ref:baseRef,
          draft:draftSupported
        };
        result.textContent=draftSupported
          ?"Executing audited draft change request creation…"
          :"Executing audited change request creation…";
      }else{
        return;
      }

      result.className="actionResult";

      const executed=await executeProviderAction(
        project.project_id,
        action,
        params
      );
      const executeReasons=(executed.reasons||[]).join(", ");
      result.textContent=
        executed.action_id+" · "+executed.action+" · "+executed.status+
        (executeReasons?" · "+executeReasons:"")+
        " · provider mutation: "+(executed.provider_mutation?"YES":"NO");
      result.className="actionResult "+(
        executed.status==="SUCCEEDED"?"ok":"block"
      );

      if(executed.status==="SUCCEEDED" || executed.status==="SUCCEEDED_EVIDENCE_DEGRADED"){
        await loadLiveState(project);
        await loadRuntimeHistory(project);
        renderWorkspace();
        renderGitMap();
      }
    };
  });
}

async function testProviderConnection(projectId,targetProvider){
  try{
    const response=await fetch("/api/providers/test-connection",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        project_id:projectId,
        target_provider:targetProvider||""
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function rollbackPrimaryProvider(
  projectId,
  targetProvider,
  expectedBindingEtag,
  confirmation
){
  try{
    const response=await fetch("/api/migrations/rollback-primary",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        target_provider:targetProvider,
        expected_binding_etag:expectedBindingEtag,
        confirmation,
        confirm:true
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function switchPrimaryProvider(
  projectId,
  targetProvider,
  expectedBindingEtag,
  confirmation
){
  try{
    const response=await fetch("/api/migrations/switch-primary",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        target_provider:targetProvider,
        expected_binding_etag:expectedBindingEtag,
        confirmation,
        confirm:true
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function submitMigrationCutoverReview(
  projectId,
  targetProvider,
  decision,
  rationale,
  approvedBy,
  expectedEtag
){
  try{
    const response=await fetch("/api/migrations/cutover-review",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        target_provider:targetProvider,
        decision,
        rationale,
        approved_by:approvedBy,
        expected_etag:expectedEtag,
        confirm:true
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function submitMigrationSecurityReview(
  projectId,
  targetProvider,
  decision,
  rationale,
  reviewedBy,
  expectedEtag
){
  try{
    const response=await fetch("/api/migrations/security-review",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        target_provider:targetProvider,
        decision,
        rationale,
        reviewed_by:reviewedBy,
        expected_etag:expectedEtag,
        confirm:true
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function bindMigrationTarget(
  projectId,
  targetProvider,
  repository,
  branch,
  expectedEtag
){
  try{
    const response=await fetch("/api/migrations/bind",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        target_provider:targetProvider,
        repository,
        branch,
        expected_etag:expectedEtag,
        confirm:true
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function verifyMigrationTarget(projectId,targetProvider){
  try{
    const response=await fetch("/api/migrations/verify",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        target_provider:targetProvider,
        confirm:true
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function planMigration(projectId,targetProvider){
  try{
    const response=await fetch("/api/migrations/plan",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        project_id:projectId,
        target_provider:targetProvider
      })
    });
    if(response.ok)return await response.json();
    const error=await response.json().catch(()=>({}));
    return{
      plan_id:"MIGPLAN-ERROR-"+Date.now(),
      state:"BLOCKED",
      blockers:[error.error||("HTTP_"+response.status)]
    };
  }catch(_error){
    return{
      plan_id:"MIGPLAN-ERROR-"+Date.now(),
      state:"BLOCKED",
      blockers:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function exportEvidencePack(projectId){
  try{
    const response=await fetch("/api/evidence/export",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        confirm:true
      })
    });
    const body=await response.json().catch(()=>({}));
    return{http_status:response.status,...body};
  }catch(_error){
    return{
      status:"BLOCKED",
      errors:["CONTROL_PLANE_API_UNAVAILABLE"]
    };
  }
}

async function handleEvidencePackExport(){
  const project=projectById(selectedProject);
  if(!project)return;
  const devsec=model.devsecopsStates[selectedProject];
  const confirmed=window.confirm(
    "Export immutable Evidence Pack for "+project.project_id+
    "? Current commit-bound DevSecOps state: "+(devsec?.status||"UNKNOWN")+
    ". The pack will be created in the tracked project tree and require a Git commit."
  );
  if(!confirmed)return;

  const result=await exportEvidencePack(project.project_id);
  if(result.status!=="EXPORTED"){
    window.alert(
      (result.status||"BLOCKED")+": "+
      (result.errors||["UNKNOWN_ERROR"]).join(", ")
    );
    return;
  }
  await loadRuntimeHistory(project);
  renderWorkspace();
  window.alert(
    result.pack.evidence_pack_id+
    " · "+result.pack.pack_status+
    " · "+result.export.path+
    " · Git commit required"
  );
}

async function executeProviderAction(projectId,action,params){
  try{
    const response=await fetch("/api/actions/execute",{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "X-FATHER-Action":"confirm"
      },
      body:JSON.stringify({
        project_id:projectId,
        action,
        params,
        confirm:true
      })
    });
    if(response.ok)return await response.json();
    const error=await response.json().catch(()=>({}));
    return{
      action_id:"ACT-ERROR-"+Date.now(),
      project_id:projectId,
      action,
      status:"BLOCKED",
      allowed:false,
      reasons:[error.error||("HTTP_"+response.status)],
      provider_mutation:false
    };
  }catch(_error){
    return{
      action_id:"ACT-ERROR-"+Date.now(),
      project_id:projectId,
      action,
      status:"BLOCKED",
      allowed:false,
      reasons:["CONTROL_PLANE_API_UNAVAILABLE"],
      provider_mutation:false
    };
  }
}

async function planProviderAction(projectId,action){
  try{
    const response=await fetch("/api/actions/plan",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({project_id:projectId,action})
    });
    if(response.ok)return await response.json();
  }catch(_error){}
  return{
    action_id:"ACT-LOCAL-"+Date.now(),
    project_id:projectId,
    action,
    status:"DRAFT",
    allowed:true,
    reasons:["CONTROL_PLANE_API_UNAVAILABLE"],
    provider_mutation:false
  };
}

function renderChecks(state){
  const live=model.liveStates[selectedProject];
  const workflow=(live?.workflow_runs||[])[0];
  const liveRows=[];
  if(workflow){
    liveRows.push({
      name:"Latest provider workflow",
      status:workflow.status==="completed" && workflow.conclusion==="success"?"PASS":
        (workflow.status==="completed"?"FAIL":"RUNNING")
    });
  }
  for(const check of live?.checks||[]){
    liveRows.push({
      name:"Provider: "+check.name,
      status:check.status==="completed" && check.conclusion==="success"?"PASS":
        (check.status==="completed"?"FAIL":"RUNNING")
    });
  }
  const rows=[...(state.checks||[]),...liveRows];
  byId("checks").innerHTML=rows.map((item)=>
    '<div class="check"><span>'+esc(item.name)+'</span>'+
    '<span class="pill '+esc(item.status)+'">'+esc(item.status)+'</span></div>'
  ).join("");
}

function renderGitMap(){
  const branches=model.git.branches||[];
  if(!branches.length){
    byId("gitMap").innerHTML='<div class="empty">No SCM snapshot.</div>';
    return;
  }
  const main=branches.find((item)=>item.branch===model.git.default_branch)||branches[0];
  const features=branches.filter((item)=>item.branch!==main.branch);
  byId("gitMap").innerHTML=
    '<div class="mainBranch"><em>DEFAULT</em><h3>'+esc(main.branch)+'</h3>'+
    '<div class="note">'+esc(model.git.repository||"repository")+'</div></div>'+
    '<div class="branchStack">'+features.map((item)=>
      '<div class="branchCard"><div class="branchCardHead"><b>'+esc(item.branch)+'</b>'+
      '<span class="pill '+(item.relation_to_main==="DIVERGED"?"FAIL":"IN_PROGRESS")+'">'+
      esc(item.relation_to_main||"UNKNOWN")+'</span></div>'+
      '<small>project: '+esc(item.linked_project||"unlinked")+
      ' · ahead '+(item.ahead_by||0)+' · behind '+(item.behind_by||0)+
      ' · change request '+(item.open_pull_request?"open":"none")+'</small></div>'
    ).join("")+'</div>';
}

function renderProviderMatrix(){
  const project=projectById(selectedProject)||{};
  const dev=project.dev_platform||{};
  const bindingEnvelope=model.providerBindings[project.project_id]||{};
  const bindings=bindingEnvelope.bindings||{};
  const primaryBinding=activeDevBinding(project)||{};
  const primary=primaryBinding.provider||dev.primary_provider||"github";
  const targets=new Set(dev.migration_targets||[]);
  const targetBindings=bindings.targets||[];
  const historicalBindings=bindings.historical||[];
  const host=byId("providerMatrix");

  host.innerHTML=(model.providers.providers||[]).map((provider)=>{
    const runtime=providerRuntimeById(provider.id);
    const binding=targetBindings.find((item)=>item.provider===provider.id);
    const rollbackCandidate=binding?.status==="ROLLBACK_CANDIDATE";
    const latestReview=(model.migrationSecurity[project.project_id]?.reviews||[])
      .filter((item)=>item.target_provider===provider.id)
      .slice(-1)[0];
    const latestCutover=(model.migrationCutover[project.project_id]?.approvals||[])
      .filter((item)=>item.target_provider===provider.id)
      .slice(-1)[0];
    const historical=historicalBindings.some(
      (item)=>item.provider===provider.id
    );
    const role=provider.id===primary
      ?"PRIMARY"
      :(historical
        ?"HISTORICAL / ROLLBACK"
        :(targets.has(provider.id)?"MIGRATION TARGET":"AVAILABLE"));
    const writes=(provider.write_capabilities||[]).map((cap)=>
      '<span>'+esc(cap.replace("SCM.",""))+'</span>'
    ).join("");
    const canTarget=provider.id!==primary && runtime?.adapter_loaded;
    const verification=model.migrationVerifications[provider.id];
    const connection=model.providerConnections[provider.id];
    const bindingText=binding
      ?binding.repository+" · "+binding.branch
      :"not bound";
    return '<div class="providerCard '+(provider.id===primary?"primary":"")+'">'+
      '<div class="providerCardHead"><h4>'+esc(provider.name)+'</h4>'+
      '<span class="pill '+(runtime?.adapter_loaded?"PASS":"DRAFT")+'">'+
      esc(provider.adapter_status||"TBD")+'</span></div>'+
      '<small>credential: '+esc(runtime?.credential_configured?"CONFIGURED":"NOT CONFIGURED / PUBLIC READ ONLY")+'</small>'+
      '<small>binding: '+esc(bindingText)+'</small>'+
      '<div class="providerCaps">'+
        (provider.capabilities||[]).slice(0,4).map((cap)=>'<span>'+esc(cap)+'</span>').join("")+
        writes+
      '</div>'+
      '<div class="providerRole">'+role+'</div>'+
      (connection
        ?'<div class="providerConnectionState '+stateClass(connection.status)+'">'+
          'CONNECT '+esc(connection.status)+
          (connection.head_sha?' · '+esc(String(connection.head_sha).slice(0,8)):'')+
          '</div>'
        :'')+
      (verification
        ?'<div class="providerVerifyState '+(verification.status==="PASS"?"pass":"blocked")+'">'+
          esc(verification.status)+
          ' · branch '+esc(verification.verification?.state||"—")+
          ' · refs '+esc(verification.ref_parity?.state||"—")+
          ' · access '+esc(verification.access_policy?.state||"—")+
          '</div>'
        :'')+
      (latestReview
        ?'<div class="providerReviewState '+stateClass(latestReview.decision==="APPROVE"?"PASS":latestReview.decision==="REJECT"?"FAIL":"HOLD")+'">'+
          'SECURITY '+esc(latestReview.decision)+' · '+esc(latestReview.reviewed_by)+
          '</div>'
        :'')+
      (latestCutover
        ?'<div class="providerCutoverState '+stateClass(latestCutover.decision==="APPROVE"?"PASS":latestCutover.decision==="CANCEL"?"FAIL":"HOLD")+'">'+
          'CUTOVER '+esc(latestCutover.decision)+' · '+esc(latestCutover.approved_by)+
          '</div>'
        :'')+
      (provider.id===primary
        ?'<div class="providerActionRow">'+
          '<button class="providerConnectionAction" data-provider="'+esc(provider.id)+'">Test connection</button>'+
          '</div>'
        :'')+
      (canTarget
        ?'<div class="providerActionRow">'+
          '<button class="providerConnectionAction" data-provider="'+esc(provider.id)+'">Test connection</button>'+
          '<button class="providerAction" data-provider="'+esc(provider.id)+'">Plan</button>'+
          '<button class="providerBindAction" data-provider="'+esc(provider.id)+'">'+
            (binding?"Edit binding":"Bind target")+
          '</button>'+
          '<button class="providerVerifyAction" data-provider="'+esc(provider.id)+'" '+(binding?"":"disabled")+'>Verify parity</button>'+
          '<button class="providerSecurityAction" data-provider="'+esc(provider.id)+'" '+(binding?"":"disabled")+'>Security review</button>'+
          '<button class="providerCutoverAction" data-provider="'+esc(provider.id)+'" '+(latestReview?.decision==="APPROVE"?"":"disabled")+'>Cutover gate</button>'+
          '<button class="providerSwitchAction" data-provider="'+esc(provider.id)+'" '+(latestCutover?.decision==="APPROVE"?"":"disabled")+'>Switch primary</button>'+
          (rollbackCandidate
            ?'<button class="providerRollbackAction danger" data-provider="'+esc(provider.id)+'">Rollback primary</button>'
            :'')+
          '</div>'
        :'')+
      '</div>';
  }).join("");

  host.querySelectorAll(".providerConnectionAction").forEach((button)=>{
    button.onclick=async()=>{
      const target=button.dataset.provider;
      const isPrimary=target===primary;
      const binding=isPrimary
        ?(model.providerBindings[project.project_id]?.bindings?.primary||null)
        :(model.providerBindings[project.project_id]?.bindings?.targets||[])
          .find((item)=>item.provider===target);
      if(!binding){
        window.alert("Provider binding is not configured.");
        return;
      }
      const output=byId("actionResult");
      output.textContent="Testing "+target+" repository/branch access…";
      output.className="actionResult";
      const tested=await testProviderConnection(
        project.project_id,
        isPrimary?"":target
      );
      model.providerConnections[target]=tested;
      if(tested.status==="PASS"){
        output.textContent=
          "CONNECT PASS · "+target+" · "+
          tested.repository+" / "+tested.branch+
          " · HEAD "+String(tested.head_sha||"").slice(0,12)+
          " · evidence "+(tested.evidence?.evidence_id||"captured");
        output.className="actionResult ok";
      }else{
        output.textContent=
          "CONNECT "+(tested.status||"FAIL")+" · "+target+" · "+
          (tested.errors||["UNKNOWN_ERROR"]).join(", ");
        output.className="actionResult block";
      }
      await loadRuntimeHistory(project);
      renderProviderMatrix();
    };
  });

  host.querySelectorAll(".providerAction").forEach((button)=>{
    button.onclick=async()=>{
      const target=button.dataset.provider;
      const result=byId("actionResult");
      result.textContent="Planning migration to "+target+"…";
      result.className="actionResult";
      const plan=await planMigration(project.project_id,target);
      model.migrationPlans[target]=plan;
      result.textContent=
        plan.plan_id+" · "+plan.source_provider+" → "+plan.target_provider+
        " · "+plan.state+
        (plan.blockers?.length?" · blockers: "+plan.blockers.join(", "):"");
      result.className="actionResult "+(plan.state==="READY"?"ok":"block");
      await loadRuntimeHistory(project);
      renderInspector(stageState(project.project_id));
      renderProviderMatrix();
    };
  });

  host.querySelectorAll(".providerBindAction").forEach((button)=>{
    button.onclick=async()=>{
      const target=button.dataset.provider;
      const provider=providerById(target);
      const current=(model.providerBindings[project.project_id]?.bindings?.targets||[])
        .find((item)=>item.provider===target);
      const repository=window.prompt(
        (provider?.repository_binding_format||"Target repository binding"),
        current?.repository||""
      );
      if(!repository)return;
      const targetBranch=window.prompt(
        "Target branch",
        current?.branch||project.branch||"main"
      );
      if(!targetBranch)return;
      const envelope=model.providerBindings[project.project_id]||{};
      if(!envelope.etag){
        window.alert("Binding ETag unavailable. Refresh FATHER.");
        return;
      }
      const confirmed=window.confirm(
        "Bind "+target+" → "+repository+" / "+targetBranch+
        "? This changes tracked project configuration and requires a Git commit."
      );
      if(!confirmed)return;

      const output=byId("actionResult");
      output.textContent="Binding migration target "+target+"…";
      output.className="actionResult";
      const bound=await bindMigrationTarget(
        project.project_id,
        target,
        repository,
        targetBranch,
        envelope.etag
      );
      if(bound.status!=="APPLIED"){
        output.textContent=
          (bound.status||"BLOCKED")+" · "+
          (bound.errors||["UNKNOWN_ERROR"]).join(", ");
        output.className="actionResult block";
        return;
      }
      await loadRuntimeHistory(project);
      output.textContent=
        "BOUND · "+target+" · ETag "+bound.etag.slice(0,12)+
        " · tracked config changed · Git commit required";
      output.className="actionResult ok";
      renderProviderMatrix();
    };
  });

  host.querySelectorAll(".providerVerifyAction:not(:disabled)").forEach((button)=>{
    button.onclick=async()=>{
      const target=button.dataset.provider;
      const confirmed=window.confirm(
        "Read source and "+target+
        " now and verify branch HEAD parity? Evidence will be stored."
      );
      if(!confirmed)return;
      const output=byId("actionResult");
      output.textContent="Verifying migration parity with "+target+"…";
      output.className="actionResult";
      const verified=await verifyMigrationTarget(
        project.project_id,
        target
      );
      model.migrationVerifications[target]=verified;
      if(verified.status==="PASS"){
        output.textContent=
          verified.verification.verification_id+
          " · PASS · HEAD "+
          verified.verification.source_head_sha+
          " · branch parity PASS · ref parity "+verified.ref_parity.state+
          " · switch-primary BLOCKED pending access/security/cutover evidence";
        output.className="actionResult ok";
      }else{
        output.textContent=
          (verified.verification?.verification_id||"VERIFY")+
          " · "+(verified.status||"BLOCKED")+" · "+
          ([...(verified.verification?.blockers||[]),...(verified.ref_parity?.blockers||[])] .length
            ?[...(verified.verification?.blockers||[]),...(verified.ref_parity?.blockers||[])].join(", ")
            :(verified.errors||["UNKNOWN_ERROR"]).join(", "));
        output.className="actionResult block";
      }
      await loadRuntimeHistory(project);
      renderProviderMatrix();
    };
  });

  host.querySelectorAll(".providerSecurityAction:not(:disabled)").forEach((button)=>{
    button.onclick=async()=>{
      const target=button.dataset.provider;
      const envelope=model.migrationSecurity[project.project_id]||{};
      if(!envelope.etag){
        window.alert("Security review ETag unavailable. Refresh FATHER.");
        return;
      }
      const decision=(window.prompt(
        "Security decision: APPROVE, HOLD or REJECT",
        "HOLD"
      )||"").trim().toUpperCase();
      if(!["APPROVE","HOLD","REJECT"].includes(decision)){
        window.alert("Invalid decision.");
        return;
      }
      const rationale=window.prompt(
        "Security rationale (minimum 20 characters)",
        ""
      );
      if(!rationale)return;
      const reviewer=window.prompt(
        "Reviewed by",
        "Information Security Specialist"
      );
      if(!reviewer)return;
      const confirmed=window.confirm(
        "Record "+decision+" security review for migration to "+target+
        "? FATHER will re-verify current technical evidence first."
      );
      if(!confirmed)return;

      const output=byId("actionResult");
      output.textContent="Re-verifying and recording security review…";
      output.className="actionResult";
      const reviewed=await submitMigrationSecurityReview(
        project.project_id,
        target,
        decision,
        rationale,
        reviewer,
        envelope.etag
      );
      if(reviewed.status!=="APPLIED"){
        output.textContent=
          (reviewed.status||"BLOCKED")+" · "+
          (reviewed.errors||["UNKNOWN_ERROR"]).join(", ");
        output.className="actionResult block";
        return;
      }
      await loadRuntimeHistory(project);
      output.textContent=
        reviewed.review.review_id+" · SECURITY "+reviewed.decision+
        " · tracked review changed · Git commit required"+
        (reviewed.cutover_blockers?.length
          ?" · cutover blockers: "+reviewed.cutover_blockers.join(", ")
          :"");
      output.className=
        "actionResult "+(reviewed.decision==="APPROVE"?"ok":"block");
      renderProviderMatrix();
    };
  });

  host.querySelectorAll(".providerCutoverAction:not(:disabled)").forEach((button)=>{
    button.onclick=async()=>{
      const target=button.dataset.provider;
      const envelope=model.migrationCutover[project.project_id]||{};
      if(!envelope.etag){
        window.alert("Cutover ETag unavailable. Refresh FATHER.");
        return;
      }
      const decision=(window.prompt(
        "Cutover decision: APPROVE, HOLD or CANCEL",
        "HOLD"
      )||"").trim().toUpperCase();
      if(!["APPROVE","HOLD","CANCEL"].includes(decision)){
        window.alert("Invalid decision.");
        return;
      }
      const rationale=window.prompt(
        "Cutover rationale (minimum 20 characters)",
        ""
      );
      if(!rationale)return;
      const approver=window.prompt(
        "Approved by",
        "Project Owner"
      );
      if(!approver)return;
      const confirmed=window.confirm(
        "Record "+decision+" cutover decision for "+target+
        "? APPROVE will re-verify current evidence and security review freshness."
      );
      if(!confirmed)return;

      const output=byId("actionResult");
      output.textContent="Validating cutover gate…";
      output.className="actionResult";
      const reviewed=await submitMigrationCutoverReview(
        project.project_id,
        target,
        decision,
        rationale,
        approver,
        envelope.etag
      );
      if(reviewed.status!=="APPLIED"){
        output.textContent=
          (reviewed.status||"BLOCKED")+" · "+
          (reviewed.errors||["UNKNOWN_ERROR"]).join(", ");
        output.className="actionResult block";
        return;
      }
      await loadRuntimeHistory(project);
      output.textContent=
        reviewed.approval.approval_id+" · CUTOVER "+reviewed.decision+
        " · tracked approval changed · Git commit required"+
        (reviewed.switch_primary_eligible
          ?" · switch-primary gate READY (execution still separate)"
          :" · switch-primary BLOCKED");
      output.className=
        "actionResult "+(reviewed.decision==="APPROVE"?"ok":"block");
      renderProviderMatrix();
    };
  });

  host.querySelectorAll(".providerRollbackAction").forEach((button)=>{
    button.onclick=async()=>{
      const target=button.dataset.provider;
      const envelope=model.providerBindings[project.project_id]||{};
      if(!envelope.etag){
        window.alert("Binding ETag unavailable. Refresh FATHER.");
        return;
      }

      const confirmation=
        "ROLLBACK_PRIMARY:"+project.project_id+":"+target;
      const typed=window.prompt(
        "EMERGENCY HIGH IMPACT ACTION. Type exactly:\n"+confirmation,
        ""
      );
      if(typed!==confirmation){
        window.alert("Rollback cancelled: confirmation did not match.");
        return;
      }

      const confirmed=window.confirm(
        "Restore preserved rollback provider "+target+
        "? FATHER will test repository/branch connectivity before changing primary."
      );
      if(!confirmed)return;

      const output=byId("actionResult");
      output.textContent=
        "Testing rollback target and restoring previous primary…";
      output.className="actionResult";

      const rolled=await rollbackPrimaryProvider(
        project.project_id,
        target,
        envelope.etag,
        confirmation
      );
      if(
        rolled.status!=="ROLLED_BACK" &&
        rolled.status!=="ROLLED_BACK_EVIDENCE_DEGRADED"
      ){
        output.textContent=
          (rolled.status||"BLOCKED")+" · "+
          (rolled.errors||["UNKNOWN_ERROR"]).join(", ");
        output.className="actionResult block";
        return;
      }

      model.migrationVerifications={};
      model.providerConnections={};
      await loadRuntimeHistory(project);
      await loadLiveState(project);
      output.textContent=
        rolled.status+
        " · restored "+esc(rolled.primary?.provider||target)+
        (rolled.post_rollback_status==="PASS"
          ?" · post-rollback live evidence PASS"
          :" · POST-ROLLBACK EVIDENCE DEGRADED")+
        " · Git commit required";
      output.className=
        "actionResult "+(
          rolled.status==="ROLLED_BACK"?"ok":"block"
        );
      render();
    };
  });

  host.querySelectorAll(".providerSwitchAction:not(:disabled)").forEach((button)=>{
    button.onclick=async()=>{
      const target=button.dataset.provider;
      const envelope=model.providerBindings[project.project_id]||{};
      if(!envelope.etag){
        window.alert("Binding ETag unavailable. Refresh FATHER.");
        return;
      }

      const confirmation=
        "SWITCH_PRIMARY:"+project.project_id+":"+target;
      const typed=window.prompt(
        "HIGH IMPACT ACTION. Type exactly:\n"+confirmation,
        ""
      );
      if(typed!==confirmation){
        window.alert("Primary switch cancelled: confirmation did not match.");
        return;
      }

      const finalConfirm=window.confirm(
        "Switch FATHER primary provider to "+target+
        "? Current primary will be preserved as historical rollback binding."
      );
      if(!finalConfirm)return;

      const output=byId("actionResult");
      output.textContent="Re-validating cutover evidence and switching primary…";
      output.className="actionResult";

      const switched=await switchPrimaryProvider(
        project.project_id,
        target,
        envelope.etag,
        confirmation
      );
      if(
        switched.status!=="APPLIED" &&
        switched.status!=="APPLIED_POST_CUTOVER_DEGRADED"
      ){
        output.textContent=
          (switched.status||"BLOCKED")+" · "+
          (switched.errors||["UNKNOWN_ERROR"]).join(", ");
        output.className="actionResult block";
        return;
      }

      model.migrationVerifications={};
      await loadRuntimeHistory(project);
      await loadLiveState(project);
      output.textContent=
        switched.status+
        " · primary "+esc(switched.primary?.provider||target)+
        " · rollback preserved"+
        (switched.post_cutover_status!=="PASS"
          ?" · POST-CUTOVER DEGRADED · ROLLBACK RECOMMENDED"+
            (switched.post_cutover?.blockers?.length
              ?" · "+switched.post_cutover.blockers.join(", ")
              :"")
          :" · POST-CUTOVER PASS · refs/access verified")+
        " · Git commit required";
      output.className=
        "actionResult "+
        (switched.status==="APPLIED"?"ok":"block");
      render();
    };
  });

}

byId("evidencePackBtn").onclick=handleEvidencePackExport;
byId("refresh").onclick=async()=>{
  model.liveStates={};
  model.evidenceStates={};
  model.manufacturingEvents={};
  model.traceability={};
  model.devsecopsStates={};
  model.evidencePacks={};
  model.providerBindings={};
  model.migrationSecurity={};
  model.migrationCutover={};
  model.migrationPlans={};
  model.migrationVerifications={};
  await load();
};
load();
