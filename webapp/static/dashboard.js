// webapp/static/dashboard.js
async function fetchReport() {
  const r = await fetch("/api/report");
  if (!r.ok) {
    document.getElementById("summary").innerText = "No report available. Run the scanner and save to report.json (or report_visual.json).";
    return null;
  }
  const data = await r.json();
  return data.report;
}

function buildSummary(report){
  const el = document.getElementById("summary");
  el.innerHTML = "";
  const t = document.getElementById("targetLabel");
  t.innerText = report.target || "unknown";

  const pOpen = document.createElement("p");
  pOpen.innerHTML = `<strong>Open ports:</strong> ${report.open_ports ? report.open_ports.length : 0}`;
  el.appendChild(pOpen);

  const ts = document.createElement("p");
  ts.innerHTML = `<strong>Timestamp:</strong> ${report.timestamp || "unknown"}`;
  el.appendChild(ts);

  const save = document.createElement("p");
  save.innerHTML = `<strong>Saved paths:</strong> report.json / report_visual.json`;
  el.appendChild(save);
}

function buildBanners(report){
  const pre = document.getElementById("banners");
  if(!report.banners || Object.keys(report.banners).length === 0) {
    pre.innerText = "No banners collected.";
    return;
  }
  let out = "";
  for(const p of Object.keys(report.banners)){
    out += `Port ${p}: ${report.banners[p] || "(no banner)"}\n\n`;
  }
  pre.innerText = out;
}

function buildRaw(report){
  const raw = document.getElementById("rawJson");
  raw.innerText = JSON.stringify(report, null, 2);
}

function buildCveList(report){
  const el = document.getElementById("cveList");
  el.innerHTML = "";
  const cves = report.explanations || {};
  const ports = Object.keys(cves);
  if(ports.length === 0){
    el.innerHTML = "<p>No CVE hints.</p>";
    return;
  }
  for(const p of ports){
    const card = document.createElement("p");
    card.innerHTML = `<strong>Port ${p}:</strong> <br/> ${cves[p].replace(/\n/g,"<br/>")}`;
    el.appendChild(card);
  }
}

function buildPortsChart(report){
  const ctx = document.getElementById("portsChart").getContext("2d");
  const ports = report.open_ports || [];
  const labels = ports.map(p => String(p));
  const dataCounts = ports.map(_=>1);
  if(window._portsChart) window._portsChart.destroy();
  window._portsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Open ports',
        data: dataCounts,
        backgroundColor: labels.map(_=>'rgba(0,255,159,0.6)'),
        borderColor: 'rgba(0,255,159,1)',
        borderWidth: 1
      }]
    },
    options: {
      scales: {
        x: { ticks: { color: '#9aa6b2' } },
        y: { ticks: { color: '#9aa6b2', stepSize: 1 }, beginAtZero:true }
      },
      plugins:{ legend:{ labels:{ color:'#9aa6b2' } } }
    }
  });
}

async function init(){
  const report = await fetchReport();
  if(!report) return;
  buildSummary(report);
  buildBanners(report);
  buildRaw(report);
  buildCveList(report);
  buildPortsChart(report);
  const updated = document.getElementById("updatedAt");
  updated.innerText = `Report target: ${report.target || "unknown"}`;
}

window.addEventListener("load", init);
