import {useMutation, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {Link} from 'react-router';
import {Erro} from '../components/ui';
import {api} from '../lib/api';
import {dataBR} from '../lib/formato';

type Resultado = {
  previa: {nome: string; sobrenome: string; data_nascimento: string; ra: string | null; turma: string; responsaveis: string[]}[];
  erros: {linha: number; campo: string; mensagem: string}[];
  importados: number;
  convites?: number;
};

export default function Importar() {
  const qc = useQueryClient();
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [convites, setConvites] = useState(true);
  const [res, setRes] = useState<Resultado | null>(null);
  const enviar = useMutation({
    mutationFn: (confirmar: boolean) => {
      const form = new FormData();
      form.append('arquivo', arquivo!);
      form.append('confirmar', String(confirmar));
      form.append('enviar_convites', String(convites));
      return api<Resultado>('/importacao/alunos', {form});
    },
    onSuccess: (r) => {
      setRes(r);
      if (r.importados) qc.invalidateQueries();
    },
  });

  return (
    <>
      <div className="topo"><h1>Importar alunos</h1></div>
      <div className="cartao pilha">
        <h2>1. Prepare a planilha</h2>
        <p className="suave">
          Uma linha por aluno, com até dois responsáveis. Pode salvar do Excel ou Google Planilhas como CSV (separado por ponto e vírgula ou vírgula).
          As turmas precisam existir no ano letivo atual.
        </p>
        <div><a className="botao secundario" href="/api/importacao/modelo.csv" download>Baixar modelo CSV</a></div>
      </div>
      <div className="cartao pilha">
        <h2>2. Envie o arquivo</h2>
        <input type="file" accept=".csv,text/csv" aria-label="Arquivo CSV" onChange={(e) => { setArquivo(e.target.files?.[0] ?? null); setRes(null); }} />
        <label className="check"><input type="checkbox" checked={convites} onChange={(e) => setConvites(e.target.checked)} /> Enviar convite por e-mail aos responsáveis</label>
        <div><button className="botao" disabled={!arquivo || enviar.isPending} onClick={() => enviar.mutate(false)}>Pré-visualizar</button></div>
        <Erro erro={enviar.error} />
      </div>
      {res && res.importados > 0 && (
        <div className="aviso ok" style={{marginTop: '1rem'}}>
          {res.importados} aluno(s) importado(s){res.convites ? ` e ${res.convites} convite(s) enviado(s)` : ''}. <Link to="/alunos">Ver alunos</Link>
        </div>
      )}
      {res && res.importados === 0 && (
        <div className="cartao pilha">
          <h2>3. Confira</h2>
          {res.erros.length > 0 ? (
            <div className="aviso erro" style={{flexDirection: 'column'}}>
              <strong>{res.erros.length} problema(s) encontrados. Nada foi gravado: corrija a planilha e envie de novo.</strong>
              <div className="tabela-rolagem" style={{width: '100%'}}>
                <table>
                  <thead><tr><th>Linha</th><th>Coluna</th><th>Problema</th></tr></thead>
                  <tbody>{res.erros.map((e, i) => <tr key={i}><td>{e.linha}</td><td>{e.campo}</td><td>{e.mensagem}</td></tr>)}</tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="aviso ok">Tudo certo com {res.previa.length} aluno(s). Confira e confirme.</div>
          )}
          {res.previa.length > 0 && (
            <div className="tabela-rolagem">
              <table>
                <thead><tr><th>Aluno</th><th>Nascimento</th><th>RA</th><th>Turma</th><th>Responsáveis</th></tr></thead>
                <tbody>
                  {res.previa.map((p, i) => (
                    <tr key={i}><td>{p.nome} {p.sobrenome}</td><td>{dataBR(p.data_nascimento)}</td><td>{p.ra}</td><td>{p.turma}</td><td>{p.responsaveis.join(', ')}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {res.erros.length === 0 && <div><button className="botao" disabled={enviar.isPending} onClick={() => enviar.mutate(true)}>Confirmar importação</button></div>}
        </div>
      )}
    </>
  );
}
