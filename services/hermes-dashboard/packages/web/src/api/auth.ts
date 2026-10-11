import { runableManagedAuth } from "@runablehq/managed-auth/server";
import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "./database";

/**
 * Operator authentication for the Hermes console.
 *
 * The console carries live controls — governor mode, the kill switch, shared
 * memory — so every surface behind the shell requires a session. Google sign-in
 * runs through the Runable broker (no provider secrets live in this repo);
 * email/password stays enabled so the unit can mint a local operator account
 * without any outbound call.
 */
export const auth = betterAuth({
  basePath: "/api/auth",
  baseURL: process.env.WEBSITE_URL,
  database: drizzleAdapter(db, { provider: "sqlite" }),
  emailAndPassword: { enabled: true, disableSignUp: true },
  secret: process.env.BETTER_AUTH_SECRET,
  trustedOrigins: [
    process.env.WEBSITE_URL,
    ...(process.env.AUTH_TRUSTED_ORIGINS ?? "").split(","),
  ].filter((origin): origin is string => Boolean(origin?.trim())).map((origin) => origin.trim()),
  plugins: [
    ...runableManagedAuth({
      applicationId: process.env.APPLICATION_ID!,
      issuer: process.env.VITE_RUNABLE_AUTH_ISSUER!,
    }),
  ],
});
