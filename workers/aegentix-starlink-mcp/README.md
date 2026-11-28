# aegentix-starlink-mcp

Cloudflare Worker that powers:

- `starlink-edge.aegentixcybernetics.com` — unified edge MCP tools
- `starlink-mcp.aegentixcybernetics.com` — federation layer over the ROG Ally `starlink-mini-mcp` tunnel origin

## AAS skills

Read-only Agentic Awesome Skills catalog tools are injected on both hosts:

- `aas_catalog_status`
- `aas_search_skills`
- `aas_get_skill`
- `aas_list_skill_files`
- `aas_read_skill_file`

Catalog source: `https://raw.githubusercontent.com/shalominattii-us/agentic-awesome-skills/main/skills_index.json`

On the mini host, Starlink/mesh tools continue to be served by the local origin; AAS tools are handled at the edge Worker route.

## Deploy

Upload `index.js` as the Worker `aegentix-starlink-mcp` main module, preserve existing bindings (`keep_bindings`), and ensure a zone route:

`starlink-mcp.aegentixcybernetics.com/*` → `aegentix-starlink-mcp`
