import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import type {Aviso, PainelAviso, TurmaResumo} from '../lib/tipos';

const quando = (iso: string) => new Date(iso).toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'});
const VAZIO = {titulo: '', corpo: '', turma_id: '', exige_ciente: false, publicar_em: ''};

function Painel({id, fechar}: {id: string | null; fechar: () => void}) {
  const p = useQuery({queryKey: ['aviso-painel', id], queryFn: () => api<PainelAviso>(`/avisos/${id}/painel`), enabled: !!id});
  return (
    <Modal titulo="Quem leu" aberto={!!id} fechar={fechar} largo>
      {p.isLoading && <Carregando />}
      <Erro erro={p.error} />
      {p.data && (
        <div className="pilha">
          <div className="linha">
            <span className="selo">{p.data.lidos}/{p.data.total} leram</span>
            {p.data.aviso.exige_ciente && <span className="selo verde">{p.data.cientes}/{p.data.total} cientes</span>}
          </div>
          <table>
            <thead><tr><th>Nome</th><th>Leitura</th>{p.data.aviso.exige_ciente && <th>Ciente</th>}</tr></thead>
            <tbody>
              {p.data.destinatarios.map((d) => (
                <tr key={d.usuario_id}>
                  <td>{d.nome}</td>
                  <td>{d.lido_em ? quando(d.lido_em) : <span className="selo laranja">pendente</span>}</td>
                  {p.data.aviso.exige_ciente && <td>{d.ciente_em ? quando(d.ciente_em) : '—'}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  );
}

export default function Avisos() {
  const papel = usePapel();
  const qc = useQueryClient();
  const escreve = papel !== 'responsavel' && papel !== 'aluno';
  const lista = useQuery({queryKey: ['avisos'], queryFn: () => api<Aviso[]>('/avisos')});
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas'), enabled: escreve});
  const [novo, setNovo] = useState(false);
  const [form, setForm] = useState(VAZIO);
  const [painel, setPainel] = useState<string | null>(null);
  const recarrega = () => {
    qc.invalidateQueries({queryKey: ['avisos']});
    qc.invalidateQueries({queryKey: ['avisos-pendentes']});
  };
  const criar = useMutation({
    mutationFn: () =>
      api('/avisos', {
        body: {
          titulo: form.titulo,
          corpo: form.corpo,
          turma_id: form.turma_id || null,
          exige_ciente: form.exige_ciente,
          publicar_em: form.publicar_em ? new Date(form.publicar_em).toISOString() : null,
        },
      }),
    onSuccess: () => {
      recarrega();
      setNovo(false);
      setForm(VAZIO);
    },
  });
  const lido = useMutation({
    mutationFn: ({id, ciente}: {id: string; ciente: boolean}) => api(`/avisos/${id}/lido?ciente=${ciente}`, {method: 'POST'}),
    onSuccess: recarrega,
  });
  const arquiva = useMutation({mutationFn: (id: string) => api(`/avisos/${id}/arquivar`, {method: 'POST'}), onSuccess: recarrega});
  const geral = papel === 'admin' || papel === 'coordenacao';

  return (
    <>
      <div className="topo">
        <h1>Avisos</h1>
        {escreve && <button className="botao" onClick={() => setNovo(true)}>+ Novo aviso</button>}
      </div>
      {lista.isLoading && <Carregando />}
      <Erro erro={lista.error} />
      {lista.data?.length === 0 && <Vazio>Nenhum aviso por enquanto.</Vazio>}
      <div className="pilha">
        {lista.data?.map((a) => {
          const agendado = new Date(a.publicar_em) > new Date();
          return (
            <article key={a.id} className="cartao" style={a.lido || escreve ? undefined : {borderLeft: '4px solid var(--azul)'}}>
              <div className="linha entre">
                <h2 style={{fontSize: '1.15rem', margin: 0}}>{a.titulo}</h2>
                <div className="linha">
                  <span className="selo">{a.turma ?? 'Escola toda'}</span>
                  {agendado && <span className="selo laranja">agendado · {quando(a.publicar_em)}</span>}
                  {a.exige_ciente && <span className="selo verde">pede ciente</span>}
                </div>
              </div>
              <div className="suave pequeno">{a.autor} · {quando(a.publicar_em)}</div>
              <p style={{whiteSpace: 'pre-wrap'}}>{a.corpo}</p>
              <div className="linha">
                {!escreve && !a.lido && !a.exige_ciente && (
                  <button className="botao secundario pequeno" onClick={() => lido.mutate({id: a.id, ciente: false})}>Marcar como lido</button>
                )}
                {!escreve && a.exige_ciente && !a.ciente && (
                  <button className="botao pequeno" onClick={() => lido.mutate({id: a.id, ciente: true})}>Estou ciente</button>
                )}
                {!escreve && a.ciente && <span className="selo verde">Ciente</span>}
                {escreve && <button className="botao secundario pequeno" onClick={() => setPainel(a.id)}>Quem leu</button>}
                {escreve && <button className="botao secundario pequeno" onClick={() => arquiva.mutate(a.id)}>Arquivar</button>}
              </div>
            </article>
          );
        })}
      </div>
      <Painel id={painel} fechar={() => setPainel(null)} />
      <Modal titulo="Novo aviso" aberto={novo} fechar={() => setNovo(false)} largo>
        <form className="pilha" onSubmit={(e) => { e.preventDefault(); criar.mutate(); }}>
          <label className="campo">Título<input required maxLength={200} value={form.titulo} onChange={(e) => setForm({...form, titulo: e.target.value})} /></label>
          <label className="campo">Mensagem<textarea required rows={6} maxLength={10000} value={form.corpo} onChange={(e) => setForm({...form, corpo: e.target.value})} /></label>
          <div className="form-grade">
            <label className="campo">
              Para
              <select value={form.turma_id} onChange={(e) => setForm({...form, turma_id: e.target.value})}>
                {geral && <option value="">Escola toda</option>}
                {!geral && <option value="" disabled>Escolha a turma</option>}
                {turmas.data?.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
              </select>
            </label>
            <label className="campo">Publicar em (opcional)<input type="datetime-local" value={form.publicar_em} onChange={(e) => setForm({...form, publicar_em: e.target.value})} /></label>
          </div>
          <label className="linha"><input type="checkbox" checked={form.exige_ciente} onChange={(e) => setForm({...form, exige_ciente: e.target.checked})} /> Pedir "ciente" das famílias</label>
          <Erro erro={criar.error} />
          <button className="botao" disabled={criar.isPending || (!geral && !form.turma_id)}>{form.publicar_em ? 'Agendar' : 'Publicar'}</button>
        </form>
      </Modal>
    </>
  );
}
