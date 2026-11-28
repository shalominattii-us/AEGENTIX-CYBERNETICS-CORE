const list = document.querySelector("#opportunity-list");
const detail = document.querySelector("#opportunity-detail");
const search = document.querySelector("#opportunity-search");
const typeFilter = document.querySelector("#opportunity-type");
const count = document.querySelector("#opportunity-count");
const status = document.querySelector("#opportunity-status");

let records = [];

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  for (const child of children) node.append(child);
  return node;
}

function formatWhen(value) {
  if (!value) return "No deadline in this sample";
  return value;
}

function filtered() {
  const query = search.value.trim().toLowerCase();
  const type = typeFilter.value;
  return records.filter((record) => {
    if (type && record.opportunityType !== type) return false;
    if (!query) return true;
    return `${record.title} ${record.issuer} ${record.summary} ${record.jurisdiction}`.toLowerCase().includes(query);
  });
}

function renderDetail(record) {
  if (!record) {
    detail.replaceChildren(el("p", { className: "empty", text: "Select a sample row." }));
    return;
  }
  detail.replaceChildren(
    el("p", { className: "kicker", text: record.id }),
    el("h2", { text: record.title }),
    el("p", { className: `status status-${record.status}`, text: record.status }),
    el("dl", { className: "detail-list" }, [
      row("Issuer", record.issuer),
      row("Jurisdiction", record.jurisdiction),
      row("Type", record.opportunityType),
      row("Published", formatWhen(record.publicationDate)),
      row("Deadline", formatWhen(record.deadline)),
      row("Set-aside", "None in this sample"),
      row("Provenance", `${record.provenance.system}. ${record.provenance.note}`),
    ]),
    el("p", { text: record.summary }),
  );
  const selected = location.hash.replace("#", "");
  if (selected !== record.id) history.replaceState(null, "", `#${record.id}`);
}

function row(term, value) {
  return el("div", {}, [el("dt", { text: term }), el("dd", { text: value })]);
}

function renderList() {
  const rows = filtered();
  count.textContent = rows.length === records.length
    ? `${records.length} sample records`
    : `${rows.length} matching · ${records.length} sample records`;
  list.replaceChildren();
  if (!rows.length) {
    list.append(el("li", { className: "empty", text: "No sample rows match that filter." }));
    renderDetail(null);
    return;
  }
  for (const record of rows) {
    const button = el("button", { type: "button", className: "ledger-row" }, [
      el("span", { className: "req-id", text: record.id }),
      el("span", { className: "ledger-title", text: record.title }),
      el("span", { className: "ledger-issuer", text: record.issuer }),
      el("span", { className: `status status-${record.status}`, text: record.status }),
    ]);
    button.addEventListener("click", () => {
      for (const item of list.querySelectorAll(".ledger-row")) item.removeAttribute("aria-current");
      button.setAttribute("aria-current", "true");
      renderDetail(record);
    });
    list.append(el("li", {}, [button]));
  }
  const wanted = location.hash.replace("#", "");
  const match = rows.find((record) => record.id === wanted) ?? rows[0];
  const buttons = [...list.querySelectorAll(".ledger-row")];
  const index = rows.indexOf(match);
  if (buttons[index]) buttons[index].setAttribute("aria-current", "true");
  renderDetail(match);
}

async function load() {
  status.textContent = "Loading the sample snapshot…";
  const response = await fetch("/api/opportunities", { headers: { accept: "application/json" } });
  if (!response.ok) throw new Error("snapshot failed");
  const body = await response.json();
  if (body.fictional !== true || body.label !== "SAMPLE DATA") throw new Error("snapshot was not labeled as sample data");
  records = body.records;
  const types = [...new Set(records.map((record) => record.opportunityType))].sort();
  for (const type of types) typeFilter.append(el("option", { value: type, text: type }));
  status.textContent = `${body.snapshotId}. ${body.records.length} fictional records from the static file. Read only.`;
  renderList();
}

search.addEventListener("input", renderList);
typeFilter.addEventListener("change", renderList);
load().catch(() => {
  status.textContent = "The sample snapshot did not load. The raw file is linked above.";
});
