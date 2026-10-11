import { withUser } from "../middleware/auth";

export const access = {
  status: withUser.handler(({ context }) => ({
    configured: Boolean(process.env.HERMES_OWNER_USER_ID),
    authorized: Boolean(context.user && process.env.HERMES_OWNER_USER_ID === context.user.id),
    identityId: context.user?.id ?? null,
  })),
};