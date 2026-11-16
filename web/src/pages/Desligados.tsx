import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Abas, Carregando, Erro, Modal, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import {NOME_PAPEL, NOME_SITUACAO, dataBR} from '../lib/formato';
import type {Desligados as Dados, ItemDesligado} from '../lib/tipos';

function Situacao({i}: {i: ItemDesligado}) {
  if (i.status === 'concluido') return <span className="selo verde">Feito em {dataBR(i.concluido_em)}</span>;
  const d = Math.max(i.dias_restantes ?? 0, 0);
  return (
    <div>
      <span className={`selo ${i.status === 'avisado' ? 'vermelho' : ''}`}>{i.status === 'avisado' ? `Avisado · em ${d} dia(s)` : `Em ${d} dia(s)`}</span>
      <div className="suave pequeno">{dataBR(i.prevista)}{i.adiado && ' · adiado'}</div>
    </div>
  );
}

function Config({dados, aberto, fechar}: {dados: Dados['config']; aberto: boolean; fechar: () => void}) {
  const qc = useQueryClient();
  const [f, setF] = useState(dados);
  const salva = useMutation({
    mutationFn: () => api('/desligados/config', {method: 'PUT', body: f}),
    onSuccess: () => { qc.invalidateQueries({queryKey: ['desligados']}); fechar(); },
  });
  return (
    <Modal titulo="Prazos" aberto={aberto} fechar={fechar}>
      <form className="pilha" onSubmit={(e) => { e.preventDefault(); salva.mutate(); }}>
        <label className="campo">Apagar dados complementares do aluno após (dias)<input type="number" min={30} max={3650} value={f.retencao_aluno_dias} onChange={(e) => setF({...f, retencao_aluno_dias: Number(e.target.value)})} /></label>
        <label className="campo">Anonimizar a conta de usuário desligado após (dias)<input type="number" min={30} max={3650} value={f.retencao_usuario_dias} onChange={(e) => setF({...f, retencao_usuario_dias: Number(e.target.value)})} /></label>
        <label className="campo">Avisar a direção com antecedência de (dias)<input type="number" min={7} max={90} value={f.aviso_dias} onChange={(e) => setF({...f, aviso_dias: Number(e.target.value)})} /></label>
        <p className="suave pequeno" style={{margin: 0}}>Nada é apagado sem o aviso. Confirme com o jurídico o prazo mínimo de guarda do histórico escolar da sua rede de ensino.</p>
        <Erro erro={salva.error} />
        <button className="botao" disabled={salva.isPending}>Salvar</button>
      </form>
    </Modal>
  );
}

export default function Desligados() {
  const papel = usePapel();
  const admin = papel === 'admin';
  const qc = useQueryClient();
  const q = useQuery({queryKey: ['desligados'], queryFn: () => api<Dados>('/desligados')});
  const [aba, setAba] = useState<'alunos' | 'usuarios'>('alunos');
  const [config, setConfig] = useState(false);
  const [dias, setDias] = useState<Record<string, string>>({});
  const recarrega = () => qc.invalidateQueries({queryKey: ['desligados']});
  const adia = useMutation({
    mutationFn: ({tipo, id}: {tipo: 'alunos' | 'usuarios'; id: string}) => api(`/desligados/${tipo}/${id}/adiar`, {body: {dias: Number(dias[id] ?? 90)}}),
    onSuccess: recarrega,
  });
  const apaga = useMutation({mutationFn: (id: string) => api(`/desligados/alunos/${id}/apagar-agora`, {body: {confirmacao: 'APAGAR'}}), onSuccess: recarrega});
  const escolhe = (id: string) => (
    <select aria-label="Adiar por" value={dias[id] ?? '90'} onChange={(e) => setDias({...dias, [id]: e.target.value})} style={{marginTop: 0, width: 'auto'}}>
      <option value="30">30 dias</option><option value="90">90 dias</option><option value="180">180 dias</option><option value="365">1 ano</option>
    </select>
  );
  const d = q.data;
  return (
    <>
      <div className="topo">
        <h1>Desligados</h1>
        {admin && d && <button className="botao secundario" onClick={() => setConfig(true)}>Prazos</button>}
      </div>
      <div className="cartao pilha">
        <p style={{margin: 0}}>Depois do prazo, os dados <strong>complementares</strong> de alunos desligados são apagados e as contas de usuários desligados são anonimizadas. A direção é <strong>avisada antes</strong>{d && <> ({d.config.aviso_dias} dias)</>} e pode adiar.</p>
        <div className="form-grade">
          <div><strong>Fica (histórico)</strong><div className="suave pequeno">Nome, nascimento, RA, matrículas, notas, frequência e os históricos escolares emitidos.</div></div>
          <div><strong>Sai</strong><div className="suave pequeno">Ficha de saúde, anotações e versões, mensagens e anexos, contatos dos responsáveis, respostas de autorização, CPF e justificativas de falta.</div></div>
          <div><strong>Contas</strong><div className="suave pequeno">Nome, e-mail, telefone, senha e sessões são removidos. O que a pessoa escreveu continua, como "Ex-usuário".</div></div>
        </div>
      </div>
      {q.isLoading && <Carregando />}
      <Erro erro={q.error || adia.error || apaga.error} />
      {d && (
        <>
          <div style={{margin: '1rem 0 0.5rem'}}>
            <Abas abas={[['alunos', `Alunos (${d.alunos.length})`], ['usuarios', `Usuários (${d.usuarios.length})`]]} ativa={aba} mudar={setAba} />
          </div>
          {aba === 'alunos' && (d.alunos.length === 0 ? <Vazio>Nenhum aluno desligado.</Vazio> : (
            <table>
              <thead><tr><th>Aluno</th><th>Situação</th><th>Desligado em</th><th>Dados complementares</th>{admin && <th>Ações</th>}</tr></thead>
              <tbody>
                {d.alunos.map((a) => (
                  <tr key={a.id}>
                    <td>{a.nome}</td><td>{NOME_SITUACAO[a.situacao] ?? a.situacao}</td><td>{dataBR(a.desligado_em)}</td><td><Situacao i={a} /></td>
                    {admin && (
                      <td>
                        {a.status !== 'concluido' && (
                          <div className="linha">
                            {escolhe(a.id)}
                            <button className="botao secundario pequeno" disabled={adia.isPending} onClick={() => adia.mutate({tipo: 'alunos', id: a.id})}>Adiar</button>
                            <button className="botao secundario pequeno" disabled={apaga.isPending} onClick={() => window.prompt(`Apagar agora os dados complementares de ${a.nome}? Não dá para desfazer. Digite APAGAR para confirmar.`) === 'APAGAR' && apaga.mutate(a.id)}>Apagar agora</button>
                          </div>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          ))}
          {aba === 'usuarios' && (d.usuarios.length === 0 ? <Vazio>Nenhum usuário desligado.</Vazio> : (
            <>
              <p className="suave pequeno">Se a pessoa ainda tem acesso ativo em outra escola, a conta não é anonimizada (só o vínculo com esta escola fica inativo).</p>
              <table>
                <thead><tr><th>Usuário</th><th>Perfil</th><th>Desligado em</th><th>Anonimização</th>{admin && <th>Ações</th>}</tr></thead>
                <tbody>
                  {d.usuarios.map((u) => (
                    <tr key={u.perfil_id}>
                      <td>{u.nome}</td><td>{NOME_PAPEL[u.papel]}</td><td>{dataBR(u.desligado_em)}</td><td><Situacao i={u} /></td>
                      {admin && (
                        <td>
                          {u.status !== 'concluido' && (
                            <div className="linha">
                              {escolhe(u.perfil_id)}
                              <button className="botao secundario pequeno" disabled={adia.isPending} onClick={() => adia.mutate({tipo: 'usuarios', id: u.perfil_id})}>Adiar</button>
                            </div>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ))}
          {admin && <Config key={String(config)} dados={d.config} aberto={config} fechar={() => setConfig(false)} />}
        </>
      )}
    </>
  );
}
