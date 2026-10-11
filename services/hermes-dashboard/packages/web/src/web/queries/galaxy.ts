import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { orpc } from "../lib/api";

export function useGalaxyMap() {
  return useQuery(orpc.galaxy.map.queryOptions());
}

export function useNode(id: number | null) {
  return useQuery({
    ...orpc.galaxy.node.queryOptions({ input: { id: id ?? 0 } }),
    enabled: id !== null,
  });
}

export function useMemory() {
  return useQuery(orpc.galaxy.memory.queryOptions());
}

export function useNotebooks() {
  return useQuery(orpc.galaxy.notebooks.queryOptions());
}

export function useNotebook(id: number | null) {
  return useQuery({
    ...orpc.galaxy.notebook.queryOptions({ input: { id: id ?? 0 } }),
    enabled: id !== null,
  });
}

export function useJarvisStatus() {
  return useQuery({
    ...orpc.jarvis.status.queryOptions(),
    refetchInterval: 15000,
  });
}

function useInvalidating<T extends { onSuccess: () => void }>(
  build: (onSuccess: () => void) => T,
  keys: (() => readonly unknown[])[],
) {
  const queryClient = useQueryClient();
  return useMutation(
    build(() => {
      for (const key of keys) {
        void queryClient.invalidateQueries({ queryKey: key() });
      }
    }),
  );
}

export function useSaveNode() {
  return useInvalidating(
    (onSuccess) => orpc.galaxy.saveNode.mutationOptions({ onSuccess }),
    [orpc.galaxy.key],
  );
}

export function useDeleteNode() {
  return useInvalidating(
    (onSuccess) => orpc.galaxy.deleteNode.mutationOptions({ onSuccess }),
    [orpc.galaxy.key],
  );
}

export function useWriteMemory() {
  return useInvalidating(
    (onSuccess) => orpc.galaxy.writeMemory.mutationOptions({ onSuccess }),
    [orpc.galaxy.key],
  );
}

export function useForgetMemory() {
  return useInvalidating(
    (onSuccess) => orpc.galaxy.forgetMemory.mutationOptions({ onSuccess }),
    [orpc.galaxy.key],
  );
}

export function useCreateNotebook() {
  return useInvalidating(
    (onSuccess) => orpc.galaxy.createNotebook.mutationOptions({ onSuccess }),
    [orpc.galaxy.key],
  );
}

export function useSaveCell() {
  return useInvalidating(
    (onSuccess) => orpc.galaxy.saveCell.mutationOptions({ onSuccess }),
    [orpc.galaxy.key],
  );
}

export function useDeleteCell() {
  return useInvalidating(
    (onSuccess) => orpc.galaxy.deleteCell.mutationOptions({ onSuccess }),
    [orpc.galaxy.key],
  );
}

export function useAskJarvis() {
  return useMutation(orpc.jarvis.ask.mutationOptions());
}
