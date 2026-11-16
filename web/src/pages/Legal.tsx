import {useQuery} from '@tanstack/react-query';
import {Link, useLocation} from 'react-router';
import {Carregando, Erro} from '../components/ui';
import {api} from '../lib/api';
import {useMe} from '../lib/auth';
import {Markdown} from '../lib/markdown';
import type {Escola, TextoLegal} from '../lib/tipos';

export function Encarregado() {
  const {data: me} = useMe();
  const escola = useQuery({queryKey: ['escola'], queryFn: () => api<Escola>('/escola'), enabled: !!me?.perfil_ativo});
  if (!me?.perfil_ativo) return <p className="suave">Entre na sua conta para ver o contato do encarregado da sua escola.</p>;
  const e = escola.data?.encarregado;
  return (
    <div className="cartao">
      <strong>Encarregado de proteção de dados da sua escola</strong>
      <div>{e?.nome || e?.email ? <>{e.nome}{e.nome && e.email ? ' · ' : ''}{e.email && <a href={`mailto:${e.email}`}>{e.email}</a>}</> : 'A escola ainda não informou. Procure a secretaria.'}</div>
    </div>
  );
}

/** Política de privacidade e termos: páginas públicas (dá para ler antes de entrar). */
export default function Legal() {
  const doc = useLocation().pathname === '/termos' ? 'termos' : 'privacidade';
  const q = useQuery({queryKey: ['legal', doc], queryFn: () => api<TextoLegal>(`/legal/${doc}`)});
  return (
    <div className="pagina-legal">
      <Link to="/entrar" className="pequeno">← Voltar</Link>
      {q.isLoading && <Carregando />}
      {q.error && <Erro erro={q.error} />}
      {q.data && (
        <>
          {q.data.status === 'rascunho' && (
            <div className="aviso atencao" role="note"><div>Versão em <strong>revisão jurídica</strong>: o texto ainda pode mudar antes de a escola começar a usar a Caderneta.</div></div>
          )}
          <div className="suave pequeno">Versão {q.data.versao} · <Link to={doc === 'termos' ? '/privacidade' : '/termos'}>{doc === 'termos' ? 'Política de privacidade' : 'Termos de uso'}</Link></div>
          <Markdown texto={q.data.texto} />
          {doc === 'privacidade' && <Encarregado />}
        </>
      )}
    </div>
  );
}
