import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {useMe, usePapel} from '../lib/auth';
import {dataBR} from '../lib/formato';
import type {ConfigImpressao, Pedido, StatusPedido, TipoPedido, TurmaResumo} from '../lib/tipos';

const STATUS: Record<StatusPedido, [string, string]> = {
  rascunho: ['Rascunho', ''], enviada: ['Em análise', 'laranja'], ajustes: ['Ajustes pedidos', 'vermelho'], aprovada: ['Na fila', 'verde'], impressa: ['Impresso', ''],
};
const TIPO: Record<TipoPedido, string> = {prova: 'Prova', trabalho: 'Trabalho', lista: 'Lista de exercícios'};
const mb = (b: number) => (b < 1e6 ? `${Math.max(1, Math.round(b / 1e3))} KB` : `${(b / 1e6).toFixed(1)} MB`);
const quando = (iso: string) => new Date(iso).toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'});

async function baixar(id: string, versao: 'principal' | 'adaptado') {
  const r = await api<{url: string}>(`/pedidos/${id}/arquivo-link?versao=${versao}`, {method: 'POST'});
  window.location.assign(r.url);
}

function Detalhe({id, fechar}: {id: string | null; fechar: () => void}) {
  const papel = usePapel();
  const {data: me} = useMe();
  const qc = useQueryClient();
  const q = useQuery({queryKey: ['pedido', id], queryFn: () => api<Pedido>(`/pedidos/${id}`), enabled: !!id});
  const [coment, setComent] = useState('');
  const [copias, setCopias] = useState<string>('');
  const refaz = () => { qc.invalidateQueries({queryKey: ['pedido', id]}); qc.invalidateQueries({queryKey: ['pedidos']}); };
  const acao = useMutation({
    mutationFn: ({rota, corpo}: {rota: string; corpo?: unknown}) => api(`/pedidos/${id}/${rota}`, {method: 'POST', body: corpo ?? {}}),
    onSuccess: () => { refaz(); setComent(''); },
  });
  const salva = useMutation({mutationFn: () => api(`/pedidos/${id}`, {method: 'PATCH', body: {copias: Number(copias)}}), onSuccess: () => { refaz(); setCopias(''); }});
  const troca = useMutation({
    mutationFn: (f: File) => { const fd = new FormData(); fd.append('versao', 'principal'); fd.append('arquivo', f); return api(`/pedidos/${id}/arquivo`, {form: fd}); },
    onSuccess: refaz,
  });
  const exclui = useMutation({mutationFn: () => api(`/pedidos/${id}`, {method: 'DELETE'}), onSuccess: () => { refaz(); fechar(); }});
  const p = q.data;
  const familia = papel === 'responsavel' || papel === 'aluno';
  const autor = !!p && p.autor_id === me?.usuario.id;
  const editavel = autor && (p?.status === 'rascunho' || p?.status === 'ajustes');
  const revisor = papel === 'admin' || papel === 'coordenacao';
  return (
    <Modal titulo={p?.titulo ?? 'Pedido'} aberto={!!id} fechar={fechar} largo>
      {q.isLoading && <Carregando />}
      <Erro erro={q.error || acao.error || salva.error || troca.error || exclui.error} />
      {p && (
        <div className="pilha">
          <div className="linha">
            <span className="selo">{TIPO[p.tipo]}</span><span className="selo">{p.turma}</span><span className="selo">{p.disciplina}</span>
            {!familia && <span className={`selo ${STATUS[p.status][1]}`}>{STATUS[p.status][0]}</span>}
            {p.publicado && <span className="selo verde">Publicado para a turma</span>}
            {p.atrasado && <span className="selo vermelho">Fora da antecedência</span>}
          </div>
          <div>{p.tipo === 'prova' ? 'Aplicação' : 'Entrega'}: <strong>{dataBR(p.data_aplicacao)}</strong> · {p.professor}</div>
          <div className="linha">
            <button className="botao secundario" onClick={() => baixar(p.id, 'principal')}>Baixar {p.arquivo.nome} ({mb(p.arquivo.tamanho)})</button>
            {p.adaptado && !familia && <button className="botao secundario" onClick={() => baixar(p.id, 'adaptado')}>Baixar versão adaptada</button>}
          </div>
          {!familia && (
            <div className="cartao" style={{padding: '0.75rem 1rem'}}>
              <strong>Impressão:</strong> {p.copias} cópia(s){p.copias !== p.copias_calculadas && ` (calculado: ${p.copias_calculadas})`}
              {!!p.copias_adaptadas && ` + ${p.copias_adaptadas} adaptada(s)`} · {p.frente_verso ? 'frente e verso' : 'só frente'} · {p.colorido ? 'colorido' : 'P&B'}{p.grampear && ' · grampear'}
              {p.observacoes && <div className="suave pequeno">{p.observacoes}</div>}
            </div>
          )}
          {!familia && (editavel || (papel === 'admin' && p.status !== 'impressa')) && (
            <form className="linha" onSubmit={(e) => { e.preventDefault(); salva.mutate(); }}>
              <input type="number" min={1} max={1000} placeholder="Nova quantidade de cópias" value={copias} onChange={(e) => setCopias(e.target.value)} style={{maxWidth: '16rem', marginTop: 0}} aria-label="Cópias" />
              <button className="botao secundario pequeno" disabled={!copias || salva.isPending}>Alterar cópias</button>
            </form>
          )}
          {editavel && (
            <label className="campo">Trocar o arquivo (PDF ou DOCX)<input type="file" accept=".pdf,.docx" onChange={(e) => e.target.files?.[0] && troca.mutate(e.target.files[0])} /></label>
          )}
          <div className="linha">
            {(editavel || (papel === 'admin' && p.status !== 'impressa' && p.status !== 'aprovada')) && <button className="botao" disabled={acao.isPending} onClick={() => acao.mutate({rota: 'enviar'})}>Enviar para {papel === 'admin' ? 'a fila' : 'análise'}</button>}
            {revisor && p.status === 'enviada' && <button className="botao" disabled={acao.isPending} onClick={() => acao.mutate({rota: 'aprovar'})}>Aprovar</button>}
            {papel === 'admin' && p.status === 'aprovada' && <button className="botao" disabled={acao.isPending} onClick={() => acao.mutate({rota: 'imprimir'})}>Marcar como impresso</button>}
            {(autor || revisor) && (p.status === 'aprovada' || p.status === 'impressa') && (
              <button className="botao secundario" disabled={acao.isPending} onClick={() => acao.mutate({rota: 'publicar', corpo: {publicado: !p.publicado}})}>{p.publicado ? 'Retirar da turma' : 'Publicar para a turma'}</button>
            )}
            {p.status === 'rascunho' && autor && <button className="botao secundario" disabled={exclui.isPending} onClick={() => exclui.mutate()}>Excluir rascunho</button>}
          </div>
          {revisor && p.status === 'enviada' && (
            <form className="pilha" onSubmit={(e) => { e.preventDefault(); acao.mutate({rota: 'ajustes', corpo: {corpo: coment}}); }}>
              <label className="campo">Pedir ajustes (explique o que mudar)<textarea required rows={2} maxLength={1000} value={coment} onChange={(e) => setComent(e.target.value)} /></label>
              <div><button className="botao secundario" disabled={acao.isPending || !coment.trim()}>Devolver ao professor</button></div>
            </form>
          )}
          {!familia && (
            <div className="pilha">
              <strong>Comentários</strong>
              {p.comentarios?.length === 0 && <span className="suave pequeno">Nenhum comentário.</span>}
              {p.comentarios?.map((c) => <div key={c.id} className="cartao" style={{padding: '0.5rem 0.9rem'}}><div className="suave pequeno">{c.autor} · {quando(c.criado_em)}</div>{c.corpo}</div>)}
              {p.status !== 'impressa' && p.status !== 'enviada' && (
                <form className="linha" onSubmit={(e) => { e.preventDefault(); acao.mutate({rota: 'comentarios', corpo: {corpo: coment}}); }}>
                  <input value={coment} maxLength={1000} onChange={(e) => setComent(e.target.value)} placeholder="Escrever um comentário" aria-label="Comentário" style={{marginTop: 0, flex: 1}} />
                  <button className="botao secundario pequeno" disabled={!coment.trim() || acao.isPending}>Comentar</button>
                </form>
              )}
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

const VAZIO = {titulo: '', tipo: 'prova' as TipoPedido, data: '', atribs: [] as string[], copias: '', adaptadas: '', fv: true, cor: false, gramp: false, obs: ''};

function Novo({aberto, fechar}: {aberto: boolean; fechar: () => void}) {
  const {data: me} = useMe();
  const papel = usePapel();
  const qc = useQueryClient();
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas'), enabled: aberto});
  const [f, setF] = useState(VAZIO);
  const [arq, setArq] = useState<File | null>(null);
  const [adap, setAdap] = useState<File | null>(null);
  const opcoes = (turmas.data ?? []).flatMap((t) => t.atribuicoes.filter((a) => papel !== 'professor' || a.professor_id === me?.usuario.id).map((a) => ({...a, turma: t.nome})));
  const sug = useQuery({queryKey: ['copias', f.atribs[0]], queryFn: () => api<{alunos: number; reserva: number; total: number}>(`/atribuicoes/${f.atribs[0]}/copias-sugeridas`), enabled: aberto && f.atribs.length > 0});
  const cria = useMutation({
    mutationFn: () => {
      const fd = new FormData();
      fd.append('titulo', f.titulo); fd.append('tipo', f.tipo); fd.append('data_aplicacao', f.data);
      f.atribs.forEach((a) => fd.append('atribuicao_ids', a));
      if (f.copias) fd.append('copias', f.copias);
      if (adap && f.adaptadas) fd.append('copias_adaptadas', f.adaptadas);
      fd.append('frente_verso', String(f.fv)); fd.append('colorido', String(f.cor)); fd.append('grampear', String(f.gramp));
      if (f.obs) fd.append('observacoes', f.obs);
      fd.append('arquivo', arq!);
      if (adap) fd.append('arquivo_adaptado', adap);
      return api('/pedidos', {form: fd});
    },
    onSuccess: () => { qc.invalidateQueries({queryKey: ['pedidos']}); setF(VAZIO); setArq(null); setAdap(null); fechar(); },
  });
  const alterna = (id: string) => setF({...f, atribs: f.atribs.includes(id) ? f.atribs.filter((x) => x !== id) : [...f.atribs, id]});
  return (
    <Modal titulo="Novo pedido" aberto={aberto} fechar={fechar} largo>
      <form className="pilha" onSubmit={(e) => { e.preventDefault(); cria.mutate(); }}>
        <div className="form-grade">
          <label className="campo">Título<input required maxLength={200} value={f.titulo} onChange={(e) => setF({...f, titulo: e.target.value})} /></label>
          <label className="campo">Tipo<select value={f.tipo} onChange={(e) => setF({...f, tipo: e.target.value as TipoPedido})}>{Object.entries(TIPO).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
          <label className="campo">{f.tipo === 'prova' ? 'Data de aplicação' : 'Data de entrega'}<input required type="date" min={new Date().toISOString().slice(0, 10)} value={f.data} onChange={(e) => setF({...f, data: e.target.value})} /></label>
        </div>
        <fieldset className="campo" style={{border: 0, padding: 0}}>
          <legend>Turmas e disciplinas</legend>
          {opcoes.map((a) => (
            <label key={a.id} className="linha"><input type="checkbox" checked={f.atribs.includes(a.id)} onChange={() => alterna(a.id)} /> {a.turma} · {a.disciplina}{papel !== 'professor' && <span className="suave pequeno"> ({a.professor})</span>}</label>
          ))}
        </fieldset>
        <div className="form-grade">
          <label className="campo">Arquivo (PDF ou DOCX, até 15 MB)<input required type="file" accept=".pdf,.docx" onChange={(e) => setArq(e.target.files?.[0] ?? null)} /></label>
          <label className="campo">Versão adaptada (opcional)<input type="file" accept=".pdf,.docx" onChange={(e) => setAdap(e.target.files?.[0] ?? null)} /></label>
          <label className="campo">Cópias {sug.data && <span className="suave pequeno">(sugerido: {sug.data.alunos} alunos + {sug.data.reserva} de reserva = {sug.data.total})</span>}
            <input type="number" min={1} max={1000} placeholder={sug.data ? String(sug.data.total) : 'automático'} value={f.copias} onChange={(e) => setF({...f, copias: e.target.value})} />
          </label>
          {adap && <label className="campo">Cópias da versão adaptada<input type="number" min={0} max={100} value={f.adaptadas} onChange={(e) => setF({...f, adaptadas: e.target.value})} /></label>}
        </div>
        <div className="linha">
          <label className="linha"><input type="checkbox" checked={f.fv} onChange={(e) => setF({...f, fv: e.target.checked})} /> Frente e verso</label>
          <label className="linha"><input type="checkbox" checked={f.cor} onChange={(e) => setF({...f, cor: e.target.checked})} /> Colorido</label>
          <label className="linha"><input type="checkbox" checked={f.gramp} onChange={(e) => setF({...f, gramp: e.target.checked})} /> Grampear</label>
        </div>
        <label className="campo">Observações (opcional)<input maxLength={500} value={f.obs} onChange={(e) => setF({...f, obs: e.target.value})} /></label>
        <p className="suave pequeno" style={{margin: 0}}>O arquivo é guardado cifrado e só você, a coordenação e a secretaria podem abri-lo, até você publicá-lo para a turma.</p>
        <Erro erro={cria.error} />
        <button className="botao" disabled={cria.isPending || !arq || f.atribs.length === 0}>Criar rascunho</button>
      </form>
    </Modal>
  );
}

function Config({aberto, fechar}: {aberto: boolean; fechar: () => void}) {
  const qc = useQueryClient();
  const q = useQuery({queryKey: ['impressao-config'], queryFn: () => api<ConfigImpressao>('/impressao/config'), enabled: aberto});
  const [f, setF] = useState<ConfigImpressao | null>(null);
  const v = f ?? q.data;
  const salva = useMutation({mutationFn: () => api<ConfigImpressao>('/impressao/config', {method: 'PUT', body: v}), onSuccess: (r) => { qc.setQueryData(['impressao-config'], r); qc.invalidateQueries({queryKey: ['pedidos']}); setF(null); fechar(); }});
  return (
    <Modal titulo="Regras da escola" aberto={aberto} fechar={fechar}>
      {v && (
        <form className="pilha" onSubmit={(e) => { e.preventDefault(); salva.mutate(); }}>
          <label className="linha"><input type="checkbox" checked={v.aprovacao} onChange={(e) => setF({...v, aprovacao: e.target.checked})} /> Exigir aprovação da coordenação antes da impressão</label>
          <label className="campo">Cópias de reserva por turma<input type="number" min={0} max={50} value={v.reserva_copias} onChange={(e) => setF({...v, reserva_copias: Number(e.target.value)})} /></label>
          <label className="campo">Antecedência mínima (dias antes da aplicação)<input type="number" min={0} max={30} value={v.antecedencia_dias} onChange={(e) => setF({...v, antecedencia_dias: Number(e.target.value)})} /></label>
          <Erro erro={salva.error} />
          <button className="botao" disabled={salva.isPending}>Salvar</button>
        </form>
      )}
    </Modal>
  );
}

export default function Provas() {
  const papel = usePapel();
  const familia = papel === 'responsavel' || papel === 'aluno';
  const staff = papel === 'admin' || papel === 'coordenacao';
  const [status, setStatus] = useState<'' | StatusPedido>('');
  const [de, setDe] = useState('');
  const [ate, setAte] = useState('');
  const [aberto, setAberto] = useState<string | null>(null);
  const [novo, setNovo] = useState(false);
  const [config, setConfig] = useState(false);
  const qs = new URLSearchParams({...(status && {status}), ...(de && {de}), ...(ate && {ate})}).toString();
  const lista = useQuery({queryKey: ['pedidos', qs], queryFn: () => api<Pedido[]>(`/pedidos${qs ? `?${qs}` : ''}`)});
  const totalCopias = (lista.data ?? []).filter((p) => p.status === 'aprovada').reduce((s, p) => s + (p.copias ?? 0) + (p.copias_adaptadas ?? 0), 0);
  return (
    <>
      <div className="topo">
        <h1>{familia ? 'Materiais' : 'Provas e impressão'}</h1>
        {!familia && (
          <div className="linha">
            {papel === 'admin' && <button className="botao secundario" onClick={() => setConfig(true)}>Regras</button>}
            <button className="botao" onClick={() => setNovo(true)}>+ Novo pedido</button>
          </div>
        )}
      </div>
      {!familia && (
        <div className="linha" style={{marginBottom: '0.75rem'}}>
          <select aria-label="Situação" value={status} onChange={(e) => setStatus(e.target.value as '' | StatusPedido)} style={{marginTop: 0}}>
            <option value="">Todas as situações</option>
            {Object.entries(STATUS).map(([k, [r]]) => <option key={k} value={k}>{r}</option>)}
          </select>
          <label className="linha">de <input type="date" value={de} onChange={(e) => setDe(e.target.value)} style={{marginTop: 0}} /></label>
          <label className="linha">até <input type="date" value={ate} onChange={(e) => setAte(e.target.value)} style={{marginTop: 0}} /></label>
          {staff && totalCopias > 0 && <span className="selo verde">{totalCopias} cópias na fila</span>}
        </div>
      )}
      {lista.isLoading && <Carregando />}
      <Erro erro={lista.error} />
      {lista.data?.length === 0 && <Vazio>{familia ? 'Nenhum material publicado pelos professores.' : 'Nenhum pedido neste filtro.'}</Vazio>}
      <div className="pilha">
        {lista.data?.map((p) => (
          <button key={p.id} className="cartao" style={{textAlign: 'left', cursor: 'pointer'}} onClick={() => setAberto(p.id)}>
            <div className="linha entre">
              <strong>{p.titulo}</strong>
              <div className="linha">
                {!familia && <span className={`selo ${STATUS[p.status][1]}`}>{STATUS[p.status][0]}</span>}
                {p.atrasado && <span className="selo vermelho">fora da antecedência</span>}
              </div>
            </div>
            <div className="suave pequeno">{TIPO[p.tipo]} · {p.turma} · {p.disciplina} · {p.tipo === 'prova' ? 'aplicação' : 'entrega'} {dataBR(p.data_aplicacao)}{!familia && ` · ${p.professor}`}{!familia && ` · ${p.copias} cópias`}</div>
          </button>
        ))}
      </div>
      <Detalhe id={aberto} fechar={() => setAberto(null)} />
      {!familia && <Novo aberto={novo} fechar={() => setNovo(false)} />}
      {papel === 'admin' && <Config aberto={config} fechar={() => setConfig(false)} />}
    </>
  );
}
