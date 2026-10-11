import { ORPCError } from "@orpc/server";
import { auth } from "../auth";
import { base } from "../__core/app";

/** Optional auth — `context.user` is the session user or null. */
export const withUser = base.use(async ({ context, next }) => {
  const session = await auth.api.getSession({ headers: context.headers });
  return next({
    context: { user: session?.user ?? null, session: session?.session ?? null },
  });
});

/** Protected procedures — rejects unauthenticated calls; `context.user` is non-null. */
export const authed = base.use(async ({ context, next }) => {
  const session = await auth.api.getSession({ headers: context.headers });
  if (!session) throw new ORPCError("UNAUTHORIZED");
  if (!process.env.HERMES_OWNER_USER_ID || session.user.id !== process.env.HERMES_OWNER_USER_ID) {
    throw new ORPCError("FORBIDDEN", { message: "This identity is not bound as the console owner." });
  }
  return next({ context: { user: session.user, session: session.session } });
});
