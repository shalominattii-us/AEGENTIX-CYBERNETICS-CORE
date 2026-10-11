import { useQuery } from "@tanstack/react-query";
import { orpc } from "../lib/api";

export function useAccess(enabled: boolean) {
  return useQuery({ ...orpc.access.status.queryOptions(), enabled, retry: false });
}