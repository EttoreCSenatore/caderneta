import {useMutation, useQueries, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Navigate, useNavigate} from 'react-router';
import {Carregando, Erro} from '../components/ui';
import {api} from '../lib/api';
import {useSair} from '../lib/auth';
import {Markdown} from '../lib/markdown';
import type {LegalPendente, TextoLegal} from '../lib/tipos';
import {TelaEntrada} from './Entrar';

/** Primeiro acesso (ou texto novo): a pessoa lê e confirma a política de privacidade e os termos antes de usar o app. */
export default function Aceitar({pendentes}: {pendentes: LegalPendente[]}) {
  const nav = useNavigate();
  const qc = useQueryClient();
  const sair = useSair();
  const [ciente, setCiente] = useState(false);
  const textos = useQueries({queries: pendentes.map((p) => ({queryKey: ['legal', p.doc], queryFn: () => api<TextoLegal>(`/legal/${p.doc}`)}))});
  const aceita = useMutation({
    mutationFn: () => api('/legal/aceitar', {body: {aceites: pendentes.map((p) => ({doc: p.doc, versao: p.versao}))}}),
    onSuccess: async () => {
      await qc.invalidateQueries({queryKey: ['legal-pendentes']});
      nav('/', {replace: true});
    },
  });
  if (!pendentes.length) return <Navigate to="/" replace />;
  return (
    <TelaEntrada titulo="Antes de continuar">
      <p className="suave" style={{margin: 0}}>Leia como seus dados são tratados e as regras de uso. Você pode reler quando quiser, no rodapé do app.</p>
      {textos.some((t) => t.isLoading) && <Carregando />}
      {textos.map((t, i) => t.data && (
        <details key={pendentes[i].doc} className="cartao">
          <summary><strong>{t.data.titulo}</strong> <span className="suave pequeno">versão {t.data.versao}</span></summary>
          {t.data.status === 'rascunho' && <div className="aviso atencao"><div>Versão em revisão jurídica.</div></div>}
          <div className="legal-rolagem"><Markdown texto={t.data.texto} /></div>
        </details>
      ))}
      <label className="linha" style={{flexWrap: 'nowrap', alignItems: 'flex-start'}}>
        <input type="checkbox" checked={ciente} onChange={(e) => setCiente(e.target.checked)} style={{marginTop: '0.3rem'}} />
        <span>Li e estou ciente dos termos de uso e da política de privacidade.</span>
      </label>
      <Erro erro={aceita.error} />
      <button className="botao largo" disabled={!ciente || aceita.isPending} onClick={() => aceita.mutate()}>Continuar</button>
      <button className="botao secundario largo" onClick={() => sair.mutate()} disabled={sair.isPending}>Sair</button>
    </TelaEntrada>
  );
}
