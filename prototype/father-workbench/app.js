const fallbackRegistry={projects:[]};
const fallbackProviders={providers:[]};
const fallbackGit={snapshot_kind:"FALLBACK",repository:"",default_branch:"main",branches:[]};

let model={
  registry:fallbackRegistry,
  providers:fallbackProviders,
  git:fallbackGit,
  stageStates:{},
  liveStates:{}
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
  if(["IN_PROGRESS","SECURITY_INTAKE","PRODUCT_DISCOVERY","AHEAD"].includes(v))return"progress";
  if(["FAIL","BLOCKED","DIVERGED"].includes(v))return"blocked";
  if(["WAITING","NOT_READY","IN_REVIEW"].includes(v))return"waiting";
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

function stageById(projectId,stageId){
  const state=stageState(projectId);
  return state?.stages?.find((item)=>item.id===stageId)||null;
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
    await loadLiveState(projectById(selectedProject));
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
  byId("projectBranch").textContent=project.branch||"branch TBD";

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
    ["Evidence",state.evidence_status||"—","no evidence → no pass"],
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
  else if(activeTab==="security")host.innerHTML=securityHtml(stage,state);
  else if(activeTab==="history")host.innerHTML=historyHtml(stage);
  else host.innerHTML=overviewHtml(stage);
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
  '<div class="analysis">'+esc(stage.analysis||"No specialist analysis yet.")+'</div>';
}

function documentsHtml(stage){
  const docs=stage.documents?.items||[];
  if(!docs.length)return'<div class="empty">Документы этапа ещё не созданы.</div>';
  return '<div class="rows">'+docs.map((item)=>
    '<div class="row">'+
      '<span class="code">'+esc(item.id)+'</span>'+
      '<span>'+esc(item.title)+'</span>'+
      '<span class="pill '+esc(item.status)+'">'+esc(item.status)+'</span>'+
    '</div>'
  ).join("")+'</div>';
}

function analysisHtml(stage){
  const decisions=stage.decisions||[];
  return '<div class="analysis">'+esc(stage.analysis||"No specialist analysis yet.")+'</div>'+
    '<div style="height:12px"></div><em>KEY DECISIONS</em>'+
    (decisions.length
      ?'<div class="rows">'+decisions.map((item,index)=>
        '<div class="row"><span class="code">DEC-'+String(index+1).padStart(2,"0")+
        '</span><span>'+esc(item)+'</span><span class="pill PASS">RECORDED</span></div>'
      ).join("")+'</div>'
      :'<div class="empty">No material decisions yet.</div>');
}

function securityHtml(stage,state){
  const relevant=["PD-02","DS-02","ARCH","DEV","QA","OPS"].includes(stage.id);
  let html='<div class="details">'+
    detail("Security status",relevant?stage.status:"UPSTREAM / N/A")+
    detail("Hard blocker",stage.status==="BLOCKED"?"YES":"NO")+
    detail("Evidence rule","NO EVIDENCE → NO PASS")+
  '</div>';
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

function historyHtml(stage){
  const history=stage.history||[];
  const lessons=stage.lessons||[];
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
  return '<em>HISTORY</em>'+events+
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

  const actions=[
    ["Create branch",false,"SCM.CREATE_BRANCH"],
    ["Open PR / MR",false,"SCM.OPEN_CHANGE_REQUEST"],
    ["Request review",false,"SCM.REQUEST_REVIEW"],
    ["Run checks",false,"SCM.TRIGGER_PIPELINE"],
    ["Release draft",false,"SCM.CREATE_RELEASE_DRAFT"],
    ["Add mirror",false,"PROVIDER.ADD_MIRROR"],
    ["Migrate",false,"PROVIDER.MIGRATE_REPOSITORY"],
    ["Verify migration",false,"PROVIDER.VERIFY_MIGRATION"],
    ["Switch primary",true,"PROVIDER.SWITCH_PRIMARY"],
    ["Merge",mergeBlocked,"SCM.MERGE_CHANGE_REQUEST"]
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
          "Create branch '"+branchName+"' from '"+project.branch+"' via FATHER?"
        );
        if(!approved)return;

        params={
          branch_name:branchName,
          base_ref:project.branch
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

        approved=window.confirm(
          "Open draft change request from '"+project.branch+"' to '"+baseRef+"'?"
        );
        if(!approved)return;

        params={
          title,
          head_ref:project.branch,
          base_ref:baseRef,
          draft:true
        };
        result.textContent="Executing audited change request creation…";
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

      if(executed.status==="SUCCEEDED"){
        await loadLiveState(project);
        renderWorkspace();
        renderGitMap();
      }
    };
  });
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
  const primary=dev.primary_provider||"github";
  const targets=new Set(dev.migration_targets||[]);
  byId("providerMatrix").innerHTML=(model.providers.providers||[]).map((provider)=>{
    const role=provider.id===primary
      ?"PRIMARY"
      :(targets.has(provider.id)?"MIGRATION TARGET":"AVAILABLE");
    return '<div class="providerCard '+(provider.id===primary?"primary":"")+'">'+
      '<div class="providerCardHead"><h4>'+esc(provider.name)+'</h4>'+
      '<span class="pill '+(provider.status==="CONNECTED"?"PASS":"DRAFT")+'">'+
      esc(provider.status)+'</span></div>'+
      '<small>adapter: '+esc(provider.adapter_status||"TBD")+'</small>'+
      '<div class="providerCaps">'+(provider.capabilities||[]).slice(0,5).map((cap)=>
        '<span>'+esc(cap)+'</span>'
      ).join("")+'</div>'+
      '<div class="providerRole">'+role+'</div></div>';
  }).join("");
}

byId("refresh").onclick=async()=>{
  model.liveStates={};
  await load();
};
load();
