import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {type FormEvent, useState} from 'react';
import {Carregando, Erro, Vazio} from '../components/ui';
import {api, baixarArquivo} from '../lib/api';
import {useMe, usePapel} from '../lib/auth';
import {dataBR} from '../lib/formato';
import type {Aluno, PedidoTitular} from '../lib/tipos';
import {Encarregado} from './Legal';

export const ROTULO_TIPO: Record<string, string> = {
  acesso: 'Acesso aos meus dados',
  correcao: 'Correção de dado errado',
  eliminacao: 'Eliminação (apagar) dados',
  portabilidade: 'Levar meus dados para outro lugar',
  informacao: 'Saber com quem os dados são compartilhados',
  revogacao: 'Retirar um consentimento',
  outro: 'Outro assunto sobre meus dados',
};
export const ROTULO_STATUS: Record<string, string> = {aberto: 'Aberto', em_analise: 'Em análise', atendido: 'Atendido', em_parte: 'Atendido em parte', negado: 'Não atendido'};

export function SeloPrazo({p}: {p: PedidoTitular}) {
  if (p.status === 'atendido' || p.status === 'em_parte' || p.status === 'negado') return <span className="selo verde">{ROTULO_STATUS[p.status]}</span>;
  if (p.vencido) return <span className="selo vermelho">Prazo vencido</span>;
  return <span className="selo laranja">{ROTULO_STATUS[p.status]} · {p.dias_restantes} dia(s) de prazo</span>;
}

function Baixar({filhos}: {filhos: Aluno[]}) {
  const [senha, setSenha] = useState('');
  const [quem, setQuem] = useState('');
  const baixa = useMutation({
    mutationFn: () => baixarArquivo('/meus-dados/exportar', 'meus-dados.json', {senha, aluno_id: quem || null}),
    onSuccess: () => setSenha(''),
  });
  const enviar = (e: FormEvent) => {
    e.preventDefault();
    baixa.mutate();
  };
  return (
    <form className="cartao pilha" onSubmit={enviar}>
      <h2 style={{margin: 0}}>Baixar meus dados</h2>
      <p className="suave" style={{margin: 0}}>Um arquivo com o que a escola guarda sobre você, de que forma e para quê. Por segurança, confirme sua senha.</p>
      {filhos.length > 0 && (
        <label className="campo">
          De quem
          <select value={quem} onChange={(e) => setQuem(e.target.value)}>
            <option value="">Meus dados de usuário</option>
            {filhos.map((a) => <option key={a.id} value={a.id}>Dados de {a.nome} {a.sobrenome}</option>)}
          </select>
        </label>
      )}
      <label className="campo">Senha<input type="password" autoComplete="current-password" required value={senha} onChange={(e) => setSenha(e.target.value)} /></label>
      <Erro erro={baixa.error} />
      <div><button className="botao" disabled={baixa.isPending}>Baixar arquivo</button></div>
    </form>
  );
}

function NovoPedido({filhos}: {filhos: Aluno[]}) {
  const qc = useQueryClient();
  const [f, setF] = useState({tipo: 'acesso', descricao: '', aluno_id: ''});
  const cria = useMutation({
    mutationFn: () => api('/meus-dados/pedidos', {body: {tipo: f.tipo, descricao: f.descricao, aluno_id: f.aluno_id || null}}),
    onSuccess: () => {
      setF({tipo: 'acesso', descricao: '', aluno_id: ''});
      qc.invalidateQueries({queryKey: ['meus-pedidos']});
    },
  });
  return (
    <form className="cartao pilha" onSubmit={(e) => { e.preventDefault(); cria.mutate(); }}>
      <h2 style={{margin: 0}}>Fazer um pedido à escola</h2>
      <p className="suave" style={{margin: 0}}>A escola responde em até <strong>15 dias</strong> (Lei Geral de Proteção de Dados, art. 19). Você acompanha aqui.</p>
      <div className="form-grade">
        <label className="campo">Assunto<select value={f.tipo} onChange={(e) => setF({...f, tipo: e.target.value})}>{Object.entries(ROTULO_TIPO).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
        {filhos.length > 0 && (
          <label className="campo">Sobre
            <select value={f.aluno_id} onChange={(e) => setF({...f, aluno_id: e.target.value})}>
              <option value="">Meus dados</option>
              {filhos.map((a) => <option key={a.id} value={a.id}>{a.nome} {a.sobrenome}</option>)}
            </select>
          </label>
        )}
      </div>
      <label className="campo">Explique o pedido<textarea required minLength={10} maxLength={2000} rows={4} value={f.descricao} onChange={(e) => setF({...f, descricao: e.target.value})} /></label>
      <Erro erro={cria.error} />
      <div><button className="botao" disabled={cria.isPending}>Enviar pedido</button></div>
    </form>
  );
}

export default function MeusDados() {
  const papel = usePapel();
  const {data: me} = useMe();
  const familia = papel === 'responsavel' || papel === 'aluno';
  const alunos = useQuery({queryKey: ['alunos', ''], queryFn: () => api<Aluno[]>('/alunos'), enabled: familia});
  const pedidos = useQuery({queryKey: ['meus-pedidos'], queryFn: () => api<PedidoTitular[]>('/meus-dados/pedidos')});
  if (!me) return <Carregando />;
  const filhos = familia ? (alunos.data ?? []) : [];
  return (
    <>
      <div className="topo"><div><h1>Meus dados</h1><div className="suave">Seus direitos sobre os dados pessoais (LGPD, art. 18)</div></div></div>
      <div className="pilha">
        <div className="cartao pilha">
          <h2 style={{margin: 0}}>O que a escola faz com os dados</h2>
          <p style={{margin: 0}}>A <strong>escola</strong> decide como os dados são usados; a Caderneta só os guarda e processa para ela. Usamos para notas, frequência, avisos, calendário, provas, histórico escolar e segurança da conta. Não vendemos dados nem fazemos propaganda.
            Saúde e dados de menores têm proteção reforçada. Você pode baixar seus dados, pedir correção, pedir eliminação (o histórico escolar, porém, a escola precisa guardar por lei) e saber com quem os dados são compartilhados.</p>
        </div>
        <Encarregado />
        <p className="suave" style={{margin: 0}}>Leia a <a href="/privacidade">política de privacidade</a> e os <a href="/termos">termos de uso</a>.</p>
        <Baixar filhos={filhos} />
        <NovoPedido filhos={filhos} />
        <div className="cartao pilha">
          <h2 style={{margin: 0}}>Meus pedidos</h2>
          {pedidos.isLoading && <Carregando />}
          {pedidos.data?.length === 0 && <Vazio>Você ainda não fez nenhum pedido.</Vazio>}
          <div className="lista">
            {pedidos.data?.map((p) => (
              <div key={p.id} className="item" style={{display: 'block'}}>
                <div className="linha entre"><strong>{ROTULO_TIPO[p.tipo]}{p.aluno ? ` · ${p.aluno}` : ''}</strong><SeloPrazo p={p} /></div>
                <div className="suave pequeno">Pedido em {dataBR(p.recebido_em.slice(0, 10))} · resposta até {dataBR(p.prazo_em.slice(0, 10))}</div>
                <div>{p.descricao}</div>
                {p.resposta && <div className="aviso ok" style={{marginTop: '0.5rem'}}>Resposta da escola: {p.resposta}</div>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
