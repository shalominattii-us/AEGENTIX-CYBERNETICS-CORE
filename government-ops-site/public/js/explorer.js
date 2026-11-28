const tabs = [...document.querySelectorAll("[data-stage]")];
const panels = [...document.querySelectorAll("[data-panel]")];

function select(id, focus) {
  for (const tab of tabs) {
    const on = tab.dataset.stage === id;
    tab.setAttribute("aria-selected", on ? "true" : "false");
    tab.tabIndex = on ? 0 : -1;
    if (on && focus) tab.focus();
  }
  for (const panel of panels) panel.hidden = panel.dataset.panel !== id;
  const next = `#${id}`;
  if (location.hash !== next) history.replaceState(null, "", next);
}

for (const [index, tab] of tabs.entries()) {
  tab.addEventListener("click", () => select(tab.dataset.stage ?? "", false));
  tab.addEventListener("keydown", (event) => {
    const key = event.key;
    if (key !== "ArrowDown" && key !== "ArrowUp" && key !== "ArrowRight" && key !== "ArrowLeft" && key !== "Home" && key !== "End") return;
    event.preventDefault();
    let next = index;
    if (key === "Home") next = 0;
    else if (key === "End") next = tabs.length - 1;
    else next = (index + (key === "ArrowDown" || key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    const target = tabs[next];
    if (target?.dataset.stage) select(target.dataset.stage, true);
  });
}

const initial = location.hash.replace("#", "");
if (tabs.some((tab) => tab.dataset.stage === initial)) select(initial, false);
