import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {type FormEvent, useState} from 'react';
import {Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api, baixarArquivo} from '../lib/api';
import {usePapel} from '../lib/auth';
import {dataBR} from '../lib/formato';
import type {PedidoTitular} from '../lib/tipos';
import {ROTULO_STATUS, ROTULO_TIPO, SeloPrazo} from './MeusDados';

function Responder({p, fechar}: {p: PedidoTitular; fechar: () => void}) {
  const qc = useQueryClient();
  const [f, setF] = useState({status: 'atendido', resposta: ''});
  const salva = useMutation({
    mutationFn: () => api(`/pedidos-titulares/${p.id}/responder`, {body: f}),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['pedidos-titulares']});
      qc.invalidateQueries({queryKey: ['pedidos-contagem']});
      fechar();
    },
  });
  return (
    <form className="pilha" onSubmit={(e) => { e.preventDefault(); salva.mutate(); }}>
      <p className="suave" style={{margin: 0}}>Registre o que foi feito. Se não for possível atender (por exemplo, o histórico escolar precisa ser guardado por lei), <strong>explique o motivo</strong>: o titular recebe essa resposta.</p>
      <label className="campo">Situação
        <select value={f.status} onChange={(e) => setF({...f, status: e.target.value})}>
          {['em_analise', 'atendido', 'em_parte', 'negado'].map((s) => <option key={s} value={s}>{ROTULO_STATUS[s]}</option>)}
        </select>
      </label>
      <label className="campo">Resposta ao titular<textarea required minLength={10} maxLength={4000} rows={5} value={f.resposta} onChange={(e) => setF({...f, resposta: e.target.value})} /></label>
      <Erro erro={salva.error} />
      <button className="botao" disabled={salva.isPending}>Salvar resposta</button>
    </form>
  );
}

function Registrar({fechar}: {fechar: () => void}) {
  const qc = useQueryClient();
  const [f, setF] = useState({titular_nome: '', titular_contato: '', canal: 'presencial', tipo: 'acesso', descricao: '', recebido_em: ''});
  const cria = useMutation({
    mutationFn: () => api('/pedidos-titulares', {body: {...f, titular_contato: f.titular_contato || null, recebido_em: f.recebido_em || null}}),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['pedidos-titulares']});
      qc.invalidateQueries({queryKey: ['pedidos-contagem']});
      fechar();
    },
  });
  const enviar = (e: FormEvent) => { e.preventDefault(); cria.mutate(); };
  return (
    <form className="pilha" onSubmit={enviar}>
      <p className="suave" style={{margin: 0}}>Pediu no balcão, por e-mail ou telefone? Registre aqui com a <strong>data em que a escola recebeu</strong>: o prazo de 15 dias conta dela.</p>
      <div className="form-grade">
        <label className="campo">Nome de quem pediu<input required value={f.titular_nome} onChange={(e) => setF({...f, titular_nome: e.target.value})} /></label>
        <label className="campo">Contato <span className="dica">(opcional)</span><input value={f.titular_contato} onChange={(e) => setF({...f, titular_contato: e.target.value})} /></label>
        <label className="campo">Canal<select value={f.canal} onChange={(e) => setF({...f, canal: e.target.value})}><option value="presencial">Presencial</option><option value="email">E-mail</option><option value="telefone">Telefone</option><option value="outro">Outro</option></select></label>
        <label className="campo">Assunto<select value={f.tipo} onChange={(e) => setF({...f, tipo: e.target.value})}>{Object.entries(ROTULO_TIPO).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        <label className="campo">Recebido em <span className="dica">(vazio = hoje)</span><input type="date" max={new Date().toISOString().slice(0, 10)} value={f.recebido_em} onChange={(e) => setF({...f, recebido_em: e.target.value})} /></label>
      </div>
      <label className="campo">O que foi pedido<textarea required minLength={10} maxLength={2000} rows={3} value={f.descricao} onChange={(e) => setF({...f, descricao: e.target.value})} /></label>
      <Erro erro={cria.error} />
      <button className="botao" disabled={cria.isPending}>Registrar pedido</button>
    </form>
  );
}

export default function PedidosTitulares() {
  const admin = usePapel() === 'admin';
  const q = useQuery({queryKey: ['pedidos-titulares'], queryFn: () => api<PedidoTitular[]>('/pedidos-titulares')});
  const [resp, setResp] = useState<PedidoTitular | null>(null);
  const [novo, setNovo] = useState(false);
  const baixa = useMutation({mutationFn: (p: PedidoTitular) => baixarArquivo(`/pedidos-titulares/${p.id}/exportar`, 'dados-do-titular.json')});
  if (q.isLoading) return <Carregando />;
  if (q.error) return <Erro erro={q.error} />;
  return (
    <>
      <div className="topo">
        <div><h1>Pedidos de titulares</h1><div className="suave">Direitos sobre dados pessoais (LGPD, arts. 18 e 19): resposta em até 15 dias</div></div>
        {admin && <button className="botao" onClick={() => setNovo(true)}>+ Registrar pedido recebido fora do app</button>}
      </div>
      {!admin && <div className="aviso atencao" style={{marginBottom: '1rem'}}>Você pode acompanhar os pedidos. Quem responde e gera os arquivos é a direção.</div>}
      {q.data?.length === 0 && <Vazio>Nenhum pedido até agora.</Vazio>}
      <div className="lista">
        {q.data?.map((p) => (
          <div key={p.id} className="cartao pilha">
            <div className="linha entre"><strong>{ROTULO_TIPO[p.tipo]}{p.aluno ? ` · ${p.aluno}` : ''}</strong><SeloPrazo p={p} /></div>
            <div className="suave pequeno">
              {p.solicitante?.nome ?? 'Titular não identificado'}{p.solicitante?.email ? ` (${p.solicitante.email})` : ''} · canal: {p.canal} · recebido em {dataBR(p.recebido_em.slice(0, 10))} · prazo {dataBR(p.prazo_em.slice(0, 10))}
            </div>
            <div>{p.descricao}</div>
            {p.resposta && <div className="aviso ok">Resposta: {p.resposta}</div>}
            {admin && (
              <div className="linha">
                {p.status !== 'atendido' && p.status !== 'em_parte' && p.status !== 'negado' && <button className="botao pequeno" onClick={() => setResp(p)}>Responder</button>}
                {(p.aluno_id || p.solicitante) && <button className="botao secundario pequeno" disabled={baixa.isPending} onClick={() => baixa.mutate(p)}>Gerar arquivo de dados</button>}
              </div>
            )}
          </div>
        ))}
      </div>
      <Erro erro={baixa.error} />
      <Modal titulo="Responder pedido" aberto={!!resp} fechar={() => setResp(null)}>{resp && <Responder p={resp} fechar={() => setResp(null)} />}</Modal>
      <Modal titulo="Registrar pedido recebido fora do app" aberto={novo} fechar={() => setNovo(false)} largo>{novo && <Registrar fechar={() => setNovo(false)} />}</Modal>
    </>
  );
}
