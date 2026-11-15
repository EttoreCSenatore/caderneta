import {useQueryClient} from '@tanstack/react-query';
import {type FormEvent, type ReactNode, useState} from 'react';
import {Link, Navigate, useLocation, useNavigate, useSearchParams} from 'react-router';
import {Erro} from '../components/ui';
import {api} from '../lib/api';
import {useMe} from '../lib/auth';

export function TelaEntrada({titulo, children}: {titulo?: string; children: ReactNode}) {
  return (
    <div className="tela-entrada">
      <div className="cartao pilha">
        <div className="marca">
          <img src="/icon.svg" alt="" /> Caderneta
        </div>
        {titulo && <h1 style={{textAlign: 'center', fontSize: '1.2rem'}}>{titulo}</h1>}
        {children}
      </div>
    </div>
  );
}

export function Entrar() {
  const {data: me} = useMe();
  const qc = useQueryClient();
  const nav = useNavigate();
  const de = (useLocation().state as {de?: string} | null)?.de ?? '/';
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [codigo, setCodigo] = useState('');
  const [erro, setErro] = useState<unknown>(null);
  const [enviando, setEnviando] = useState(false);

  if (me?.status === 'ok') return <Navigate to={de} replace />;
  if (me?.status === 'configurar_2fa') return <Navigate to="/configurar-2fa" replace />;
  const etapaCodigo = me?.status === 'codigo';

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const r = etapaCodigo
        ? await api<{status: string}>('/auth/codigo', {body: {codigo}})
        : await api<{status: string}>('/auth/login', {body: {email, senha}});
      await qc.invalidateQueries({queryKey: ['me']});
      // Com 2FA ativo, a mesma tela passa para a etapa do código (sem navegar).
      if (r.status === 'ok') nav(de, {replace: true});
      else if (r.status === 'configurar_2fa') nav('/configurar-2fa', {replace: true});
    } catch (ex) {
      setErro(ex);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <TelaEntrada titulo={etapaCodigo ? 'Verificação em duas etapas' : undefined}>
      <form className="pilha" onSubmit={enviar}>
        {etapaCodigo ? (
          <>
            <p className="suave">Digite o código de 6 dígitos do seu aplicativo autenticador.</p>
            <label className="campo">
              Código
              <input inputMode="numeric" autoComplete="one-time-code" autoFocus required maxLength={8} value={codigo} onChange={(e) => setCodigo(e.target.value)} />
            </label>
          </>
        ) : (
          <>
            <p className="suave" style={{textAlign: 'center'}}>Notas, avisos e calendário da escola num só lugar.</p>
            <label className="campo">
              E-mail
              <input type="email" autoComplete="username" required autoFocus value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <label className="campo">
              Senha
              <input type="password" autoComplete="current-password" required value={senha} onChange={(e) => setSenha(e.target.value)} />
            </label>
          </>
        )}
        <Erro erro={erro} />
        <button className="botao largo" disabled={enviando}>{enviando ? 'Entrando…' : etapaCodigo ? 'Confirmar' : 'Entrar'}</button>
        {!etapaCodigo && (
          <p className="pequeno" style={{textAlign: 'center'}}>
            <Link to="/esqueci-senha">Esqueci minha senha</Link>
          </p>
        )}
        <p className="suave pequeno" style={{textAlign: 'center'}}>
          Não tem conta? O acesso é feito por convite da escola.
        </p>
      </form>
    </TelaEntrada>
  );
}

export function Esqueci() {
  const [email, setEmail] = useState('');
  const [feito, setFeito] = useState(false);
  const [erro, setErro] = useState<unknown>(null);
  return (
    <TelaEntrada titulo="Recuperar senha">
      {feito ? (
        <div className="aviso ok">Se o e-mail estiver cadastrado, você vai receber um link para criar uma nova senha.</div>
      ) : (
        <form
          className="pilha"
          onSubmit={async (e) => {
            e.preventDefault();
            try {
              await api('/auth/senha/esqueci', {body: {email}});
              setFeito(true);
            } catch (ex) {
              setErro(ex);
            }
          }}>
          <label className="campo">
            E-mail
            <input type="email" required autoFocus value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <Erro erro={erro} />
          <button className="botao largo">Enviar link</button>
        </form>
      )}
      <p className="pequeno" style={{textAlign: 'center'}}>
        <Link to="/entrar">Voltar para entrar</Link>
      </p>
    </TelaEntrada>
  );
}

export function CamposSenha({senha, setSenha, confirma, setConfirma}: {senha: string; setSenha: (s: string) => void; confirma: string; setConfirma: (s: string) => void}) {
  return (
    <>
      <label className="campo">
        Nova senha <span className="dica">(mínimo 10 caracteres, com letras e números)</span>
        <input type="password" autoComplete="new-password" required minLength={10} value={senha} onChange={(e) => setSenha(e.target.value)} />
      </label>
      <label className="campo">
        Repita a senha
        <input type="password" autoComplete="new-password" required value={confirma} onChange={(e) => setConfirma(e.target.value)} />
      </label>
    </>
  );
}

export function Redefinir() {
  const [params] = useSearchParams();
  const [senha, setSenha] = useState('');
  const [confirma, setConfirma] = useState('');
  const [erro, setErro] = useState<unknown>(null);
  const [feito, setFeito] = useState(false);
  return (
    <TelaEntrada titulo="Criar nova senha">
      {feito ? (
        <div className="aviso ok">Senha alterada. <Link to="/entrar">Entrar</Link></div>
      ) : (
        <form
          className="pilha"
          onSubmit={async (e) => {
            e.preventDefault();
            if (senha !== confirma) return setErro(new Error('As senhas não conferem.'));
            try {
              await api('/auth/senha/redefinir', {body: {token: params.get('token') ?? '', senha}});
              setFeito(true);
            } catch (ex) {
              setErro(ex);
            }
          }}>
          <CamposSenha senha={senha} setSenha={setSenha} confirma={confirma} setConfirma={setConfirma} />
          <Erro erro={erro} />
          <button className="botao largo">Salvar senha</button>
        </form>
      )}
    </TelaEntrada>
  );
}
