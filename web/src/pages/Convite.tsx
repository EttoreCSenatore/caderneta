import {useQuery, useQueryClient} from '@tanstack/react-query';
import {useState} from 'react';
import {useNavigate, useParams} from 'react-router';
import {Carregando, Erro} from '../components/ui';
import {api} from '../lib/api';
import {NOME_PAPEL} from '../lib/formato';
import type {Papel} from '../lib/tipos';
import {CamposSenha, TelaEntrada} from './Entrar';

type Info = {nome: string; email: string; papel: Papel; escola: string; aluno: string | null; conta_existente: boolean};

export function Convite() {
  const {token = ''} = useParams();
  const qc = useQueryClient();
  const nav = useNavigate();
  const info = useQuery({queryKey: ['convite', token], queryFn: () => api<Info>(`/convites/abrir/${token}`), retry: false});
  const [nome, setNome] = useState<string | null>(null);
  const [senha, setSenha] = useState('');
  const [confirma, setConfirma] = useState('');
  const [erro, setErro] = useState<unknown>(null);

  if (info.isLoading) return <Carregando />;
  if (info.error || !info.data)
    return (
      <TelaEntrada titulo="Convite">
        <Erro erro={info.error} />
        <p className="suave">Peça à escola um novo convite.</p>
      </TelaEntrada>
    );
  const c = info.data;
  return (
    <TelaEntrada titulo={`Bem-vindo(a) à ${c.escola}`}>
      <p style={{textAlign: 'center'}}>
        Você foi convidado(a) como <strong>{NOME_PAPEL[c.papel].toLowerCase()}</strong>
        {c.aluno && <> de <strong>{c.aluno}</strong></>}.
      </p>
      <form
        className="pilha"
        onSubmit={async (e) => {
          e.preventDefault();
          if (!c.conta_existente && senha !== confirma) return setErro(new Error('As senhas não conferem.'));
          try {
            await api(`/convites/abrir/${token}`, {body: {nome: nome ?? c.nome, senha}});
            await qc.invalidateQueries({queryKey: ['me']});
            nav('/', {replace: true});
          } catch (ex) {
            setErro(ex);
          }
        }}>
        <label className="campo">
          E-mail
          <input value={c.email} readOnly />
        </label>
        {c.conta_existente ? (
          <>
            <div className="aviso atencao">Você já tem uma conta na Caderneta. Confirme com sua senha para adicionar este acesso.</div>
            <label className="campo">
              Senha atual
              <input type="password" autoComplete="current-password" required value={senha} onChange={(e) => setSenha(e.target.value)} />
            </label>
          </>
        ) : (
          <>
            <label className="campo">
              Seu nome
              <input required value={nome ?? c.nome} onChange={(e) => setNome(e.target.value)} />
            </label>
            <CamposSenha senha={senha} setSenha={setSenha} confirma={confirma} setConfirma={setConfirma} />
          </>
        )}
        <Erro erro={erro} />
        <button className="botao largo">{c.conta_existente ? 'Adicionar acesso' : 'Criar acesso'}</button>
      </form>
    </TelaEntrada>
  );
}
