import { route, type SiteDeps } from "./route.js";

export default {
  async fetch(request, env): Promise<Response> {
    const deps: SiteDeps = {
      fetchAsset: (assetRequest) => env.ASSETS.fetch(assetRequest),
      limitDemo: async (key) => (await env.DEMO_RATE_LIMITER.limit({ key })).success,
      now: () => Date.now(),
      siteMode: env.SITE_MODE,
    };
    return route(request, deps);
  },
} satisfies ExportedHandler<Env>;
