import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import type {Aluno, Conversa, ConversaAberta, TurmaResumo} from '../lib/tipos';

const mb = (b: number) => (b < 1e6 ? `${Math.max(1, Math.round(b / 1e3))} KB` : `${(b / 1e6).toFixed(1)} MB`);
async function baixarAnexo(cid: string, aid: string) {
  const r = await api<{url: string}>(`/conversas/${cid}/anexos/${aid}/link`, {method: 'POST'});
  window.location.assign(r.url);
}

const quando = (iso: string) => new Date(iso).toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'});
const VAZIO = {aluno_id: '', professor_id: '', assunto: '', corpo: ''};

function Thread({id, voltar}: {id: string; voltar: () => void}) {
  const qc = useQueryClient();
  const [texto, setTexto] = useState('');
  const [arquivos, setArquivos] = useState<File[]>([]);
  const c = useQuery({
    queryKey: ['conversa', id],
    queryFn: async () => {
      const r = await api<ConversaAberta>(`/conversas/${id}`);
      qc.invalidateQueries({queryKey: ['conversas']});
      qc.invalidateQueries({queryKey: ['mensagens-pendentes']});
      return r;
    },
    refetchInterval: 20000,
  });
  const envia = useMutation({
    mutationFn: () => {
      if (arquivos.length === 0) return api(`/conversas/${id}/mensagens`, {body: {corpo: texto}});
      const fd = new FormData();
      fd.append('corpo', texto);
      arquivos.forEach((f) => fd.append('arquivos', f));
      return api(`/conversas/${id}/mensagens-anexos`, {form: fd});
    },
    onSuccess: () => {
      setTexto('');
      setArquivos([]);
      qc.invalidateQueries({queryKey: ['conversa', id]});
      qc.invalidateQueries({queryKey: ['conversas']});
    },
  });
  return (
    <>
      <div className="topo">
        <div>
          <button className="botao secundario pequeno" onClick={voltar}>← Conversas</button>
        </div>
      </div>
      {c.isLoading && <Carregando />}
      <Erro erro={c.error} />
      {c.data && (
        <div className="pilha">
          <div>
            <h1 style={{marginBottom: 0}}>{c.data.assunto}</h1>
            <div className="suave pequeno">{c.data.aluno} · com {c.data.escola_usuario}</div>
          </div>
          {c.data.mensagens.map((m) => (
            <div key={m.id} className="cartao" style={{marginLeft: m.minha ? '2rem' : 0, marginRight: m.minha ? 0 : '2rem', background: m.minha ? 'var(--azul-claro)' : undefined}}>
              <div className="suave pequeno">{m.autor} · {quando(m.criado_em)}</div>
              <div style={{whiteSpace: 'pre-wrap'}}>{m.corpo}</div>
              {m.anexos.map((x) => (
                <button key={x.id} className="botao secundario pequeno" style={{marginTop: '0.4rem', marginRight: '0.4rem'}} onClick={() => baixarAnexo(id, x.id)}>
                  📎 {x.nome} ({mb(x.tamanho)})
                </button>
              ))}
            </div>
          ))}
          <form className="pilha" onSubmit={(e) => { e.preventDefault(); envia.mutate(); }}>
            <label className="campo">Responder<textarea required={arquivos.length === 0} rows={3} maxLength={5000} value={texto} onChange={(e) => setTexto(e.target.value)} /></label>
            <label className="campo">Anexos (opcional: até 3 arquivos PDF, JPG ou PNG de 10 MB)
              <input type="file" multiple accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setArquivos(Array.from(e.target.files ?? []).slice(0, 3))} />
            </label>
            {arquivos.length > 0 && <span className="suave pequeno">Fotos são enviadas sem localização e outros dados do aparelho.</span>}
            <Erro erro={envia.error} />
            <div><button className="botao" disabled={envia.isPending || (!texto.trim() && arquivos.length === 0)}>Enviar</button></div>
          </form>
        </div>
      )}
    </>
  );
}

export default function Mensagens() {
  const papel = usePapel();
  const qc = useQueryClient();
  const familia = papel === 'responsavel';
  const [aberta, setAberta] = useState<string | null>(null);
  const [novo, setNovo] = useState(false);
  const [form, setForm] = useState(VAZIO);
  const lista = useQuery({queryKey: ['conversas'], queryFn: () => api<Conversa[]>('/conversas'), refetchInterval: 30000});
  const alunos = useQuery({queryKey: ['alunos-msg'], queryFn: () => api<Aluno[]>('/alunos'), enabled: novo});
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas'), enabled: novo && familia});
  const aluno = alunos.data?.find((a) => a.id === form.aluno_id);
  const professores = familia && aluno?.turma
    ? [...new Map((turmas.data?.find((t) => t.id === aluno.turma!.id)?.atribuicoes ?? []).map((a) => [a.professor_id, a])).values()]
    : [];
  const criar = useMutation({
    mutationFn: () => api<Conversa>('/conversas', {body: {aluno_id: form.aluno_id, assunto: form.assunto, corpo: form.corpo, professor_id: familia ? form.professor_id : null}}),
    onSuccess: (c) => {
      qc.invalidateQueries({queryKey: ['conversas']});
      setNovo(false);
      setForm(VAZIO);
      setAberta(c.id);
    },
  });

  if (aberta) return <Thread id={aberta} voltar={() => setAberta(null)} />;
  return (
    <>
      <div className="topo">
        <h1>Mensagens</h1>
        <button className="botao" onClick={() => setNovo(true)}>+ Nova conversa</button>
      </div>
      {lista.isLoading && <Carregando />}
      <Erro erro={lista.error} />
      {lista.data?.length === 0 && <Vazio>Nenhuma conversa ainda.</Vazio>}
      <div className="pilha">
        {lista.data?.map((c) => (
          <button key={c.id} className="cartao" style={{textAlign: 'left', cursor: 'pointer', borderLeft: c.nao_lida ? '4px solid var(--azul)' : undefined}} onClick={() => setAberta(c.id)}>
            <div className="linha entre">
              <strong>{c.assunto}</strong>
              <div className="linha">
                {c.nao_lida && <span className="selo vermelho">nova</span>}
                <span className="suave pequeno">{quando(c.ultima_em)}</span>
              </div>
            </div>
            <div className="suave pequeno">{c.aluno} · com {c.escola_usuario}</div>
            <div style={{overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{c.previa}</div>
          </button>
        ))}
      </div>
      <Modal titulo="Nova conversa" aberto={novo} fechar={() => setNovo(false)} largo>
        <form className="pilha" onSubmit={(e) => { e.preventDefault(); criar.mutate(); }}>
          <div className="form-grade">
            <label className="campo">
              Aluno
              <select required value={form.aluno_id} onChange={(e) => setForm({...form, aluno_id: e.target.value, professor_id: ''})}>
                <option value="" disabled>Escolha</option>
                {alunos.data?.map((a) => <option key={a.id} value={a.id}>{a.nome} {a.sobrenome}{a.turma ? ` (${a.turma.nome})` : ''}</option>)}
              </select>
            </label>
            {familia && (
              <label className="campo">
                Professor
                <select required value={form.professor_id} onChange={(e) => setForm({...form, professor_id: e.target.value})}>
                  <option value="" disabled>Escolha</option>
                  {professores.map((a) => <option key={a.professor_id} value={a.professor_id}>{a.professor} · {a.disciplina}</option>)}
                </select>
              </label>
            )}
          </div>
          <label className="campo">Assunto<input required maxLength={200} value={form.assunto} onChange={(e) => setForm({...form, assunto: e.target.value})} /></label>
          <label className="campo">Mensagem<textarea required rows={5} maxLength={5000} value={form.corpo} onChange={(e) => setForm({...form, corpo: e.target.value})} /></label>
          <Erro erro={criar.error} />
          <button className="botao" disabled={criar.isPending}>Enviar</button>
        </form>
      </Modal>
    </>
  );
}
