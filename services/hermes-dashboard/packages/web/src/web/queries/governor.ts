import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { orpc } from "../lib/api";

/** Full control-plane snapshot, polled so telemetry stays current. */
export function useSnapshot() {
  return useQuery({
    ...orpc.governor.snapshot.queryOptions(),
    refetchInterval: 5000,
  });
}

export function useAudit(limit = 40) {
  return useQuery({
    ...orpc.governor.audit.queryOptions({ input: { limit } }),
    refetchInterval: 5000,
  });
}

/** Invalidates every governor query after a control action. */
function useGovernorMutation<TInput, TOutput>(
  options: (onSuccess: () => void) => {
    mutationFn: (input: TInput) => Promise<TOutput>;
    onSuccess: () => void;
  },
) {
  const queryClient = useQueryClient();
  return useMutation(
    options(() => {
      void queryClient.invalidateQueries({ queryKey: orpc.governor.key() });
    }),
  );
}

export function useSetKillSwitch() {
  return useGovernorMutation((onSuccess) =>
    orpc.governor.setKillSwitch.mutationOptions({ onSuccess }),
  );
}

export function useSetMode() {
  return useGovernorMutation((onSuccess) =>
    orpc.governor.setMode.mutationOptions({ onSuccess }),
  );
}

export function useSetProofGate() {
  return useGovernorMutation((onSuccess) =>
    orpc.governor.setProofGate.mutationOptions({ onSuccess }),
  );
}

export function useSetEndpoint() {
  return useGovernorMutation((onSuccess) =>
    orpc.governor.setEndpoint.mutationOptions({ onSuccess }),
  );
}

export function useSetLimitEnforced() {
  return useGovernorMutation((onSuccess) =>
    orpc.governor.setLimitEnforced.mutationOptions({ onSuccess }),
  );
}

export function useResetWindow() {
  return useGovernorMutation((onSuccess) =>
    orpc.governor.resetWindow.mutationOptions({ onSuccess }),
  );
}
