"use strict";
const API = "/api/v1";
const money = new Intl.NumberFormat("en-US", {style:"currency", currency:"USD", maximumFractionDigits:2});
const number = new Intl.NumberFormat("en-US", {maximumFractionDigits:1});
const watchlist = document.querySelector("#watchlist");
const detail = document.querySelector("#detail");
const toast = document.querySelector("#toast");
let items = [];
let selected = null;

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
  const scores=el("div","score-grid"); [["Technical",item.technical_score],["Fundamental",item.fundamental_score],["Combined",item.opportunity_score]].forEach(([label,value])=>{const card=el("article","score-card"); const bar=el("span","bar"); bar.style.setProperty("--score",`${value}%`); card.append(el("span","",label),el("strong","",`${number.format(value)}/100`),bar); scores.append(card);});
  const why=el("section","why"); why.append(el("p","eyebrow","WHY NOW?"),el("h3","","Explainable evidence")); const list=el("ul","rtl"); item.explanations.forEach(text=>list.append(el("li","",text))); why.append(list);
  const warning=el("div","warning",item.actionable ? "Decision-support gate is open; execution remains manual." : "Not actionable: Shadow Mode, stale/insufficient data, or a risk gate is active.");
  detail.append(header,levels,scores,why,warning); renderSizing();
}
function renderSizing() {
  if(!selected) return;
  const equity=Math.max(0,Number(document.querySelector("#portfolio-equity").value)||0);
  const entry=(Number(selected.buy_zone_low)+Number(selected.buy_zone_high))/2;
  const riskPerShare=Math.max(.01,entry-Number(selected.stop_price));
  const shares=Math.max(0,Math.min(Math.floor(equity*.02/riskPerShare),Math.floor(equity*.20/entry)));
  document.querySelector("#sizing-symbol").textContent=selected.symbol;
  document.querySelector("#sizing-shares").textContent=number.format(shares);
  document.querySelector("#sizing-risk").textContent=money.format(shares*riskPerShare);
  document.querySelector("#sizing-value").textContent=money.format(shares*entry);
}
async function load() { toast.hidden=true; try { const response=await fetch(`${API}/opportunities`,{headers:{Accept:"application/json"}}); if(!response.ok) throw new Error(`API returned ${response.status}`); const payload=await response.json(); items=payload.items; document.querySelector("#tracked").textContent=items.length; document.querySelector("#buy-count").textContent=items.filter(x=>x.action==="BUY ZONE").length; document.querySelector("#certified-count").textContent=items.filter(x=>x.lifecycle_status==="CERTIFIED").length; document.querySelector("#fresh-count").textContent=items.filter(x=>new Date(x.valid_until_utc)>new Date()).length; renderWatchlist(); } catch(error) { items=[]; renderWatchlist(); showError(`Opportunity data unavailable: ${error.message}`); } }
document.querySelector("#refresh").addEventListener("click",load);
document.querySelector("#portfolio-equity").addEventListener("input",renderSizing);
load();
