import {useMutation, useQueryClient} from '@tanstack/react-query';
import QRCode from 'qrcode';
import {useEffect, useState} from 'react';
import {Navigate, useNavigate} from 'react-router';
import {Carregando, Erro} from '../components/ui';
import {api} from '../lib/api';
import {useMe, useSair, useTrocaPerfil} from '../lib/auth';
import {NOME_PAPEL} from '../lib/formato';
import {TelaEntrada} from './Entrar';

export function Configurar2fa() {
  const {data: me, isLoading} = useMe();
  const qc = useQueryClient();
  const nav = useNavigate();
  const [qr, setQr] = useState<{img: string; secret: string} | null>(null);
  const [codigo, setCodigo] = useState('');
  const iniciar = useMutation({
    mutationFn: () => api<{secret: string; uri: string}>('/auth/2fa/iniciar', {method: 'POST'}),
    onSuccess: async (r) => setQr({img: await QRCode.toDataURL(r.uri, {margin: 1, width: 220}), secret: r.secret}),
  });
  const ativar = useMutation({
    mutationFn: () => api('/auth/2fa/ativar', {body: {codigo}}),
    onSuccess: async () => {
      await qc.invalidateQueries({queryKey: ['me']});
      nav('/', {replace: true});
    },
  });
  const precisa = me?.status === 'configurar_2fa';
  const {mutate} = iniciar;
  useEffect(() => {
    if (precisa) mutate();
  }, [precisa, mutate]);

  if (isLoading) return <Carregando />;
  if (!me) return <Navigate to="/entrar" replace />;
  if (!precisa) return <Navigate to="/" replace />;
  return (
    <TelaEntrada titulo="Proteja sua conta">
      <p className="suave">
        Contas da equipe da escola acessam dados de alunos, por isso usam verificação em duas etapas. Escaneie o código com um
        aplicativo autenticador (Google Authenticator, Microsoft Authenticator, 2FAS…).
      </p>
      {qr ? (
        <div style={{textAlign: 'center'}}>
          <img src={qr.img} alt="QR code para o aplicativo autenticador" width={220} height={220} style={{background: '#fff', borderRadius: 8}} />
          <p className="suave pequeno">
            Ou digite a chave: <code style={{wordBreak: 'break-all'}}>{qr.secret}</code>
          </p>
        </div>
      ) : (
        <Carregando />
      )}
      <form
        className="pilha"
        onSubmit={(e) => {
          e.preventDefault();
          ativar.mutate();
        }}>
        <label className="campo">
          Código de 6 dígitos
          <input inputMode="numeric" autoComplete="one-time-code" required maxLength={8} value={codigo} onChange={(e) => setCodigo(e.target.value)} />
        </label>
        <Erro erro={ativar.error ?? iniciar.error} />
        <button className="botao largo" disabled={ativar.isPending}>Ativar e continuar</button>
      </form>
    </TelaEntrada>
  );
}

export function EscolherPerfil() {
  const {data: me, isLoading} = useMe();
  const troca = useTrocaPerfil();
  const sair = useSair();
  const nav = useNavigate();
  if (isLoading) return <Carregando />;
  if (!me || me.status !== 'ok') return <Navigate to="/entrar" replace />;
  return (
    <TelaEntrada titulo={`Olá, ${me.usuario.nome.split(' ')[0]}!`}>
      <p className="suave" style={{textAlign: 'center'}}>Com qual perfil você quer entrar?</p>
      {me.perfis.length === 0 && <div className="aviso atencao">Sua conta não tem nenhum acesso ativo. Fale com a escola.</div>}
      <div className="pilha">
        {me.perfis.map((p) => (
          <button
            key={p.id}
            className="botao secundario largo"
            style={{justifyContent: 'flex-start', flexDirection: 'column', alignItems: 'flex-start'}}
            onClick={() => troca.mutate(p.id, {onSuccess: () => nav('/', {replace: true})})}>
            <strong>{NOME_PAPEL[p.papel]}</strong>
            <span className="suave pequeno">{p.escola}</span>
          </button>
        ))}
      </div>
      <Erro erro={troca.error} />
      <button className="botao secundario pequeno" onClick={() => sair.mutate()}>Sair</button>
    </TelaEntrada>
  );
}
