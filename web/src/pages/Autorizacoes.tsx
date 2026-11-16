import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import {dataBR} from '../lib/formato';
import type {AutorizacaoEquipe, AutorizacaoFamilia, PainelAutorizacao, TurmaResumo} from '../lib/tipos';

const quando = (iso: string) => new Date(iso).toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'});
const COR = {autorizado: 'verde', negado: 'vermelho', pendente: 'laranja'} as const;
const VAZIO = {titulo: '', descricao: '', turma_id: '', data_evento: '', prazo: ''};

function Painel({id, fechar}: {id: string | null; fechar: () => void}) {
  const p = useQuery({queryKey: ['autorizacao-painel', id], queryFn: () => api<PainelAutorizacao>(`/autorizacoes/${id}/painel`), enabled: !!id});
  return (
    <Modal titulo="Respostas" aberto={!!id} fechar={fechar} largo>
      {p.isLoading && <Carregando />}
      <Erro erro={p.error} />
      {p.data && (
        <div className="pilha">
          <div className="linha">
            <span className="selo verde">{p.data.autorizado} autorizaram</span>
            <span className="selo vermelho">{p.data.negado} negaram</span>
            <span className="selo laranja">{p.data.pendente} pendentes</span>
          </div>
          <table>
            <thead><tr><th>Aluno</th><th>Situação</th><th>Observação</th></tr></thead>
            <tbody>
              {p.data.alunos.map((a) => (
                <tr key={a.aluno_id}>
                  <td>{a.aluno}</td>
                  <td><span className={`selo ${COR[a.situacao]}`}>{a.situacao}</span>{a.respondido_em && <span className="suave pequeno"> {quando(a.respondido_em)}</span>}</td>
                  <td>{a.observacao ?? ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}

function Familia() {
  const qc = useQueryClient();
  const lista = useQuery({queryKey: ['autorizacoes'], queryFn: () => api<AutorizacaoFamilia[]>('/autorizacoes')});
  const responde = useMutation({
    mutationFn: ({a, autoriza}: {a: AutorizacaoFamilia; autoriza: boolean}) => api(`/autorizacoes/${a.id}/alunos/${a.aluno_id}`, {method: 'PUT', body: {autoriza}}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['autorizacoes']}),
  });
  return (
    <>
      {lista.isLoading && <Carregando />}
      <Erro erro={lista.error} />
      <Erro erro={responde.error} />
      {lista.data?.length === 0 && <Vazio>Nenhuma autorização pedida.</Vazio>}
      <div className="pilha">
        {lista.data?.map((a) => (
          <article key={a.id + a.aluno_id} className="cartao">
            <div className="linha entre">
              <h2 style={{fontSize: '1.15rem', margin: 0}}>{a.titulo}</h2>
              <span className="selo">{a.aluno}</span>
            </div>
            <div className="suave pequeno">
              {a.autor}{a.data_evento && ` · data: ${dataBR(a.data_evento)}`}{a.prazo && ` · responder até ${quando(a.prazo)}`}
            </div>
            <p style={{whiteSpace: 'pre-wrap'}}>{a.descricao}</p>
            {a.resposta && <p><span className={`selo ${a.resposta === 'autorizo' ? 'verde' : 'vermelho'}`}>{a.resposta === 'autorizo' ? 'Você autorizou' : 'Você não autorizou'}</span></p>}
            {a.encerrada ? (
              <span className="selo laranja">Prazo encerrado</span>
            ) : (
              <div className="linha">
                <button className="botao pequeno" disabled={responde.isPending || a.resposta === 'autorizo'} onClick={() => responde.mutate({a, autoriza: true})}>Autorizo</button>
                <button className="botao secundario pequeno" disabled={responde.isPending || a.resposta === 'nao_autorizo'} onClick={() => responde.mutate({a, autoriza: false})}>Não autorizo</button>
              </div>
            )}
          </article>
        ))}
      </div>
    </>
  );
}

function Equipe() {
  const papel = usePapel();
  const qc = useQueryClient();
  const geral = papel === 'admin' || papel === 'coordenacao';
  const lista = useQuery({queryKey: ['autorizacoes'], queryFn: () => api<AutorizacaoEquipe[]>('/autorizacoes')});
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas')});
  const [novo, setNovo] = useState(false);
  const [form, setForm] = useState(VAZIO);
  const [painel, setPainel] = useState<string | null>(null);
  const recarrega = () => qc.invalidateQueries({queryKey: ['autorizacoes']});
  const criar = useMutation({
    mutationFn: () => api('/autorizacoes', {body: {titulo: form.titulo, descricao: form.descricao, turma_id: form.turma_id || null, data_evento: form.data_evento || null, prazo: form.prazo ? new Date(form.prazo).toISOString() : null}}),
    onSuccess: () => { recarrega(); setNovo(false); setForm(VAZIO); },
  });
  const arquiva = useMutation({mutationFn: (id: string) => api(`/autorizacoes/${id}/arquivar`, {method: 'POST'}), onSuccess: recarrega});
  return (
    <>
      <div className="topo">
        <h1>Autorizações</h1>
        <button className="botao" onClick={() => setNovo(true)}>+ Nova autorização</button>
      </div>
      {lista.isLoading && <Carregando />}
      <Erro erro={lista.error} />
      {lista.data?.length === 0 && <Vazio>Nenhuma autorização pedida.</Vazio>}
      <div className="pilha">
        {lista.data?.map((a) => (
          <article key={a.id} className="cartao">
            <div className="linha entre">
              <h2 style={{fontSize: '1.15rem', margin: 0}}>{a.titulo}</h2>
              <span className="selo">{a.turma ?? 'Escola toda'}</span>
            </div>
            <div className="suave pequeno">{a.autor}{a.data_evento && ` · data: ${dataBR(a.data_evento)}`}{a.prazo && ` · prazo ${quando(a.prazo)}`}</div>
            <div className="linha" style={{margin: '0.6rem 0'}}>
              <span className="selo verde">{a.autorizados} autorizaram</span>
              <span className="selo vermelho">{a.negados} negaram</span>
              <span className="selo laranja">{a.pendentes} pendentes</span>
            </div>
            <div className="linha">
              <button className="botao secundario pequeno" onClick={() => setPainel(a.id)}>Ver respostas</button>
              <button className="botao secundario pequeno" onClick={() => arquiva.mutate(a.id)}>Arquivar</button>
            </div>
          </article>
        ))}
      </div>
      <Painel id={painel} fechar={() => setPainel(null)} />
      <Modal titulo="Nova autorização" aberto={novo} fechar={() => setNovo(false)} largo>
        <form className="pilha" onSubmit={(e) => { e.preventDefault(); criar.mutate(); }}>
          <label className="campo">Título<input required maxLength={200} placeholder="Passeio ao museu" value={form.titulo} onChange={(e) => setForm({...form, titulo: e.target.value})} /></label>
          <label className="campo">Detalhes<textarea required rows={5} maxLength={5000} placeholder="Local, horário, custo, o que levar" value={form.descricao} onChange={(e) => setForm({...form, descricao: e.target.value})} /></label>
          <div className="form-grade">
            <label className="campo">
              Para
              <select value={form.turma_id} onChange={(e) => setForm({...form, turma_id: e.target.value})}>
                {geral ? <option value="">Escola toda</option> : <option value="" disabled>Escolha a turma</option>}
                {turmas.data?.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
              </select>
            </label>
            <label className="campo">Data do evento<input type="date" value={form.data_evento} onChange={(e) => setForm({...form, data_evento: e.target.value})} /></label>
            <label className="campo">Responder até<input type="datetime-local" value={form.prazo} onChange={(e) => setForm({...form, prazo: e.target.value})} /></label>
          </div>
          <Erro erro={criar.error} />
          <button className="botao" disabled={criar.isPending || (!geral && !form.turma_id)}>Pedir autorização</button>
        </form>
      </Modal>
    </>
  );
}

export default function Autorizacoes() {
  const papel = usePapel();
  return papel === 'responsavel' ? <><div className="topo"><h1>Autorizações</h1></div><Familia /></> : <Equipe />;
}
