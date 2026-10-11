import { managedAuthClient } from "@runablehq/managed-auth/client";
import { createAuthClient } from "better-auth/react";

// Both values are injected into the app env and exposed to the browser by Vite.
const config = {
  applicationId: import.meta.env.VITE_APPLICATION_ID,
  issuer: import.meta.env.VITE_RUNABLE_AUTH_ISSUER,
};

export const authClient = createAuthClient({
  // Packaged desktop builds load from file://, so the page origin is not the server there.
  baseURL: import.meta.env.VITE_WEBSITE_URL ?? window.location.origin,
  basePath: "/api/auth",
  plugins: [managedAuthClient(config)],
});
