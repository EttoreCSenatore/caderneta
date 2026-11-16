import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useEffect, useState} from 'react';
import {useNavigate} from 'react-router';
import {Carregando, Erro, Vazio} from '../components/ui';
import {api} from '../lib/api';
import type {Notificacao, PreferenciasNotif} from '../lib/tipos';

const quando = (iso: string) => new Date(iso).toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'});
const ROTULO: Record<string, string> = {aviso: 'Aviso', autorizacao: 'Autorização', mensagem: 'Mensagem', nota: 'Nota', falta: 'Faltas', lembrete: 'Lembrete'};

function Preferencias() {
  const qc = useQueryClient();
  const p = useQuery({queryKey: ['notif-prefs'], queryFn: () => api<PreferenciasNotif>('/notificacoes-preferencias')});
  const [f, setF] = useState<PreferenciasNotif | null>(null);
  const [salvo, setSalvo] = useState(false);
  useEffect(() => { if (p.data) setF(p.data); }, [p.data]);
  const salva = useMutation({
    mutationFn: () => api<PreferenciasNotif>('/notificacoes-preferencias', {method: 'PUT', body: f}),
    onSuccess: (r) => { qc.setQueryData(['notif-prefs'], r); setSalvo(true); },
  });
  if (!f) return <Carregando />;
  return (
    <form className="cartao pilha" onSubmit={(e) => { e.preventDefault(); setSalvo(false); salva.mutate(); }}>
      <h2 style={{fontSize: '1.1rem', margin: 0}}>Preferências</h2>
      <label className="linha"><input type="checkbox" checked={f.email} onChange={(e) => setF({...f, email: e.target.checked})} /> Receber um e-mail quando houver novidades</label>
      <p className="suave pequeno" style={{margin: 0}}>Por segurança o e-mail não traz o conteúdo, só avisa que há novidades e leva até aqui. As notificações dentro do app não podem ser desligadas.</p>
      <div className="form-grade">
        <label className="campo">Silêncio a partir de<input type="time" value={f.silencio_inicio} onChange={(e) => setF({...f, silencio_inicio: e.target.value})} /></label>
        <label className="campo">Silêncio até<input type="time" value={f.silencio_fim} onChange={(e) => setF({...f, silencio_fim: e.target.value})} /></label>
      </div>
      <p className="suave pequeno" style={{margin: 0}}>Neste horário os e-mails esperam, e saem juntos quando ele termina.</p>
      <Erro erro={salva.error} />
      <div className="linha"><button className="botao pequeno" disabled={salva.isPending}>Salvar</button>{salvo && <span className="selo verde" role="status">Salvo</span>}</div>
    </form>
  );
}

export default function Notificacoes() {
  const qc = useQueryClient();
  const nav = useNavigate();
  const lista = useQuery({queryKey: ['notificacoes'], queryFn: () => api<Notificacao[]>('/notificacoes'), refetchInterval: 30000});
  const recarrega = () => {
    qc.invalidateQueries({queryKey: ['notificacoes']});
    qc.invalidateQueries({queryKey: ['notificacoes-contagem']});
  };
  const le = useMutation({mutationFn: (n: Notificacao) => api(`/notificacoes/${n.id}/lida`, {method: 'POST'}), onSuccess: recarrega});
  const todas = useMutation({mutationFn: () => api('/notificacoes/lidas', {method: 'POST'}), onSuccess: recarrega});
  const abre = (n: Notificacao) => {
    if (!n.lida) le.mutate(n);
    nav(n.url);
  };
  const naoLidas = lista.data?.filter((n) => !n.lida).length ?? 0;
  return (
    <>
      <div className="topo">
        <h1>Notificações</h1>
        <button className="botao secundario" disabled={!naoLidas || todas.isPending} onClick={() => todas.mutate()}>Marcar todas como lidas</button>
      </div>
      {lista.isLoading && <Carregando />}
      <Erro erro={lista.error} />
      {lista.data?.length === 0 && <Vazio>Nenhuma notificação por enquanto.</Vazio>}
      <div className="pilha">
        {lista.data?.map((n) => (
          <button key={n.id} className="cartao" style={{textAlign: 'left', cursor: 'pointer', borderLeft: n.lida ? undefined : '4px solid var(--azul)'}} onClick={() => abre(n)}>
            <div className="linha entre">
              <strong>{n.titulo}</strong>
              <div className="linha"><span className="selo">{ROTULO[n.tipo] ?? n.tipo}</span><span className="suave pequeno">{quando(n.criado_em)}</span></div>
            </div>
            {n.corpo && <div>{n.corpo}</div>}
          </button>
        ))}
      </div>
      <div style={{marginTop: '1.5rem'}}><Preferencias /></div>
      <p className="suave pequeno">Notificações lidas somem após 90 dias, e as não lidas após 180.</p>
    </>
  );
}
