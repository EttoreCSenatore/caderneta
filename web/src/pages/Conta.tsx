import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {Link} from 'react-router';
import {useNovidades} from '../lib/novidades';
import {type FormEvent, useState} from 'react';
import {Carregando, Erro} from '../components/ui';
import {api} from '../lib/api';
import {useMe} from '../lib/auth';
import {limparOffline} from '../lib/offlineApp';

type Sessao = {id: string; atual: boolean; criado_em: string; ultimo_uso: string; ip: string | null; aparelho: string | null};

const quando = (iso: string) => new Date(iso).toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'});

/** Nome curto do aparelho a partir do user agent (sem biblioteca: só o suficiente para a pessoa reconhecer). */
function aparelho(ua: string | null): string {
  if (!ua) return 'Aparelho desconhecido';
  const so = /Android/i.test(ua) ? 'Android' : /iPhone|iPad/i.test(ua) ? 'iPhone/iPad' : /Windows/i.test(ua) ? 'Windows' : /Mac OS/i.test(ua) ? 'Mac' : /Linux/i.test(ua) ? 'Linux' : 'Outro sistema';
  const nav = /Edg\//.test(ua) ? 'Edge' : /Firefox/i.test(ua) ? 'Firefox' : /Chrome/i.test(ua) ? 'Chrome' : /Safari/i.test(ua) ? 'Safari' : 'navegador';
  return `${nav} em ${so}`;
}

function TrocarSenha() {
  const [f, setF] = useState({atual: '', nova: ''});
  const troca = useMutation({
    mutationFn: () => api('/auth/senha/alterar', {body: {senha_atual: f.atual, senha_nova: f.nova}}),
    onSuccess: () => setF({atual: '', nova: ''}),
  });
  const qc = useQueryClient();
  const enviar = (e: FormEvent) => {
    e.preventDefault();
    troca.mutate(undefined, {onSuccess: () => qc.invalidateQueries({queryKey: ['sessoes']})});
  };
  return (
    <form className="cartao pilha" onSubmit={enviar}>
      <h2 style={{margin: 0}}>Trocar a senha</h2>
      <label className="campo">Senha atual<input type="password" autoComplete="current-password" required value={f.atual} onChange={(e) => setF({...f, atual: e.target.value})} /></label>
      <label className="campo">
        Nova senha <span className="dica">(10 caracteres ou mais, com letras e números ou símbolos)</span>
        <input type="password" autoComplete="new-password" required minLength={10} value={f.nova} onChange={(e) => setF({...f, nova: e.target.value})} />
      </label>
      <Erro erro={troca.error} />
      {troca.isSuccess && <div className="aviso ok">Senha trocada. Os outros aparelhos foram desconectados.</div>}
      <div><button className="botao" disabled={troca.isPending}>Trocar senha</button></div>
    </form>
  );
}

function Sessoes() {
  const qc = useQueryClient();
  const q = useQuery({queryKey: ['sessoes'], queryFn: () => api<Sessao[]>('/auth/sessoes')});
  const sairTodos = useMutation({
    mutationFn: async () => {
      await limparOffline();
      return api('/auth/sair-de-todos', {method: 'POST'});
    },
    onSettled: () => {
      qc.clear();
      window.location.assign('/entrar');
    },
  });
  return (
    <div className="cartao pilha">
      <h2 style={{margin: 0}}>Aparelhos conectados</h2>
      <p className="suave" style={{margin: 0}}>Perdeu ou emprestou o celular? Encerre todas as sessões. Isso também cancela os avisos por push de todos os seus aparelhos.</p>
      {q.isLoading && <Carregando />}
      {q.error && <Erro erro={q.error} />}
      <div className="lista">
        {q.data?.map((s) => (
          <div key={s.id} className="item">
            <div style={{flex: 1}}>
              <strong>{aparelho(s.aparelho)}</strong> {s.atual && <span className="selo verde">este aparelho</span>}
              <div className="suave pequeno">Entrou em {quando(s.criado_em)} · último uso {quando(s.ultimo_uso)}{s.ip ? ` · IP ${s.ip}` : ''}</div>
            </div>
          </div>
        ))}
      </div>
      <Erro erro={sairTodos.error} />
      <div>
        <button className="botao secundario" disabled={sairTodos.isPending} onClick={() => confirm('Sair em todos os aparelhos, inclusive neste?') && sairTodos.mutate()}>
          Sair em todos os aparelhos
        </button>
      </div>
    </div>
  );
}

/** Versão do app e link para as Novidades (no celular, o rodapé do menu lateral não aparece). */
function SobreApp() {
  const q = useNovidades();
  return (
    <div className="cartao">
      <h2 style={{marginTop: 0}}>Sobre o app</h2>
      <p className="suave" style={{margin: '0 0 0.75rem'}}>
        Caderneta{q.data ? ` versão ${q.data.versao_atual}` : ''} · <a href="/privacidade" target="_blank" rel="noreferrer">Privacidade</a> ·{' '}
        <a href="/termos" target="_blank" rel="noreferrer">Termos</a>
      </p>
      <Link className="botao secundario" to="/novidades">Ver as novidades</Link>
    </div>
  );
}

export default function Conta() {
  const {data: me} = useMe();
  if (!me) return <Carregando />;
  return (
    <>
      <div className="topo">
        <div>
          <h1>Minha conta</h1>
          <div className="suave">{me.usuario.nome} · {me.usuario.email}</div>
        </div>
      </div>
      <div className="pilha">
        <div className="cartao">
          <h2 style={{marginTop: 0}}>Verificação em duas etapas</h2>
          <p className="suave" style={{margin: 0}}>{me.usuario.totp_ativo ? 'Ativada neste usuário.' : 'Não está ativada. Ela é obrigatória para a equipe da escola.'}</p>
        </div>
        <div className="cartao">
          <h2 style={{marginTop: 0}}>Meus dados e direitos (LGPD)</h2>
          <p className="suave" style={{margin: '0 0 0.75rem'}}>Baixe uma cópia dos seus dados e faça pedidos à escola: correção, eliminação, portabilidade.</p>
          <Link className="botao secundario" to="/meus-dados">Abrir Meus dados</Link>
        </div>
        <TrocarSenha />
        <Sessoes />
        <SobreApp />
      </div>
    </>
  );
}
