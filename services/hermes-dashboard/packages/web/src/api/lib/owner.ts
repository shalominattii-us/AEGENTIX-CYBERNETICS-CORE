/** Owner authorization is server-configured; email must be provider-verified. */
export function isOwner(user: { id: string; email: string; emailVerified: boolean } | null) {
  if (!user) return false;
  const id = process.env.HERMES_OWNER_USER_ID?.trim();
  if (id) return user.id === id;
  const email = process.env.HERMES_OWNER_EMAIL?.trim().toLowerCase();
  return Boolean(email && user.emailVerified && user.email.trim().toLowerCase() === email);
}

export function ownerConfigured() {
  return Boolean(process.env.HERMES_OWNER_USER_ID?.trim() || process.env.HERMES_OWNER_EMAIL?.trim());
}