import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Link, useParams} from 'react-router';
import {Icone} from '../components/icones';
import {Abas, Avatar, Carregando, Erro, LinkConvite, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import {dataBR, idade, NOME_VINCULO, nomeExibicao} from '../lib/formato';
import type {Aluno as TAluno, Saude, TurmaResumo, Vinculo} from '../lib/tipos';

type Aba = 'dados' | 'familia' | 'saude' | 'historico';

const CAMPOS_SAUDE: [keyof Saude, string][] = [
  ['alergias', 'Alergias'],
  ['medicamentos', 'Medicamentos de uso contínuo'],
  ['condicoes', 'Condições de saúde'],
  ['restricoes_alimentares', 'Restrições alimentares'],
  ['necessidades_especificas', 'Necessidades educacionais específicas'],
  ['plano_saude', 'Plano de saúde'],
  ['observacoes', 'Observações'],
];

function Dados({aluno}: {aluno: TAluno}) {
  const papel = usePapel();
  const qc = useQueryClient();
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas'), enabled: papel === 'admin'});
  const [edit, setEdit] = useState(false);
  const [f, setF] = useState({nome: aluno.nome, sobrenome: aluno.sobrenome, nome_social: aluno.nome_social ?? '', data_nascimento: aluno.data_nascimento, ra: aluno.ra ?? '', cpf: aluno.cpf ?? ''});
  const salvar = useMutation({
    mutationFn: () => api(`/alunos/${aluno.id}`, {method: 'PATCH', body: {...f, nome_social: f.nome_social || null, ra: f.ra || null, cpf: f.cpf || null}}),
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['aluno', aluno.id]});
      setEdit(false);
    },
  });
  const matricular = useMutation({
    mutationFn: (turma_id: string) => api(`/alunos/${aluno.id}/matricula`, {method: 'PUT', body: {turma_id}}),
    onSuccess: () => qc.invalidateQueries({queryKey: ['aluno', aluno.id]}),
  });
  const linhas: [string, string][] = [
    ['Nome', aluno.nome],
    ['Sobrenome', aluno.sobrenome],
    ['Nome social', aluno.nome_social ?? '—'],
    ['Nascimento', `${dataBR(aluno.data_nascimento)} (${idade(aluno.data_nascimento)} anos)`],
    ['RA / matrícula', aluno.ra ?? '—'],
  ];
  if (aluno.cpf !== undefined) linhas.push(['CPF', aluno.cpf ?? '—']);
  const set = (k: keyof typeof f) => (e: {target: {value: string}}) => setF({...f, [k]: e.target.value});
  return (
    <div className="pilha">
      <div className="cartao">
        <div className="linha entre">
          <h2>Identificação</h2>
          {papel === 'admin' && !edit && <button className="botao secundario pequeno" onClick={() => setEdit(true)}>Editar</button>}
        </div>
        {edit ? (
          <form className="pilha" onSubmit={(e) => { e.preventDefault(); salvar.mutate(); }}>
            <div className="form-grade">
              <label className="campo">Nome<input required value={f.nome} onChange={set('nome')} /></label>
              <label className="campo">Sobrenome<input required value={f.sobrenome} onChange={set('sobrenome')} /></label>
              <label className="campo">Nome social<input value={f.nome_social} onChange={set('nome_social')} /></label>
              <label className="campo">Nascimento<input type="date" required value={f.data_nascimento} onChange={set('data_nascimento')} /></label>
              <label className="campo">RA<input value={f.ra} onChange={set('ra')} /></label>
              <label className="campo">CPF <span className="dica">(opcional)</span><input value={f.cpf} onChange={set('cpf')} placeholder="000.000.000-00" /></label>
            </div>
            <Erro erro={salvar.error} />
            <div className="linha"><button className="botao">Salvar</button><button type="button" className="botao secundario" onClick={() => setEdit(false)}>Cancelar</button></div>
          </form>
        ) : (
          <table><tbody>{linhas.map(([k, v]) => <tr key={k}><th style={{width: '40%'}}>{k}</th><td>{v}</td></tr>)}</tbody></table>
        )}
      </div>
      {papel === 'admin' && (
        <div className="cartao">
          <h2>Turma no ano atual</h2>
          <select aria-label="Turma" value={aluno.turma?.id ?? ''} onChange={(e) => e.target.value && matricular.mutate(e.target.value)}>
            <option value="">Sem turma</option>
            {turmas.data?.map((t) => <option key={t.id} value={t.id}>{t.nome} · {t.serie}</option>)}
          </select>
          <Erro erro={matricular.error} />
        </div>
      )}
    </div>
  );
}

const VINCULO_VAZIO = {nome: '', tipo: 'mae', telefone: '', email: '', pode_buscar: true, recebe_avisos: true, emergencia: false, restrito: false};

function Familia({aluno}: {aluno: TAluno}) {
  const papel = usePapel();
  const qc = useQueryClient();
  const [modal, setModal] = useState<null | 'novo' | Vinculo>(null);
  const [f, setF] = useState(VINCULO_VAZIO);
  const [link, setLink] = useState<string | null>(null);
  const atualiza = () => qc.invalidateQueries({queryKey: ['aluno', aluno.id]});
  const salvar = useMutation({
    mutationFn: () => {
      const body = {...f, telefone: f.telefone || null, email: f.email || null};
      if (modal === 'novo') return api(`/alunos/${aluno.id}/responsaveis`, {body});
      const v = modal as Vinculo;
      return api(`/responsaveis/${v.id}`, {method: 'PATCH', body: papel === 'admin' ? body : {telefone: body.telefone, email: body.email}});
    },
    onSuccess: () => { atualiza(); setModal(null); },
  });
  const convidar = useMutation({
    mutationFn: (id: string) => api<{link: string}>(`/responsaveis/${id}/convite`, {method: 'POST'}),
    onSuccess: (r) => { setLink(r.link); atualiza(); },
  });
  const abrir = (v: Vinculo | 'novo') => {
    setF(v === 'novo' ? VINCULO_VAZIO : {...VINCULO_VAZIO, ...v, telefone: v.telefone ?? '', email: v.email ?? ''});
    setModal(v);
  };
  const resps = aluno.responsaveis ?? [];
  const soContato = papel !== 'admin';
  return (
    <div className="pilha">
      {link && <LinkConvite link={link} />}
      <div className="cartao lista">
        {resps.length === 0 && <Vazio>Nenhum responsável cadastrado.</Vazio>}
        {resps.map((v) => (
          <div key={v.id} className="item" style={{alignItems: 'flex-start'}}>
            <Avatar nome={v.nome} />
            <div style={{flex: 1, minWidth: 0}}>
              <div className="linha" style={{gap: '0.4rem'}}>
                <strong>{v.nome}</strong>
                <span className="selo">{NOME_VINCULO[v.tipo] ?? v.tipo}</span>
                {v.emergencia && <span className="selo vermelho">Emergência</span>}
                {v.restrito && <span className="selo laranja">Acesso restrito</span>}
                {v.tem_conta ? <span className="selo verde">Usa o app</span> : v.convite_pendente ? <span className="selo laranja">Convite enviado</span> : null}
              </div>
              <div className="suave pequeno">{[v.telefone, v.email].filter(Boolean).join(' · ') || 'Sem contato'}</div>
              <div className="suave pequeno">{v.pode_buscar ? 'Pode buscar o aluno' : 'Não pode buscar o aluno'} · {v.recebe_avisos ? 'recebe avisos' : 'não recebe avisos'}</div>
            </div>
            <div className="linha" style={{gap: '0.4rem'}}>
              {papel === 'admin' && !v.tem_conta && v.email && !v.restrito && (
                <button className="botao secundario pequeno" onClick={() => convidar.mutate(v.id)}>{v.convite_pendente ? 'Reenviar convite' : 'Convidar'}</button>
              )}
              {papel === 'admin' && <button className="botao secundario pequeno" onClick={() => abrir(v)}>Editar</button>}
            </div>
          </div>
        ))}
      </div>
      <Erro erro={convidar.error} />
      {papel === 'admin' && <div><button className="botao" onClick={() => abrir('novo')}>+ Adicionar responsável</button></div>}
      {papel === 'responsavel' && resps.length > 0 && (
        <div><button className="botao secundario" onClick={() => abrir(resps.find((r) => r.tem_conta) ?? resps[0])}>Atualizar meu contato</button></div>
      )}
      <Modal titulo={modal === 'novo' ? 'Novo responsável' : 'Editar contato'} aberto={modal !== null} fechar={() => setModal(null)}>
        <form className="pilha" onSubmit={(e) => { e.preventDefault(); salvar.mutate(); }}>
          <div className="form-grade">
            <label className="campo">Nome<input required disabled={soContato} value={f.nome} onChange={(e) => setF({...f, nome: e.target.value})} /></label>
            <label className="campo">
              Vínculo
              <select disabled={soContato} value={f.tipo} onChange={(e) => setF({...f, tipo: e.target.value})}>
                {Object.entries(NOME_VINCULO).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            <label className="campo">Telefone<input type="tel" value={f.telefone} onChange={(e) => setF({...f, telefone: e.target.value})} /></label>
            <label className="campo">E-mail<input type="email" value={f.email} onChange={(e) => setF({...f, email: e.target.value})} /></label>
          </div>
          {!soContato && (
            <div className="pilha">
              {([['pode_buscar', 'Pode buscar o aluno na escola'], ['recebe_avisos', 'Recebe avisos e mensagens'], ['emergencia', 'Contato de emergência'], ['restrito', 'Acesso restrito (ex.: decisão judicial)']] as const).map(([k, r]) => (
                <label key={k} className="check"><input type="checkbox" checked={f[k]} onChange={(e) => setF({...f, [k]: e.target.checked})} /> {r}</label>
              ))}
            </div>
          )}
          <Erro erro={salvar.error} />
          <button className="botao" disabled={salvar.isPending}>Salvar</button>
        </form>
      </Modal>
    </div>
  );
}

function SaudeAba({aluno}: {aluno: TAluno}) {
  const papel = usePapel();
  const qc = useQueryClient();
  const q = useQuery({queryKey: ['saude', aluno.id], queryFn: () => api<Saude>(`/alunos/${aluno.id}/saude`)});
  const [edit, setEdit] = useState<Saude | null>(null);
  const salvar = useMutation({
    mutationFn: () => api(`/alunos/${aluno.id}/saude`, {method: 'PUT', body: edit}),
    onSuccess: () => { qc.invalidateQueries({queryKey: ['saude', aluno.id]}); qc.invalidateQueries({queryKey: ['aluno', aluno.id]}); setEdit(null); },
  });
  if (q.isLoading) return <Carregando />;
  if (q.error) return <Erro erro={q.error} />;
  const s = q.data!;
  const podeEditar = papel === 'admin' || papel === 'responsavel';
  return (
    <div className="pilha">
      <div className="aviso atencao">
        {Icone.saude}
        <div>
          <strong>Alerta para professores</strong>
          <div>{s.alerta || 'Nenhum alerta cadastrado.'}</div>
          {papel === 'responsavel' && <div className="suave pequeno">Este resumo é definido pela escola a partir das informações abaixo.</div>}
        </div>
      </div>
      {papel === 'professor' ? (
        <p className="suave pequeno">Professores veem só o alerta resumido. Os detalhes de saúde ficam com a secretaria e a família.</p>
      ) : edit ? (
        <form className="cartao pilha" onSubmit={(e) => { e.preventDefault(); salvar.mutate(); }}>
          {papel === 'admin' && (
            <label className="campo">Alerta para professores <span className="dica">(curto, o essencial para quem está em sala)</span>
              <input maxLength={300} value={edit.alerta} onChange={(e) => setEdit({...edit, alerta: e.target.value})} />
            </label>
          )}
          {CAMPOS_SAUDE.map(([k, r]) => (
            <label key={k} className="campo">{r}
              <textarea value={(edit[k] as string) ?? ''} onChange={(e) => setEdit({...edit, [k]: e.target.value})} />
            </label>
          ))}
          <Erro erro={salvar.error} />
          <div className="linha"><button className="botao">Salvar</button><button type="button" className="botao secundario" onClick={() => setEdit(null)}>Cancelar</button></div>
        </form>
      ) : (
        <div className="cartao">
          <div className="linha entre">
            <h2>Ficha de saúde</h2>
            {podeEditar && <button className="botao secundario pequeno" onClick={() => setEdit(s)}>Editar</button>}
          </div>
          <table><tbody>
            {CAMPOS_SAUDE.map(([k, r]) => <tr key={k}><th style={{width: '40%'}}>{r}</th><td>{(s[k] as string) || <span className="suave">—</span>}</td></tr>)}
          </tbody></table>
          <p className="suave pequeno" style={{marginTop: '0.75rem'}}>🔒 Dado sensível: guardado criptografado e cada acesso fica registrado.</p>
        </div>
      )}
    </div>
  );
}

export default function Aluno() {
  const {id = ''} = useParams();
  const papel = usePapel();
  const [aba, setAba] = useState<Aba>('dados');
  const q = useQuery({queryKey: ['aluno', id], queryFn: () => api<TAluno>(`/alunos/${id}`)});
  if (q.isLoading) return <Carregando />;
  if (q.error) return <Erro erro={q.error} />;
  const a = q.data!;
  const abas: [Aba, string][] = [['dados', 'Dados']];
  if (a.responsaveis) abas.push(['familia', 'Família']);
  if (papel !== 'aluno') abas.push(['saude', 'Saúde']);
  if (a.historico) abas.push(['historico', 'Histórico']);
  const voltar = papel === 'admin' || papel === 'coordenacao' || papel === 'professor' ? '/alunos' : '/';
  return (
    <>
      <Link to={voltar} className="pequeno">← Voltar</Link>
      <div className="cartao linha" style={{margin: '0.5rem 0 1rem', flexWrap: 'nowrap'}}>
        <Avatar nome={nomeExibicao(a)} grande />
        <div style={{flex: 1}}>
          <h1 style={{margin: 0}}>{nomeExibicao(a)}</h1>
          <div className="suave">{a.turma ? `${a.turma.nome} · ${a.turma.serie}` : 'Sem turma'} · {idade(a.data_nascimento)} anos</div>
          <div className="linha" style={{gap: '0.35rem', marginTop: '0.4rem'}}>
            {a.tem_alerta_saude && <span className="selo vermelho">Alerta de saúde</span>}
            {a.situacao !== 'ativo' && <span className="selo laranja">{a.situacao}</span>}
            {a.aluno_tem_conta && <span className="selo verde">Aluno usa o app</span>}
          </div>
        </div>
      </div>
      <Abas abas={abas} ativa={aba} mudar={setAba} />
      {aba === 'dados' && <Dados aluno={a} />}
      {aba === 'familia' && <Familia aluno={a} />}
      {aba === 'saude' && <SaudeAba aluno={a} />}
      {aba === 'historico' && (
        <div className="cartao lista">
          {a.historico!.map((h) => (
            <div key={h.ano_letivo_id} className="item"><strong>{h.turma}</strong><span className="suave">{h.serie}</span><span className="selo">{h.situacao}</span></div>
          ))}
          <p className="suave pequeno">Notas, frequência e anotações de cada ano entram aqui a partir do M2.</p>
        </div>
      )}
    </>
  );
}
