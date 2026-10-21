const fallbackRegistry={projects:[
{project_id:"FATHER-ACADEMY-OSINT-001",name:"ALINA OSINT ACADEMY",status:"SECURITY_INTAKE",current_stage:"PD-02_INFORMATION_SECURITY",branch:"feature/alina-osint-academy-v01",product_gate:"PASS",security_gate:"IN_PROGRESS",architecture_gate:"BLOCKED"},
{project_id:"LIFE-001",name:"Personal Lifelong Companion",status:"PRODUCT_DISCOVERY",current_stage:"PD-01_PRODUCT_MANAGER",branch:"feature/father-ecosystem-workspace-v03",product_gate:"IN_PROGRESS",security_gate:"NOT_STARTED",architecture_gate:"BLOCKED"}]};
const fallbackProviders={providers:[
{id:"github",name:"GitHub",status:"CONNECTED",adapter_status:"AVAILABLE",capabilities:["REPOSITORIES","BRANCHES","PULL_REQUESTS","ISSUES","CHECKS"]},
{id:"gitlab",name:"GitLab",status:"AVAILABLE",adapter_status:"PLANNED",capabilities:["REPOSITORIES","MERGE_REQUESTS","ISSUES","PIPELINES"]},
{id:"gitverse",name:"GitVerse / SberTech",status:"AVAILABLE",adapter_status:"PLANNED",capabilities:["REPOSITORIES","CODE_REVIEW","TRACKER","CI_CD"]},
{id:"sourcecraft",name:"SourceCraft / Yandex",status:"AVAILABLE",adapter_status:"PLANNED",capabilities:["REPOSITORIES","PULL_REQUESTS","ISSUES","CI_CD"]},
{id:"gitflic",name:"GitFlic",status:"AVAILABLE",adapter_status:"PLANNED",capabilities:["REPOSITORIES","CODE_REVIEW","ISSUES","CI_CD"]},
{id:"azure_devops",name:"Azure DevOps",status:"AVAILABLE",adapter_status:"PLANNED",capabilities:["REPOS","WORK_ITEMS","PIPELINES"]},
{id:"bitbucket",name:"Bitbucket",status:"AVAILABLE",adapter_status:"PLANNED",capabilities:["REPOSITORIES","PULL_REQUESTS","PIPELINES"]},
{id:"forgejo",name:"Forgejo",status:"AVAILABLE",adapter_status:"PLANNED",capabilities:["REPOSITORIES","PULL_REQUESTS","ISSUES","ACTIONS"]},
{id:"gitea",name:"Gitea",status:"AVAILABLE",adapter_status:"PLANNED",capabilities:["REPOSITORIES","PULL_REQUESTS","ISSUES","ACTIONS"]}
]};
const fallbackGit={snapshot_kind:"FALLBACK",repository:"VictorKVS/FATHER-Universal-AI-Engine",default_branch:"main",branches:[
{branch:"main",role:"DEFAULT",relation_to_main:"SELF"},
{branch:"feature/alina-osint-academy-v01",linked_project:"FATHER-ACADEMY-OSINT-001",relation_to_main:"DIVERGED",ahead_by:16,behind_by:3,open_pull_request:false},
{branch:"feature/father-project-registry-v01",linked_project:"FATHER-PLATFORM-PROJECT-REGISTRY",relation_to_main:"AHEAD",ahead_by:17,behind_by:0,open_pull_request:false}]};

const stages={
"FATHER-ACADEMY-OSINT-001":{
description:"Фабрика профессиональной подготовки агентов. Первый профиль — OSINT Specialist; обучение подтверждается evidence и независимой evaluation.",
current:"PD-02",docs:[8,36],evidence:"PARTIAL",score:{Documents:22,Evidence:28,Security:18,DevSecOps:12},
checks:[["Git binding","PASS"],["Unit / integration tests","NOT_RUN"],["SAST","NOT_RUN"],["SCA","NOT_RUN"],["Secret scan","NOT_RUN"],["License scan","NOT_RUN"],["SBOM","NOT_RUN"],["Security review","IN_PROGRESS"]],
items:[
["PD-00","IDEA","Idea Intake","PASS","Product","PASS",1,1,0,"—","Идея зарегистрирована как FATHER-проект. Архитектурные предложения исходного ТЗ сохранены как PROPOSED_NOT_APPROVED.",["PD-001|Idea Card|PASS"],["ALINA OSINT ACADEMY развивается внутри FATHER.","Первый профиль — OSINT Specialist."],["Project registered","Idea gate passed"],["Source baseline надо сохранять до нормализации требований."]],
["PD-01","PRODUCT","Product Manager","PASS","Product Manager","PASS",5,5,8,"TBD","PM сузил задачу до одного доказуемого вертикального цикла обучения: teacher → task → evidence → evaluation → correction → SkillProfile.",["PD-002|Product Brief|PASS","PD-003|Stakeholder Map|PASS","PD-004|Value & Success Metrics|PASS","PD-005|Scope & Non-Goals|PASS","PD-006|Assumption Register|PASS","GATE-PD01|Product Gate|PASS"],["NO EVIDENCE → NO MASTERY.","Первый MVP не включает SFT/DPO/RL.","RAG и UI сами по себе не считаются компетентностью."],["PD-002..006 created","GATE-PD01 passed"],["Узкий vertical slice снижает риск преждевременной платформы.","Skill change важнее размера базы знаний."]],
["PD-02","INFOSEC","Information Security","IN_PROGRESS","ИБ-специалист","NOT_READY",1,6,15,"TBD_BY_SECURITY","Защищается не только информация, но и целостность обучения: student не может менять mastery/evaluation и сам себя сертифицировать.",["PD-007|Security Context|DRAFT","PD-008|Data Classification|NOT_STARTED","PD-009|Authority & Action Matrix|NOT_STARTED","PD-010|Initial Risk Register|NOT_STARTED","PD-011|Security Constraints|NOT_STARTED","PD-011A|Security / Compliance Budget|NOT_STARTED"],["External content = untrusted input.","Student is not trusted by default.","Secrets excluded from repo/RAG/training data.","Runtime failure cannot silently become PASS."],["Security intake opened","PD-007 created"],["SkillProfile и Evaluation — самостоятельные security assets."]],
["DS-02","DEVSECOPS","DevSecOps Security","WAITING","DevSecOps Security","WAITING",0,1,0,"TBD_BY_DEVSECOPS","После классификации и authority matrix требования ИБ переводятся в исполняемые CI/CD, supply-chain и runtime checks.",["SEC-ENG|Executable security gates|NOT_STARTED"],[],[],[]],
["PD-03","COMPLIANCE","Legal / Compliance","NOT_STARTED","Compliance","NOT_READY",0,3,0,"TBD","Применимость определяется после Security Intake.",[],[],[],[]],
["PD-04","BA","Business Analysis","BLOCKED","Business Analyst","BLOCKED",0,6,0,"—","Заблокировано до Security/Compliance.",[],[],[],[]],
["PD-05","SA","System Analysis","BLOCKED","System Analyst","BLOCKED",0,7,0,"—","Заблокировано до BA и security constraints.",[],[],[],[]],
["PD-06","REQ","Requirements Baseline","BLOCKED","Requirements","BLOCKED",0,7,0,"—","Требования после BA/SA.",[],[],[],[]],
["PD-07","REVIEW","Pre-Design Review","BLOCKED","Review Board","BLOCKED",0,2,0,"—","READY_FOR_ARCHITECTURE пока запрещён.",[],[],[],[]],
["ARCH","ARCH","Architecture","BLOCKED","Architect","BLOCKED",0,0,0,"—","Architecture starts only after Pre-Design PASS.",[],[],[],[]],
["DEV","DEV","Development","NOT_STARTED","Development","NOT_READY",0,0,0,"—","Not started.",[],[],[],[]],
["QA","QA / EVAL","QA / Evaluation","NOT_STARTED","QA / Evaluator","NOT_READY",0,0,0,"—","Not started.",[],[],[],[]],
["OPS","OPS","Operations","NOT_STARTED","SRE / Operations","NOT_READY",0,0,0,"—","Not started.",[],[],[],[]]
]},
"LIFE-001":{
description:"Персональный lifelong companion: непрерывность контекста, документов, обязательств и решений на протяжении жизни.",
current:"PD-01",docs:[3,36],evidence:"EARLY",score:{Documents:9,Evidence:10,Security:0,DevSecOps:0},
checks:[["Git binding","NOT_EVALUATED"],["Security review","NOT_RUN"],["DevSecOps checks","NOT_RUN"]],
items:[
["PD-00","IDEA","Idea Intake","PASS","Product","PASS",1,1,0,"—","Long-term vision сохранён, но не принят за MVP.",["PD-001|Idea Card|PASS"],["AGENT ASSISTS / HUMAN DECIDES"],["Idea registered"],["Широкая life vision должна быть отделена от первого slice."]],
["PD-01","PRODUCT","Product Manager","IN_PROGRESS","Product Manager","NOT_READY",2,5,0,"TBD","Первый slice определён как Life Continuity Desk.",["PD-002|Product Brief|PASS","PD-003|Stakeholder Map|PASS","PD-004|Value & Success Metrics|NOT_STARTED","PD-005|Scope & Non-Goals|NOT_STARTED","PD-006|Assumption Register|NOT_STARTED"],["First target = independent adult","Portability + provenance are first-class"],["PD-002 created","PD-003 created"],["Security-cost feedback should enter before architecture."]],
["PD-02","INFOSEC","Information Security","BLOCKED","ИБ-специалист","BLOCKED",0,6,0,"TBD","Waiting for Product Gate.",[],[],[],[]],
["DS-02","DEVSECOPS","DevSecOps Security","BLOCKED","DevSecOps Security","BLOCKED",0,1,0,"TBD","Waiting for Security Intake.",[],[],[],[]],
["PD-03","COMPLIANCE","Legal / Compliance","BLOCKED","Compliance","BLOCKED",0,3,0,"TBD","Not started.",[],[],[],[]],
["PD-04","BA","Business Analysis","BLOCKED","Business Analyst","BLOCKED",0,6,0,"—","Not started.",[],[],[],[]],
["PD-05","SA","System Analysis","BLOCKED","System Analyst","BLOCKED",0,7,0,"—","Not started.",[],[],[],[]],
["PD-06","REQ","Requirements Baseline","BLOCKED","Requirements","BLOCKED",0,7,0,"—","Not started.",[],[],[],[]],
["PD-07","REVIEW","Pre-Design Review","BLOCKED","Review Board","BLOCKED",0,2,0,"—","Architecture blocked.",[],[],[],[]],
["ARCH","ARCH","Architecture","BLOCKED","Architect","BLOCKED",0,0,0,"—","Architecture blocked.",[],[],[],[]],
["DEV","DEV","Development","NOT_STARTED","Development","NOT_READY",0,0,0,"—","Not started.",[],[],[],[]],
["QA","QA / EVAL","QA / Evaluation","NOT_STARTED","QA","NOT_READY",0,0,0,"—","Not started.",[],[],[],[]],
["OPS","OPS","Operations","NOT_STARTED","SRE","NOT_READY",0,0,0,"—","Not started.",[],[],[],[]]
]}};

let model={registry:fallbackRegistry,git:fallbackGit,providers:fallbackProviders},selectedProject="FATHER-ACADEMY-OSINT-001",selectedStage="PD-02",activeTab="overview";
const byId=function(id){return document.getElementById(id)};
const esc=function(v){return String(v==null?"":v).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;")};
const stateClass=function(v){v=String(v||"").toUpperCase();if(["PASS","MERGED"].includes(v))return"pass";if(["IN_PROGRESS","SECURITY_INTAKE","PRODUCT_DISCOVERY","AHEAD"].includes(v))return"progress";if(["FAIL","BLOCKED","DIVERGED"].includes(v))return"blocked";if(["WAITING","NOT_READY","IN_REVIEW"].includes(v))return"waiting";return"idle"};
const project=function(id){return model.registry.projects.find(function(x){return x.project_id===id})};
const branch=function(p){return model.git.branches&&model.git.branches.find(function(x){return x.branch===p.branch})};
const unpack=function(x){return{id:x[0],short:x[1],name:x[2],status:x[3],owner:x[4],gate:x[5],done:x[6],total:x[7],risks:x[8],cost:x[9],analysis:x[10],docs:x[11]||[],decisions:x[12]||[],history:x[13]||[],lessons:x[14]||[]}};
async function readJson(path,fallback){try{const r=await fetch(path,{cache:"no-store"});if(!r.ok)throw new Error("http");return await r.json()}catch(e){return fallback}}
async function load(){model.registry=await readJson("../../projects/registry.json",fallbackRegistry);model.git=await readJson("../../docs/git/current_workspace.snapshot.json",fallbackGit);model.providers=await readJson("../../config/dev_platform/providers.json",fallbackProviders);byId("snapshot").textContent=model.git.snapshot_kind==="POINT_IN_TIME"?"Dev Platform snapshot":"prototype fallback";render()}
function mini(a,b){return'<div class="mini"><span>'+esc(a)+'</span><b>'+esc(b||"—")+'</b></div>'}
function render(){renderProjects();renderWorkspace();renderGitMap();renderProviderMatrix()}
function renderProjects(){const host=byId("projects");host.innerHTML="";model.registry.projects.forEach(function(p){const b=branch(p),card=document.createElement("article");card.className="project"+(p.project_id===selectedProject?" selected":"");card.innerHTML='<div class="projectHead"><div><h3>'+esc(p.name)+'</h3><div class="id">'+esc(p.project_id)+'</div></div><span class="chip '+stateClass(p.status)+'">'+esc(p.status)+'</span></div><div class="miniGrid">'+mini("Stage",p.current_stage)+mini("Product Gate",p.product_gate)+mini("Security",p.security_gate)+mini("Git",b?b.relation_to_main:"NO SNAPSHOT")+'</div>';card.onclick=function(){selectedProject=p.project_id;selectedStage=stages[p.project_id].current;activeTab="overview";render()};host.appendChild(card)})}
function renderWorkspace(){const p=project(selectedProject),d=stages[selectedProject],b=branch(p);if(!p||!d)return;byId("projectId").textContent=p.project_id;byId("projectName").textContent=p.name;byId("projectDescription").textContent=d.description;byId("projectStatus").textContent=p.status;byId("projectStatus").className="chip "+stateClass(p.status);byId("projectBranch").textContent=p.branch||"branch TBD";renderKpis(p,d,b);renderConveyor(d);renderInspector(d);renderScorecards(d);renderGitPanel(p,b);renderScmActions(p,d,b);renderChecks(d)}
function renderKpis(p,d,b){const vals=[["Product Gate",p.product_gate,"PM decision"],["Security Gate",p.security_gate,"InfoSec + DevSecOps"],["Documents",d.docs[0]+" / "+d.docs[1],"pre-design pack"],["Evidence",d.evidence,"no evidence → no pass"],["Git",b?b.relation_to_main:"NO SNAPSHOT",b?("+"+(b.ahead_by||0)+" / -"+(b.behind_by||0)):"external / TBD"]];byId("kpis").innerHTML=vals.map(function(x){return'<div class="kpi"><span>'+esc(x[0])+'</span><b>'+esc(x[1])+'</b><small>'+esc(x[2])+'</small></div>'}).join("")}
function renderConveyor(d){const host=byId("conveyor");host.innerHTML="";d.items.map(unpack).forEach(function(s){const node=document.createElement("button");node.className="stage "+stateClass(s.status)+(s.id===selectedStage?" active":"");node.innerHTML='<small>'+esc(s.id)+'</small><b>'+esc(s.short)+'</b><i>'+esc(s.status)+'</i><div class="stageMeta"><span>DOCS</span><span>'+s.done+"/"+s.total+'</span></div><div class="stageMeta"><span>GATE</span><span>'+esc(s.gate)+'</span></div>';node.onclick=function(){selectedStage=s.id;activeTab="overview";renderConveyor(d);renderInspector(d)};host.appendChild(node)})}
function detail(a,b){return'<div class="detail"><span>'+esc(a)+'</span><b>'+esc(b)+'</b></div>'}
function renderInspector(d){const s=d.items.map(unpack).find(function(x){return x.id===selectedStage})||unpack(d.items[0]);byId("stageTitle").textContent=s.short+" · "+s.name;byId("stageStatus").textContent=s.status;byId("stageStatus").className="chip "+stateClass(s.status);document.querySelectorAll(".tab").forEach(function(t){t.classList.toggle("active",t.dataset.tab===activeTab);t.onclick=function(){activeTab=t.dataset.tab;renderInspector(d)}});if(activeTab==="documents")byId("stageContent").innerHTML=documents(s);else if(activeTab==="analysis")byId("stageContent").innerHTML=analysis(s);else if(activeTab==="security")byId("stageContent").innerHTML=security(s,d);else if(activeTab==="history")byId("stageContent").innerHTML=history(s);else byId("stageContent").innerHTML=overview(s)}
function overview(s){return'<div class="details">'+detail("Owner",s.owner)+detail("Gate",s.gate)+detail("Documents",s.done+" / "+s.total)+detail("Open risks",s.risks)+detail("Cost impact",s.cost)+detail("Lessons",s.lessons.length)+'</div><div class="analysis">'+esc(s.analysis||"No specialist analysis yet.")+'</div>'}
function documents(s){if(!s.docs.length)return'<div class="empty">Документы этапа ещё не созданы.</div>';return'<div class="rows">'+s.docs.map(function(x){const p=x.split("|");return'<div class="row"><span class="code">'+esc(p[0])+'</span><span>'+esc(p[1])+'</span><span class="pill '+esc(p[2])+'">'+esc(p[2])+'</span></div>'}).join("")+'</div>'}
function analysis(s){return'<div class="analysis">'+esc(s.analysis||"No specialist analysis yet.")+'</div><div style="height:12px"></div><em>KEY DECISIONS</em>'+(s.decisions.length?'<div class="rows">'+s.decisions.map(function(x,i){return'<div class="row"><span class="code">DEC-'+String(i+1).padStart(2,"0")+'</span><span>'+esc(x)+'</span><span class="pill PASS">RECORDED</span></div>'}).join("")+'</div>':'<div class="empty">No material decisions yet.</div>')}
function security(s,d){const relevant=["PD-02","DS-02","ARCH","DEV","QA","OPS"].includes(s.id);let body='<div class="details">'+detail("Security status",relevant?s.status:"UPSTREAM / N/A")+detail("Hard blocker",s.status==="BLOCKED"?"YES":"NO")+detail("Evidence rule","NO EVIDENCE → NO PASS")+'</div>';if(!relevant)return body+'<div class="analysis">Исполняемые DevSecOps checks появляются по мере продвижения конвейера.</div>';return body+'<div class="rows">'+d.checks.map(function(x){return'<div class="row"><span class="code">CHECK</span><span>'+esc(x[0])+'</span><span class="pill '+esc(x[1])+'">'+esc(x[1])+'</span></div>'}).join("")+'</div>'}
function history(s){const h=s.history.length?'<div class="rows">'+s.history.map(function(x,i){return'<div class="row"><span class="code">EVT-'+(i+1)+'</span><span>'+esc(x)+'</span><span></span></div>'}).join("")+'</div>':'<div class="empty">No stage events yet.</div>';const l=s.lessons.length?'<div class="rows">'+s.lessons.map(function(x,i){return'<div class="row"><span class="code">LESSON-'+(i+1)+'</span><span>'+esc(x)+'</span><span class="pill DRAFT">OBSERVED</span></div>'}).join("")+'</div>':'<div class="empty">No lessons yet.</div>';return'<em>HISTORY</em>'+h+'<div style="height:13px"></div><em>LESSONS LEARNED</em>'+l}
function renderScorecards(d){byId("scorecards").innerHTML=Object.entries(d.score).map(function(x){return'<div class="scoreRow"><span>'+esc(x[0])+'</span><div class="meter"><i style="width:'+x[1]+'%"></i></div><b>'+x[1]+'%</b></div>'}).join("")}
function renderGitPanel(p,b){const dp=p.dev_platform||{};const provider=(model.providers.providers||[]).find(function(x){return x.id===(dp.primary_provider||"github")});if(!b){byId("gitPanel").innerHTML='<div class="branch">'+esc(provider?provider.name:"Provider TBD")+' · '+esc(p.branch||"No branch")+'</div><div class="warn" style="margin-top:10px">Live SCM snapshot for this repository was not refreshed.</div>';return}const warning=b.relation_to_main==="DIVERGED"?"Ветка впереди и позади main. Это не FAIL, но evidence/merge-readiness требуют актуализации.":"Ветка не отстаёт от default branch в текущем snapshot.";byId("gitPanel").innerHTML='<div class="branch">'+esc(provider?provider.name:"Provider TBD")+' · '+esc(b.branch)+'</div><div class="gitStats"><div><span>STATE</span><b>'+esc(b.relation_to_main)+'</b></div><div><span>AHEAD</span><b>'+(b.ahead_by||0)+'</b></div><div><span>BEHIND</span><b>'+(b.behind_by||0)+'</b></div></div><div class="warn">'+esc(warning)+'</div>'}
function renderScmActions(p,d,b){
  const checks=d.checks||[];
  const required=["SAST","SCA","Secret scan","Security review"];
  const missing=required.filter(function(name){
    const hit=checks.find(function(x){return x[0]===name});
    return !hit || hit[1]!=="PASS";
  });
  const mergeBlocked=(p.security_gate!=="PASS") || missing.length>0 || !b || b.relation_to_main==="DIVERGED";
  const actions=[
    ["Create branch",false,"SCM.CREATE_BRANCH"],
    ["Open PR",false,"SCM.OPEN_CHANGE_REQUEST"],
    ["Request review",false,"SCM.REQUEST_REVIEW"],
    ["Run checks",false,"SCM.TRIGGER_PIPELINE"],
    ["Release draft",false,"SCM.CREATE_RELEASE_DRAFT"],
    ["Add mirror",false,"PROVIDER.ADD_MIRROR"],
    ["Migrate",false,"PROVIDER.MIGRATE_REPOSITORY"],
    ["Verify migration",false,"PROVIDER.VERIFY_MIGRATION"],
    ["Switch primary",true,"PROVIDER.SWITCH_PRIMARY"],
    ["Merge",mergeBlocked,"SCM.MERGE_CHANGE_REQUEST"]
  ];
  byId("scmActions").innerHTML=actions.map(function(a){
    return '<button class="scmBtn '+(a[0]==="Merge"?"danger":"")+'" data-action="'+a[2]+'" '+(a[1]?"disabled":"")+'>'+esc(a[0])+'<br><span class="code">'+esc(a[2])+'</span></button>';
  }).join("");
  const result=byId("actionResult");
  if(mergeBlocked){
    const reasons=[];
    if(p.security_gate!=="PASS")reasons.push("Security Gate != PASS");
    if(missing.length)reasons.push("missing checks: "+missing.join(", "));
    if(!b)reasons.push("Git snapshot unavailable");
    if(b&&b.relation_to_main==="DIVERGED")reasons.push("branch diverged");
    result.textContent="Merge BLOCKED · "+reasons.join(" · ");
    result.className="actionResult block";
  } else {
    result.textContent="Merge policy prerequisites satisfied in prototype snapshot. Explicit approval is still required.";
    result.className="actionResult ok";
  }
  byId("scmActions").querySelectorAll("button:not(:disabled)").forEach(function(btn){
    btn.onclick=function(){
      const id="ACT-"+Date.now();
      result.textContent=id+" · "+btn.dataset.action+" · DRAFT. No provider mutation executed in browser.";
      result.className="actionResult ok";
    };
  });
}
function renderChecks(d){byId("checks").innerHTML=d.checks.map(function(x){return'<div class="check"><span>'+esc(x[0])+'</span><span class="pill '+esc(x[1])+'">'+esc(x[1])+'</span></div>'}).join("")}
function renderGitMap(){const bs=model.git.branches||[],main=bs.find(function(x){return x.branch===model.git.default_branch})||bs[0],features=bs.filter(function(x){return x.branch!==main.branch});byId("gitMap").innerHTML='<div class="mainBranch"><em>DEFAULT</em><h3>'+esc(main.branch)+'</h3><div class="note">'+esc(model.git.repository||"repository")+'</div></div><div class="branchStack">'+features.map(function(b){return'<div class="branchCard"><div class="branchCardHead"><b>'+esc(b.branch)+'</b><span class="pill '+(b.relation_to_main==="DIVERGED"?"FAIL":"IN_PROGRESS")+'">'+esc(b.relation_to_main||"UNKNOWN")+'</span></div><small>project: '+esc(b.linked_project||"unlinked")+' · ahead '+(b.ahead_by||0)+' · behind '+(b.behind_by||0)+' · change request '+(b.open_pull_request?"open":"none")+'</small></div>'}).join("")+'</div>'}
function renderProviderMatrix(){const p=project(selectedProject)||{};const dp=p.dev_platform||{};const primary=dp.primary_provider||"github";const targets=new Set(dp.migration_targets||[]);byId("providerMatrix").innerHTML=(model.providers.providers||[]).map(function(x){const role=x.id===primary?"PRIMARY":targets.has(x.id)?"MIGRATION TARGET":"AVAILABLE";return'<div class="providerCard '+(x.id===primary?"primary":"")+'"><div class="providerCardHead"><h4>'+esc(x.name)+'</h4><span class="pill '+(x.status==="CONNECTED"?"PASS":"DRAFT")+'">'+esc(x.status)+'</span></div><small>adapter: '+esc(x.adapter_status||"TBD")+'</small><div class="providerCaps">'+(x.capabilities||[]).slice(0,5).map(function(c){return"<span>"+esc(c)+"</span>"}).join("")+'</div><div class="providerRole">'+role+'</div></div>'}).join("")}
byId("refresh").onclick=load;load();