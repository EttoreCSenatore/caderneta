import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import type {Anotacao, TipoAnotacao, VersaoAnotacao} from '../lib/tipos';
import {Carregando, Erro, Modal, Vazio} from './ui';

const NOME: Record<TipoAnotacao, string> = {pedagogica: 'Pedagógica', ocorrencia: 'Ocorrência', elogio: 'Elogio', reservada: 'Reservada'};
const COR: Record<TipoAnotacao, string> = {pedagogica: '', ocorrencia: 'laranja', elogio: 'verde', reservada: 'vermelho'};
const DICA: Record<TipoAnotacao, string> = {
  pedagogica: 'Professores do aluno e coordenação. Segue o aluno de um ano para o outro.',
  ocorrencia: 'Coordenação, direção e quem registrou. Os responsáveis só veem se você marcar.',
  elogio: 'Professores, coordenação e responsáveis.',
  reservada: 'Só coordenação e direção. Cada leitura fica registrada.',
};
const quando = (iso: string) => new Date(iso).toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'});
const VAZIO = {id: '', tipo: 'pedagogica' as TipoAnotacao, corpo: '', visivel: false};

function Historico({id, fechar}: {id: string | null; fechar: () => void}) {
  const q = useQuery({queryKey: ['versoes', id], queryFn: () => api<VersaoAnotacao[]>(`/anotacoes/${id}/versoes`), enabled: !!id});
  return (
    <Modal titulo="Histórico de edições" aberto={!!id} fechar={fechar}>
      {q.isLoading && <Carregando />}
      <Erro erro={q.error} />
      <div className="pilha">
        {q.data?.map((v) => (
          <div key={v.versao} className="cartao" style={{padding: '0.6rem 0.9rem'}}>
            <div className="suave pequeno">Versão {v.versao} · {v.editado_por} · {quando(v.criado_em)} · {NOME[v.tipo]}</div>
            <div style={{whiteSpace: 'pre-wrap'}}>{v.corpo}</div>
          </div>
        ))}
      </div>
    </Modal>
  );
}

export function Anotacoes({alunoId}: {alunoId: string}) {
  const papel = usePapel();
  const qc = useQueryClient();
  const staff = papel === 'admin' || papel === 'coordenacao';
  const escreve = papel === 'admin' || papel === 'coordenacao' || papel === 'professor';
  const [filtro, setFiltro] = useState<'' | TipoAnotacao>('');
  const [form, setForm] = useState<typeof VAZIO | null>(null);
  const [hist, setHist] = useState<string | null>(null);
  const lista = useQuery({queryKey: ['anotacoes', alunoId, filtro], queryFn: () => api<Anotacao[]>(`/alunos/${alunoId}/anotacoes${filtro ? `?tipo=${filtro}` : ''}`)});
  const recarrega = () => qc.invalidateQueries({queryKey: ['anotacoes', alunoId]});
  const salva = useMutation({
    mutationFn: (f: typeof VAZIO) => {
      const body = {tipo: f.tipo, corpo: f.corpo, visivel_responsaveis: f.tipo === 'ocorrencia' && f.visivel};
      return f.id ? api(`/anotacoes/${f.id}`, {method: 'PATCH', body}) : api(`/alunos/${alunoId}/anotacoes`, {body});
    },
    onSuccess: () => { recarrega(); setForm(null); },
  });
  const remove = useMutation({mutationFn: (id: string) => api(`/anotacoes/${id}`, {method: 'DELETE'}), onSuccess: recarrega});
  const tipos = (staff ? ['pedagogica', 'ocorrencia', 'elogio', 'reservada'] : ['pedagogica', 'ocorrencia', 'elogio']) as TipoAnotacao[];
  return (
    <div className="pilha">
      <div className="linha entre">
        <select aria-label="Filtrar por tipo" value={filtro} onChange={(e) => setFiltro(e.target.value as '' | TipoAnotacao)} style={{marginTop: 0, maxWidth: '14rem'}}>
          <option value="">Todos os tipos</option>
          {(Object.keys(NOME) as TipoAnotacao[]).filter((t) => staff || t !== 'reservada').map((t) => <option key={t} value={t}>{NOME[t]}</option>)}
        </select>
        {escreve && <button className="botao" onClick={() => setForm({...VAZIO})}>+ Nova anotação</button>}
      </div>
      {lista.isLoading && <Carregando />}
      <Erro erro={lista.error} />
      {lista.data?.length === 0 && <Vazio>Nenhuma anotação.</Vazio>}
      {lista.data?.map((a) => (
        <article key={a.id} className="cartao" style={a.removida ? {opacity: 0.55} : undefined}>
          <div className="linha entre">
            <div className="linha">
              <span className={`selo ${COR[a.tipo]}`}>{NOME[a.tipo]}</span>
              <span className="suave pequeno">{a.ano} · {a.autor} · {quando(a.criado_em)}</span>
              {a.versao && a.versao > 1 && <span className="selo">editada ({a.versao} versões)</span>}
              {a.removida && <span className="selo vermelho">removida</span>}
              {a.tipo === 'ocorrencia' && a.visivel_responsaveis && <span className="selo">visível aos responsáveis</span>}
            </div>
          </div>
          <p style={{whiteSpace: 'pre-wrap', margin: '0.5rem 0'}}>{a.corpo}</p>
          {a.editavel && (
            <div className="linha">
              <button className="botao secundario pequeno" onClick={() => setForm({id: a.id, tipo: a.tipo, corpo: a.corpo, visivel: a.visivel_responsaveis})}>Editar</button>
              {(a.versao ?? 1) > 1 && <button className="botao secundario pequeno" onClick={() => setHist(a.id)}>Histórico</button>}
              <button className="botao secundario pequeno" disabled={remove.isPending} onClick={() => window.confirm('Remover esta anotação? Ela some das telas e é eliminada em 30 dias.') && remove.mutate(a.id)}>Remover</button>
            </div>
          )}
        </article>
      ))}
      <Erro erro={remove.error} />
      <Historico id={hist} fechar={() => setHist(null)} />
      <Modal titulo={form?.id ? 'Editar anotação' : 'Nova anotação'} aberto={!!form} fechar={() => setForm(null)} largo>
        {form && (
          <form className="pilha" onSubmit={(e) => { e.preventDefault(); salva.mutate(form); }}>
            <label className="campo">Tipo
              <select value={form.tipo} onChange={(e) => setForm({...form, tipo: e.target.value as TipoAnotacao})}>
                {tipos.map((t) => <option key={t} value={t}>{NOME[t]}</option>)}
              </select>
            </label>
            <p className="suave pequeno" style={{margin: 0}}>{DICA[form.tipo]}</p>
            <label className="campo">Texto<textarea required rows={6} maxLength={5000} value={form.corpo} onChange={(e) => setForm({...form, corpo: e.target.value})} /></label>
            {form.tipo === 'ocorrencia' && (
              <label className="linha"><input type="checkbox" checked={form.visivel} onChange={(e) => setForm({...form, visivel: e.target.checked})} /> Mostrar aos responsáveis (eles são avisados)</label>
            )}
            <p className="suave pequeno" style={{margin: 0}}>Escreva só o necessário. Evite dados de saúde e citar outros alunos. Editar guarda a versão anterior.</p>
            <Erro erro={salva.error} />
            <button className="botao" disabled={salva.isPending || !form.corpo.trim()}>{form.id ? 'Salvar nova versão' : 'Salvar'}</button>
          </form>
        )}
      </Modal>
    </div>
  );
}
