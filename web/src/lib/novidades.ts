import {useQuery} from '@tanstack/react-query';
import {useCallback, useState} from 'react';
import {api} from './api';

export type TipoNovidade = 'novo' | 'melhoria' | 'correcao' | 'seguranca';
export type Versao = {versao: string; data: string; titulo: string; itens: {tipo: TipoNovidade; texto: string}[]};
export type Novidades = {versao_atual: string; versoes: Versao[]};

const CHAVE = 'caderneta-novidades-vista';

function lerVista(): string | null {
  try {
    return localStorage.getItem(CHAVE);
  } catch {
    return null;
  }
}

export function useNovidades() {
  return useQuery({queryKey: ['novidades'], queryFn: () => api<Novidades>('/novidades'), staleTime: 60 * 60 * 1000, retry: false});
}

/** Última versão que esta pessoa viu neste aparelho (só conveniência: sem armazenamento, o aviso volta a aparecer). */
export function useVersaoVista() {
  const [vista, setVista] = useState(lerVista);
  const marcar = useCallback((versao: string) => {
    setVista(versao);
    try {
      localStorage.setItem(CHAVE, versao);
    } catch {
      /* sem armazenamento */
    }
  }, []);
  return {vista, marcar};
}
