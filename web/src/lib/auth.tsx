import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {api, ApiError} from './api';
import type {Me, Papel} from './tipos';

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      try {
        return await api<Me>('/auth/me');
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) return null;
        throw e;
      }
    },
    staleTime: 60_000,
  });
}

/** Papel do perfil ativo (ou null). */
export function usePapel(): Papel | null {
  const {data} = useMe();
  return data?.perfis.find((p) => p.id === data.perfil_ativo)?.papel ?? null;
}

export function useTrocaPerfil() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (perfil_id: string) => api('/auth/perfil', {body: {perfil_id}}),
    onSuccess: () => qc.resetQueries(),
  });
}

export function useSair() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api('/auth/logout', {method: 'POST'}),
    onSettled: () => {
      qc.clear();
      window.location.assign('/entrar');
    },
  });
}
