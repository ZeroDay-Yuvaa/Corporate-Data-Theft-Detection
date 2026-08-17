// ForensiX Recover — client-side interactivity for the educational prototype

function runDemoInvestigation() {
  const btn = document.getElementById("run-demo-btn");
  const pipeline = document.getElementById("demo-pipeline");
  const fill = document.getElementById("demo-progress-fill");
  if (!pipeline || !fill) return;

  btn.disabled = true;
  btn.textContent = "Running Investigation...";

  const steps = pipeline.querySelectorAll(".pipeline-step");
  let i = 0;

  function nextStep() {
    if (i >= steps.length) {
      btn.disabled = false;
      btn.textContent = "Run Demo Investigation";
      return;
    }
    steps[i].classList.add("done");
    steps[i].querySelector(".status").textContent = "Completed";
    i += 1;
    fill.style.width = `${(i / steps.length) * 100}%`;
    setTimeout(nextStep, 450);
  }

  // reset
  steps.forEach(s => { s.classList.remove("done"); s.querySelector(".status").textContent = "Pending"; });
  fill.style.width = "0%";
  setTimeout(nextStep, 300);
}

function filterDeletedFiles(status) {
  const rows = document.querySelectorAll("[data-status]");
  const chips = document.querySelectorAll(".filter-chip");
  chips.forEach(c => c.classList.toggle("active", c.dataset.filter === status));

  rows.forEach(row => {
    if (status === "All" || row.dataset.status === status) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}

function filterTimeline(type) {
  const items = document.querySelectorAll(".timeline-item");
  const chips = document.querySelectorAll(".filter-chip");
  chips.forEach(c => c.classList.toggle("active", c.dataset.filter === type));

  items.forEach(item => {
    if (type === "all" || item.dataset.type === type) {
      item.style.display = "";
    } else {
      item.style.display = "none";
    }
  });
}

function showCorrelationDetail(nodeId) {
  const nodes = document.querySelectorAll(".corr-node");
  nodes.forEach(n => n.classList.toggle("active", n.dataset.id === nodeId));

  const detailPanels = document.querySelectorAll(".corr-detail-panel");
  detailPanels.forEach(panel => {
    panel.style.display = panel.dataset.id === nodeId ? "block" : "none";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const runBtn = document.getElementById("run-demo-btn");
  if (runBtn) runBtn.addEventListener("click", runDemoInvestigation);

  document.querySelectorAll("[data-filter-target='deleted']").forEach(chip => {
    chip.addEventListener("click", () => filterDeletedFiles(chip.dataset.filter));
  });

  document.querySelectorAll("[data-filter-target='timeline']").forEach(chip => {
    chip.addEventListener("click", () => filterTimeline(chip.dataset.filter));
  });

  document.querySelectorAll(".corr-node").forEach(node => {
    node.addEventListener("click", () => showCorrelationDetail(node.dataset.id));
  });

  // Auto-dismiss flash messages after a few seconds
  document.querySelectorAll(".flash").forEach(f => {
    setTimeout(() => { f.style.opacity = "0.3"; }, 4000);
  });
});
