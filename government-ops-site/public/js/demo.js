const form = document.querySelector("#demo-form");
const choices = document.querySelector("#sample-choices");
const text = document.querySelector("#solicitation");
const status = document.querySelector("#demo-status");
const results = document.querySelector("#demo-results");
const submit = document.querySelector("#demo-submit");

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

function setStatus(message, alert) {
  status.textContent = message;
  if (alert) status.setAttribute("role", "alert");
  else status.setAttribute("role", "status");
}

async function loadSamples() {
  setStatus("Loading sample solicitations…", false);
  const response = await fetch("/api/demo/samples", { headers: { accept: "application/json" } });
  if (!response.ok) throw new Error("The sample list did not load.");
  const body = await response.json();
  choices.replaceChildren();
  for (const sample of body.samples) {
    const input = el("input", { type: "radio", name: "sample", value: sample.id, id: `sample-${sample.id}` });
    const title = el("span", { className: "choice-title", text: sample.title });
    const blurb = el("span", { className: "choice-blurb", text: sample.blurb });
    const label = el("label", { className: "choice", for: input.id }, [input, title, blurb]);
    input.addEventListener("change", () => {
      text.value = sample.text;
      results.replaceChildren();
      setStatus("Sample loaded in the browser. Nothing has been sent yet.", false);
    });
    choices.append(label);
  }
  const paste = el("input", { type: "radio", name: "sample", value: "", id: "sample-paste" });
  paste.addEventListener("change", () => {
    text.value = "";
    text.focus();
    setStatus("Paste sample text. It stays in this browser until you run the demo.", false);
  });
  choices.append(el("label", { className: "choice", for: "sample-paste" }, [
    paste,
    el("span", { className: "choice-title", text: "Paste text" }),
    el("span", { className: "choice-blurb", text: "Use your own wording. The Worker does not store it." }),
  ]));
  const first = choices.querySelector("input");
  if (first) {
    first.checked = true;
    text.value = body.samples[0]?.text ?? "";
  }
  setStatus("Choose a sample or paste text, then run the extraction.", false);
}

function pill(label, className) {
  return el("span", { className, text: label });
}

function section(title, kicker) {
  return el("section", { className: "result-block" }, [
    el("p", { className: "kicker", text: kicker }),
    el("h3", { text: title }),
  ]);
}

function list(items, empty) {
  if (!items.length) return el("p", { className: "empty", text: empty });
  const node = el("ul", { className: "plain" });
  for (const item of items) node.append(el("li", { text: item }));
  return node;
}

function render(body) {
  const analysis = body.analysis;
  const mandatory = analysis.requirements.filter((item) => item.mandatory).length;
  const optional = analysis.requirements.length - mandatory;
  const metrics = el("dl", { className: "metrics" });
  for (const [term, value] of [
    ["Requirements", String(analysis.requirements.length)],
    ["Mandatory", String(mandatory)],
    ["Optional", String(optional)],
    ["Confidence", analysis.confidence.toFixed(2)],
    ["Review required", analysis.reviewRequired ? "Yes" : "No"],
    ["Source", body.source === "sample" ? "Labeled sample" : "Pasted text"],
  ]) {
    metrics.append(el("div", {}, [el("dt", { text: term }), el("dd", { text: value })]));
  }

  const requirements = section("Requirements", "parseOpportunity");
  if (!analysis.requirements.length) {
    requirements.append(el("p", { className: "empty", text: "No explicit requirement sentences were extracted." }));
  } else {
    const rows = el("ol", { className: "reqs" });
    for (const requirement of analysis.requirements) {
      rows.append(el("li", {}, [
        el("div", { className: "req-meta" }, [
          el("span", { className: "req-id", text: requirement.id }),
          pill(requirement.mandatory ? "Mandatory" : "Optional", requirement.mandatory ? "pill pill-mandatory" : "pill pill-optional"),
          pill(requirement.category, "pill"),
        ]),
        el("p", { text: requirement.statement }),
      ]));
    }
    requirements.append(rows);
  }

  const context = section("Standards, risks, and outcomes", "Same pass over the sentences");
  context.append(el("h4", { text: "Standards lines" }));
  context.append(list(analysis.standards, "No standards keywords in this text."));
  context.append(el("h4", { text: "Risks" }));
  context.append(list(analysis.risks, "No parser risks were added."));
  context.append(el("h4", { text: "Desired outcomes" }));
  context.append(list(analysis.desiredOutcomes, "No outcome keywords were found."));
  context.append(el("h4", { text: "Fit tags" }));
  context.append(list(analysis.fitTags, "No fit tags were found."));

  const matches = section("Capability match", "matchCapabilities on the sample catalog");
  matches.append(el("p", { className: "note", text: body.capabilityCatalog.disclaimer }));
  if (!body.matches.length) {
    matches.append(el("p", { className: "empty", text: "No matches, because no requirements were extracted." }));
  } else {
    const table = el("div", { className: "match-list" });
    for (const match of body.matches) {
      table.append(el("article", { className: `match match-${match.disposition}` }, [
        pill(match.disposition, `pill pill-${match.disposition}`),
        el("p", { className: "match-score", text: `Score ${match.score.toFixed(2)} · ${match.capabilityId ?? "no catalog id"}` }),
        el("p", { text: match.rationale }),
        el("p", { className: "req-id", text: match.requirementId }),
      ]));
    }
    matches.append(table);
  }

  const spec = body.specification;
  const specification = section("Build specification", spec.specificationId);
  specification.append(el("p", { text: spec.objective }));
  specification.append(el("p", {}, [
    pill(spec.approvalState, "pill pill-draft"),
    el("span", { className: "note", text: " The generator always leaves this as draft." }),
  ]));
  specification.append(el("h4", { text: "Components" }));
  specification.append(list(spec.components, "No components were named."));
  specification.append(el("h4", { text: "Acceptance criteria" }));
  specification.append(list(spec.acceptanceCriteria, "No mandatory requirements, so there are no acceptance criteria."));
  specification.append(el("h4", { text: "Evidence the spine asks to assemble" }));
  specification.append(list(spec.evidenceRequired, "None."));
  specification.append(el("h4", { text: "Execution zones on the specification" }));
  specification.append(list(spec.executionZones, "No zones."));

  const plan = section("Plan", body.plan.planId);
  plan.append(el("p", { className: "blocked-line", text: "externalActionsBlocked is true on this plan." }));
  const tasks = el("ol", { className: "tasks" });
  for (const task of body.plan.tasks) {
    const depends = task.dependsOn.length ? `Depends on ${task.dependsOn.join(", ")}` : "No dependencies";
    tasks.append(el("li", {}, [
      el("div", { className: "req-meta" }, [
        el("span", { className: "req-id", text: task.id }),
        pill(task.kind, "pill"),
        pill(task.executionZone, "pill"),
      ]),
      el("p", { text: task.title }),
      el("p", { className: "note", text: depends }),
    ]));
  }
  plan.append(tasks);

  const hash = section("Content hash", "Illustration only");
  hash.append(el("p", { text: body.contentHash.note }));
  hash.append(el("p", { className: "hash", text: `${body.contentHash.algorithm} ${body.contentHash.hex}` }));
  const copy = el("button", { type: "button", className: "button button-quiet", text: "Copy hash" });
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(body.contentHash.hex);
      setStatus("Hash copied.", false);
    } catch {
      setStatus("The hash is on the page. The browser did not allow clipboard access.", true);
    }
  });
  hash.append(copy);

  const gate = section("Authorization gate", "Always closed on this site");
  gate.append(el("p", { text: "No authorization token is accepted here. Each check below was made with an empty token." }));
  const checks = el("ul", { className: "gate-list" });
  for (const check of body.gate.checks) {
    checks.append(el("li", {}, [
      pill("Blocked", "pill pill-blocked"),
      el("span", { className: "req-id", text: check.action }),
      el("span", { text: check.message }),
    ]));
  }
  gate.append(checks);

  const banner = el("p", { className: "result-banner", text: `${body.label}. ${body.disclaimer}` });
  results.replaceChildren(banner, metrics, requirements, context, matches, specification, plan, hash, gate);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const selected = form.querySelector("input[name=sample]:checked");
  submit.disabled = true;
  setStatus("Running the spine parser on this text…", false);
  results.replaceChildren();
  try {
    const response = await fetch("/api/demo/analyze", {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ sampleId: selected?.value || undefined, text: text.value }),
    });
    const body = await response.json();
    if (!response.ok) {
      setStatus(body.error || "The demo did not complete.", true);
      return;
    }
    render(body);
    setStatus("Demo result is on the page. It was not stored.", false);
  } catch {
    setStatus("The demo request failed before a result was returned.", true);
  } finally {
    submit.disabled = false;
  }
});

loadSamples().catch(() => {
  setStatus("Sample solicitations did not load. You can still paste text.", true);
});
