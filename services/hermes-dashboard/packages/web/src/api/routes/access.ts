import { withUser } from "../middleware/auth";
import { isOwner, ownerConfigured } from "../lib/owner";

export const access = {
  status: withUser.handler(({ context }) => ({
    configured: ownerConfigured(),
    authorized: isOwner(context.user),
    identityId: context.user?.id ?? null,
  })),
};