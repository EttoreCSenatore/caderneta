import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {useEffect, useState} from 'react';
import {Carregando, Erro, Vazio} from '../components/ui';
import {api} from '../lib/api';
import {usePapel} from '../lib/auth';
import type {AnoLetivo, PreviaRematricula, TurmaResumo} from '../lib/tipos';

type Resultado = '' | 'aprovado' | 'retido' | 'transferido' | 'concluiu';
type Linha = {resultado: Resultado; destino: string};
const COR = {aprovado: 'verde', retido: 'vermelho', pendente: 'laranja'} as const;

function Rematricula({anoDestino, anoAtual}: {anoDestino: AnoLetivo; anoAtual: AnoLetivo}) {
  const qc = useQueryClient();
  const turmas = useQuery({queryKey: ['turmas'], queryFn: () => api<TurmaResumo[]>('/turmas')});
  const [turma, setTurma] = useState('');
  const previa = useQuery({
    queryKey: ['previa', turma, anoDestino.id],
    queryFn: () => api<PreviaRematricula>(`/rematricula/previa?turma_id=${turma}&ano_destino_id=${anoDestino.id}`),
    enabled: !!turma,
  });
  const [linhas, setLinhas] = useState<Record<string, Linha>>({});
  useEffect(() => {
    if (!previa.data) return;
    setLinhas(Object.fromEntries(previa.data.alunos.map((a) => [a.aluno_id, {resultado: (a.sugestao === 'pendente' ? '' : a.sugestao) as Resultado, destino: a.turma_destino_sugerida ?? ''}])));
  }, [previa.data]);
  const [ok, setOk] = useState('');
  const aplica = useMutation({
    mutationFn: () => api<{processados: number}>('/rematricula', {body: {
      turma_origem_id: turma, ano_destino_id: anoDestino.id,
      itens: previa.data!.alunos.filter((a) => !a.ja_rematriculado && linhas[a.aluno_id]?.resultado).map((a) => {
        const l = linhas[a.aluno_id];
        return {aluno_id: a.aluno_id, resultado: l.resultado, turma_destino_id: l.resultado === 'aprovado' || l.resultado === 'retido' ? l.destino || null : null};
      }),
    }}),
    onSuccess: (r) => { setOk(`${r.processados} aluno(s) processado(s).`); qc.invalidateQueries({queryKey: ['previa']}); qc.invalidateQueries({queryKey: ['turmas']}); },
  });
  const turmasAtuais = (turmas.data ?? []);
  const pend = previa.data?.alunos.filter((a) => !a.ja_rematriculado && !linhas[a.aluno_id]?.resultado).length ?? 0;
  return (
    <section className="cartao pilha">
      <h2 style={{margin: 0}}>2. Rematrícula em lote</h2>
      <label className="campo">Turma de {anoAtual.ano}
        <select value={turma} onChange={(e) => { setTurma(e.target.value); setOk(''); }}>
          <option value="">Escolha a turma</option>
          {turmasAtuais.map((t) => <option key={t.id} value={t.id}>{t.nome} · {t.serie} ({t.alunos} alunos)</option>)}
        </select>
      </label>
      {previa.isLoading && <Carregando />}
      <Erro erro={previa.error} />
      {previa.data && (
        <>
          {previa.data.ultima_serie && <p className="suave pequeno" style={{margin: 0}}>Última série do ensino fundamental: quem passa deve ser marcado como "Concluiu".</p>}
          <table>
            <thead><tr><th>Aluno</th><th>Sugestão do boletim</th><th>Resultado</th><th>Turma em {anoDestino.ano}</th></tr></thead>
            <tbody>
              {previa.data.alunos.map((a) => {
                const l = linhas[a.aluno_id] ?? {resultado: '' as Resultado, destino: ''};
                const segue = l.resultado === 'aprovado' || l.resultado === 'retido';
                return (
                  <tr key={a.aluno_id}>
                    <td>{a.nome}</td>
                    <td><span className={`selo ${COR[a.sugestao]}`}>{a.sugestao}</span>{a.motivo && <div className="suave pequeno">{a.motivo}</div>}</td>
                    <td>
                      {a.ja_rematriculado ? <span className="selo">já rematriculado</span> : (
                        <select aria-label={`Resultado de ${a.nome}`} value={l.resultado} onChange={(e) => setLinhas({...linhas, [a.aluno_id]: {...l, resultado: e.target.value as Resultado}})} style={{marginTop: 0}}>
                          <option value="">Decidir</option><option value="aprovado">Aprovado</option><option value="retido">Retido</option><option value="transferido">Transferido</option><option value="concluiu">Concluiu</option>
                        </select>
                      )}
                    </td>
                    <td>
                      {segue && !a.ja_rematriculado && (
                        <select aria-label={`Turma de ${a.nome}`} value={l.destino} onChange={(e) => setLinhas({...linhas, [a.aluno_id]: {...l, destino: e.target.value}})} style={{marginTop: 0}}>
                          <option value="">Escolha</option>
                          {previa.data!.turmas_destino.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
                        </select>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <Erro erro={aplica.error} />
          {ok && <span className="selo verde" role="status">{ok}</span>}
          <div className="linha">
            <button className="botao" disabled={aplica.isPending || pend > 0} onClick={() => aplica.mutate()}>Aplicar rematrícula</button>
            {pend > 0 && <span className="suave pequeno">{pend} aluno(s) sem decisão</span>}
          </div>
        </>
      )}
    </section>
  );
}

export default function Virada() {
  const papel = usePapel();
  const qc = useQueryClient();
  const anos = useQuery({queryKey: ['anos'], queryFn: () => api<AnoLetivo[]>('/anos-letivos')});
  const lista = [...(anos.data ?? [])].sort((a, b) => b.ano - a.ano);
  const abertos = lista.filter((a) => a.aberto);
  const atual = abertos.length > 1 ? abertos[abertos.length - 1] : abertos[0];
  const destino = lista.find((a) => atual && a.ano > atual.ano);
  const [msg, setMsg] = useState('');
  const turmas = useMutation({
    mutationFn: () => api<{criadas: string[]}>(`/anos-letivos/${destino!.id}/turmas-do-ano`, {body: {de_ano_letivo_id: atual!.id}}),
    onSuccess: (r) => { setMsg(r.criadas.length ? `Turmas criadas: ${r.criadas.join(', ')}.` : 'Nenhuma turma nova (já existiam).'); qc.invalidateQueries({queryKey: ['turmas']}); },
  });
  const encerra = useMutation({
    mutationFn: () => api(`/anos-letivos/${atual!.id}/encerrar`, {body: {abrir_ano_id: destino!.id}}),
    onSuccess: () => { qc.invalidateQueries(); },
  });
  if (anos.isLoading) return <Carregando />;
  return (
    <>
      <div className="topo"><h1>Virada de ano</h1></div>
      <Erro erro={anos.error} />
      {!atual && <Vazio>Nenhum ano letivo aberto.</Vazio>}
      {atual && !destino && <Vazio>Crie o ano letivo seguinte em Escola para começar a virada de {atual.ano}.</Vazio>}
      {atual && destino && (
        <div className="pilha">
          <p className="suave" style={{margin: 0}}>De <strong>{atual.ano}</strong> para <strong>{destino.ano}</strong>. Notas, frequência e anotações de {atual.ano} permanecem no histórico de cada aluno.</p>
          <section className="cartao pilha">
            <h2 style={{margin: 0}}>1. Turmas de {destino.ano}</h2>
            <p className="suave pequeno" style={{margin: 0}}>Cria as turmas com a série seguinte (7º A vira 8º A) e copia os professores. Quem repete precisa de turma da mesma série: crie em Turmas.</p>
            <Erro erro={turmas.error} />
            {msg && <span className="selo verde" role="status">{msg}</span>}
            <div><button className="botao secundario" disabled={papel !== 'admin' || turmas.isPending} onClick={() => turmas.mutate()}>Criar turmas a partir de {atual.ano}</button>{papel !== 'admin' && <span className="suave pequeno"> Só a direção cria turmas.</span>}</div>
          </section>
          <Rematricula anoDestino={destino} anoAtual={atual} />
          <section className="cartao pilha">
            <h2 style={{margin: 0}}>3. Encerrar {atual.ano} e abrir {destino.ano}</h2>
            <p className="suave pequeno" style={{margin: 0}}>Exige todos os períodos fechados. {destino.ano} passa a ser o ano atual, e os professores de {atual.ano} deixam de ver os alunos que não são mais deles.</p>
            <Erro erro={encerra.error} />
            <div><button className="botao secundario" disabled={papel !== 'admin' || encerra.isPending} onClick={() => window.confirm(`Encerrar ${atual.ano} e abrir ${destino.ano}?`) && encerra.mutate()}>Encerrar {atual.ano} e abrir {destino.ano}</button></div>
          </section>
        </div>
      )}
    </>
  );
}
