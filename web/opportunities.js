"use strict";
const API = "/api/v1";
const money = new Intl.NumberFormat("en-US", {style:"currency", currency:"USD", maximumFractionDigits:2});
const number = new Intl.NumberFormat("en-US", {maximumFractionDigits:1});
const watchlist = document.querySelector("#watchlist");
const detail = document.querySelector("#detail");
const toast = document.querySelector("#toast");
let items = [];
let selected = null;
let userState = {equity:10000,cash_balance:10000,risk_per_trade_pct:2,max_symbol_exposure_pct:20,max_open_risk_pct:6,symbols:["AAPL","MSFT","NVDA","SPY"]};

function el(tag, className, text) { const node=document.createElement(tag); if(className) node.className=className; if(text!==undefined) node.textContent=text; return node; }
function metric(label, value, tone="") { const node=el("article",`metric ${tone}`); node.append(el("span","",label),el("strong","",value)); return node; }
function showError(message) { toast.textContent=message; toast.hidden=false; }
function statusClass(value) { return String(value).toLowerCase().replaceAll(" ","-").replaceAll("_","-"); }

function renderWatchlist() {
  watchlist.replaceChildren();
  if (!items.length) { const empty=el("div","empty"); empty.append(el("strong","","No recommendations published"),el("p","","The API is healthy, but Phase 14 has not produced an auditable snapshot yet.")); watchlist.append(empty); return; }
  items.forEach((item,index)=>{ const button=el("button","asset"); button.type="button"; button.dataset.symbol=item.symbol; button.setAttribute("aria-label",`Open ${item.symbol} decision`); const top=el("div","asset-top"); top.append(el("strong","",item.symbol),el("span",`pill ${statusClass(item.action)}`,item.action)); const score=el("div","score"); score.append(el("span","","Opportunity score"),el("strong","",`${number.format(item.opportunity_score)}`)); button.append(top,score,el("small","",`${item.lifecycle_status} · confidence ${number.format(item.confidence)}%`)); button.addEventListener("click",()=>renderDetail(item)); watchlist.append(button); if(index===0) renderDetail(item); });
}
function renderDetail(item) {
  selected = item;
  detail.replaceChildren();
  const header=el("header","decision-header"); const left=el("div",""); left.append(el("p","eyebrow",`${item.symbol} · ${item.lifecycle_status}`),el("h2","",item.action),el("p","muted",`Valid until ${new Date(item.valid_until_utc).toLocaleString()}`)); header.append(left,el("div",`confidence ${statusClass(item.lifecycle_status)}`,`${number.format(item.confidence)}% confidence`));
  const levels=el("div","levels"); levels.append(metric("Market price",money.format(item.market_price)),metric("Buy zone",`${money.format(item.buy_zone_low)} – ${money.format(item.buy_zone_high)}`,"accent"),metric("Stop",money.format(item.stop_price),"risk"),metric("Target 1",money.format(item.target_1),"positive"),metric("Target 2",money.format(item.target_2),"positive"),metric("Risk / Reward",`${number.format(item.risk_reward_1)}R · ${number.format(item.risk_reward_2)}R`));
  const scores=el("div","score-grid"); [["Technical",item.technical_score],["Fundamental",item.fundamental_score],["Rule score",item.opportunity_score]].forEach(([label,value])=>{const card=el("article","score-card"); const bar=el("span","bar"); bar.style.setProperty("--score",`${value}%`); card.append(el("span","",label),el("strong","",`${number.format(value)}/100`),bar); scores.append(card);});
  const probability=item.success_probability===null||item.success_probability===undefined?"Not trained":`${number.format(Number(item.success_probability)*100)}%`;
  const hybrid=el("div","levels hybrid-evidence"); hybrid.append(metric("Model probability",probability),metric("Expected R",item.expected_r===null||item.expected_r===undefined?"Unavailable":`${number.format(item.expected_r)}R`),metric("Data confidence",`${number.format(item.confidence)}%`),metric("Model state",item.model_status||"FALLBACK"));
  const drivers=el("section","why"); drivers.append(el("p","eyebrow","HYBRID EVIDENCE"),el("h3","","Why the model thinks this")); const positive=el("p","",`Supports: ${(item.top_positive_drivers||[]).join(", ")||"No calibrated model evidence yet"}`); const negative=el("p","",`Weakens: ${(item.top_negative_drivers||[]).join(", ")||"No calibrated model evidence yet"}`); drivers.append(positive,negative,el("small","muted",`Probability model: ${item.probability_model_version||"v1 rules fallback"} · ${item.calibration_status||"UNAVAILABLE"}`));
  const why=el("section","why"); why.append(el("p","eyebrow","WHY NOW?"),el("h3","","Explainable evidence")); const list=el("ul","rtl"); item.explanations.forEach(text=>list.append(el("li","",text))); why.append(list);
  const warning=el("div","warning",item.actionable ? "Decision-support gate is open; execution remains manual." : "Not actionable: Shadow Mode, stale/insufficient data, or a risk gate is active.");
  detail.append(header,levels,scores,hybrid,drivers,why,warning); renderSizing(); loadDecisionContext(item);
}
function svgEl(tag,attributes={}) { const node=document.createElementNS("http://www.w3.org/2000/svg",tag); Object.entries(attributes).forEach(([key,value])=>node.setAttribute(key,String(value))); return node; }
function chartText(x,y,text,className="chart-label") { const node=svgEl("text",{x,y,class:className}); node.textContent=text; return node; }
function renderChart(bars,item) {
  const chart=document.querySelector("#decision-chart"); chart.replaceChildren();
  if(!bars.length){chart.append(chartText(450,180,"No price bars available for this window","chart-empty"));return;}
  const ordered=[...bars].reverse(); const values=ordered.map(bar=>Number(bar.close));
  const levels=[Number(item.stop_price),Number(item.buy_zone_low),Number(item.buy_zone_high),Number(item.target_1),Number(item.target_2)];
  const min=Math.min(...values,...levels),max=Math.max(...values,...levels),span=Math.max(.01,max-min),left=48,right=875,top=24,bottom=326;
  const x=index=>left+(right-left)*index/Math.max(1,ordered.length-1); const y=value=>bottom-(value-min)/span*(bottom-top);
  [0,.25,.5,.75,1].forEach(ratio=>{const value=min+span*ratio;chart.append(svgEl("line",{x1:left,y1:y(value),x2:right,y2:y(value),class:"chart-grid"}),chartText(4,y(value)+4,money.format(value)));});
  chart.append(svgEl("rect",{x:left,y:y(Number(item.buy_zone_high)),width:right-left,height:Math.max(2,y(Number(item.buy_zone_low))-y(Number(item.buy_zone_high))),class:"chart-zone"}));
  [[item.stop_price,"chart-stop","STOP"],[item.target_1,"chart-target","T1"],[item.target_2,"chart-target","T2"]].forEach(([value,className,label])=>{chart.append(svgEl("line",{x1:left,y1:y(Number(value)),x2:right,y2:y(Number(value)),class:className}),chartText(right-35,y(Number(value))-6,label));});
  chart.append(svgEl("polyline",{points:values.map((value,index)=>`${x(index)},${y(value)}`).join(" "),class:"chart-price"}));
  document.querySelector("#chart-window").textContent=`${ordered.length} latest 1m bars · ${item.symbol}`;
  const legend=document.querySelector("#chart-legend"); legend.replaceChildren(); [["Close","#4edcc0"],["Buy zone","#4edcc0"],["Stop","#ff7188"],["Targets","#78aefe"]].forEach(([label,color])=>{const key=el("span","legend-key",label);key.style.setProperty("--key",color);legend.append(key);});
}
function renderJournal(history) { const journal=document.querySelector("#recommendation-journal"); journal.replaceChildren(); if(!history.length){journal.append(el("div","empty","No history yet"));return;} history.forEach(item=>{const row=el("article",`journal-item ${statusClass(item.action)}`);const header=el("header");header.append(el("strong","",item.action),el("time","",new Date(item.as_of_utc).toLocaleString()));row.append(header,el("p","",`Score ${number.format(item.opportunity_score)} · confidence ${number.format(item.confidence)}% · ${item.lifecycle_status}`));journal.append(row);}); }
function renderEvaluation(status) { const meter=document.querySelector("#shadow-meter"); meter.max=status.required_sessions; meter.value=status.completed_sessions; meter.textContent=`${status.completed_sessions} of ${status.required_sessions}`; document.querySelector("#shadow-label").textContent=status.promotion_status==="APPROVED"?"DECISION SUPPORT":"LIVE SHADOW MODE"; const metrics=status.evaluated_recommendations?` · ${status.evaluated_recommendations} evaluated · ${number.format(status.hit_rate_pct||0)}% hit rate`:""; document.querySelector("#shadow-progress").textContent=`${status.completed_sessions}/${status.required_sessions} real sessions${metrics}`; const range=status.historical_first_session_date&&status.historical_latest_session_date?` · ${status.historical_first_session_date} → ${status.historical_latest_session_date}`:""; document.querySelector("#historical-progress").textContent=`${status.historical_certified_sessions} certified sessions · ${status.published_backtest_runs} published backtests${range}`; }
function renderModelStatus(model) { document.querySelector("#hybrid-model-status").textContent=`${model.status} · ${model.model_family||"no trained model"} · threshold ${number.format(Number(model.activation_threshold)*100)}%`; document.querySelector("#hybrid-model-reason").textContent=model.promotion_reasons.length?model.promotion_reasons[0]:"Validation gates passed; human approval is still required"; }
function renderAlerts(alerts) { const panel=document.querySelector("#decision-alerts"); panel.replaceChildren(); if(!alerts.length){panel.append(el("div","empty","No decision transitions recorded yet."));return;} alerts.forEach(alert=>{const card=el("article",`decision-alert ${statusClass(alert.severity)}`);const header=el("header");header.append(el("strong","",alert.title),el("time","",new Date(alert.created_at_utc).toLocaleString()));card.append(header,el("p","rtl",alert.message),el("small","",`${alert.symbol} · ${alert.alert_type.replaceAll("_"," ")}`));panel.append(card);}); }
async function loadDecisionContext(item) { try { const end=new Date(item.market_data_time_utc),start=new Date(end.getTime()-5*86400000); const params=new URLSearchParams({symbol:item.symbol,start_utc:start.toISOString(),end_utc:new Date(end.getTime()+60000).toISOString(),source:"alpaca",page_size:"200"}); const [barsResponse,historyResponse]=await Promise.all([fetch(`${API}/market-bars?${params}`),fetch(`${API}/opportunities/${item.symbol}/history?limit=20`)]); if(!barsResponse.ok||!historyResponse.ok) throw new Error("context API failed"); renderChart((await barsResponse.json()).items,item); renderJournal((await historyResponse.json()).items); } catch(error) { renderChart([],item); renderJournal([]); showError(`Decision context unavailable: ${error.message}`); } }
function renderSizing() {
  if(!selected) return;
  const equity=Math.max(0,Number(document.querySelector("#portfolio-equity").value)||0);
  const entry=(Number(selected.buy_zone_low)+Number(selected.buy_zone_high))/2;
  const riskPerShare=Math.max(.01,entry-Number(selected.stop_price));
  const riskLimit=Number(userState.risk_per_trade_pct||2)/100;
  const exposureLimit=Number(userState.max_symbol_exposure_pct||20)/100;
  const cash=Math.max(0,Number(document.querySelector("#portfolio-cash").value)||0);
  const shares=Math.max(0,Math.min(Math.floor(equity*riskLimit/riskPerShare),Math.floor(equity*exposureLimit/entry),Math.floor(cash/entry)));
  document.querySelector("#sizing-symbol").textContent=selected.symbol;
  document.querySelector("#sizing-shares").textContent=number.format(shares);
  document.querySelector("#sizing-risk").textContent=money.format(shares*riskPerShare);
  document.querySelector("#sizing-value").textContent=money.format(shares*entry);
}
function applyUserState(state) { userState=state; document.querySelector("#portfolio-equity").value=state.equity; document.querySelector("#portfolio-cash").value=state.cash_balance; document.querySelector("#portfolio-symbols").value=state.symbols.join(", "); document.querySelector("#save-status").textContent=`Saved locally · ${state.risk_per_trade_pct}% risk per trade · ${state.max_symbol_exposure_pct}% max exposure`; renderSizing(); }
async function loadUserState() { try { const response=await fetch(`${API}/user-state`); if(!response.ok) throw new Error(`API returned ${response.status}`); applyUserState(await response.json()); } catch(error) { document.querySelector("#save-status").textContent="Saved workspace unavailable; simulator is still usable."; showError(`User workspace unavailable: ${error.message}`); } }
async function saveUserState() { const button=document.querySelector("#save-preferences"); const status=document.querySelector("#save-status"); const symbols=[...new Set(document.querySelector("#portfolio-symbols").value.split(",").map(value=>value.trim().toUpperCase()).filter(Boolean))]; button.disabled=true; status.textContent="Saving…"; try { const payload={...userState,equity:Number(document.querySelector("#portfolio-equity").value),cash_balance:Number(document.querySelector("#portfolio-cash").value),symbols}; const response=await fetch(`${API}/user-state`,{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}); const result=await response.json(); if(!response.ok) throw new Error(result.detail||`API returned ${response.status}`); applyUserState(result); status.textContent="Workspace saved. Re-run the decision pipeline after adding a new symbol."; } catch(error) { status.textContent=`Save failed: ${error.message}`; showError(`Could not save workspace: ${error.message}`); } finally { button.disabled=false; } }
async function load() { toast.hidden=true; try { const symbolQuery=userState.symbols.length?`?symbols=${encodeURIComponent(userState.symbols.join(","))}`:""; const [response,evaluationResponse,alertsResponse,modelResponse]=await Promise.all([fetch(`${API}/opportunities${symbolQuery}`,{headers:{Accept:"application/json"}}),fetch(`${API}/decision-evaluation/status`),fetch(`${API}/decision-alerts?limit=20`),fetch(`${API}/decision-model/status`)]); if(!response.ok||!evaluationResponse.ok||!alertsResponse.ok||!modelResponse.ok) throw new Error("one or more decision APIs failed"); const payload=await response.json(); items=payload.items; renderEvaluation(await evaluationResponse.json()); renderAlerts((await alertsResponse.json()).items); renderModelStatus(await modelResponse.json()); document.querySelector("#tracked").textContent=items.length; document.querySelector("#buy-count").textContent=items.filter(x=>x.action==="BUY ZONE").length; document.querySelector("#certified-count").textContent=items.filter(x=>x.lifecycle_status==="CERTIFIED").length; document.querySelector("#fresh-count").textContent=items.filter(x=>new Date(x.valid_until_utc)>new Date()).length; renderWatchlist(); } catch(error) { items=[]; renderWatchlist(); showError(`Opportunity data unavailable: ${error.message}`); } }
document.querySelector("#refresh").addEventListener("click",load);
document.querySelector("#portfolio-equity").addEventListener("input",renderSizing);
document.querySelector("#portfolio-cash").addEventListener("input",renderSizing);
document.querySelector("#save-preferences").addEventListener("click",saveUserState);
loadUserState().finally(load);
