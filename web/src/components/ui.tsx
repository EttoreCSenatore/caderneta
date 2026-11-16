import {type ReactNode, useEffect, useState} from 'react';
import {iniciais} from '../lib/formato';

export function Carregando() {
  return <div className="carregando" role="status">Carregando…</div>;
}

export function Erro({erro}: {erro: unknown}) {
  if (!erro) return null;
  const msg = erro instanceof Error ? erro.message : String(erro);
  return <div className="aviso erro" role="alert">{msg}</div>;
}

export function Vazio({children}: {children: ReactNode}) {
  return <div className="vazio">{children}</div>;
}

export function Avatar({nome, grande}: {nome: string; grande?: boolean}) {
  return <div className={`avatar${grande ? ' grande' : ''}`} aria-hidden="true">{iniciais(nome)}</div>;
}

export function Modal({titulo, aberto, fechar, children, largo}: {titulo: string; aberto: boolean; fechar: () => void; children: ReactNode; largo?: boolean}) {
  useEffect(() => {
    if (!aberto) return;
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && fechar();
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, [aberto, fechar]);
  if (!aberto) return null;
  return (
    <div className="modal-fundo" onMouseDown={(e) => e.target === e.currentTarget && fechar()}>
      <div className="modal" style={largo ? {width: 'min(960px, 100%)'} : undefined} role="dialog" aria-modal="true" aria-label={titulo}>
        <div className="linha entre" style={{marginBottom: '1rem'}}>
          <h2 style={{margin: 0}}>{titulo}</h2>
          <button className="botao secundario pequeno" onClick={fechar} aria-label="Fechar">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Abas<T extends string>({abas, ativa, mudar}: {abas: [T, string][]; ativa: T; mudar: (t: T) => void}) {
  return (
    <div className="abas" role="tablist">
      {abas.map(([id, rotulo]) => (
        <button key={id} role="tab" aria-selected={ativa === id} className={ativa === id ? 'ativa' : ''} onClick={() => mudar(id)}>
          {rotulo}
        </button>
      ))}
    </div>
  );
}

/** Link de convite com botão de copiar (para mandar por WhatsApp quando o e-mail não chega). */
export function LinkConvite({link}: {link: string}) {
  const [copiado, setCopiado] = useState(false);
  return (
    <div className="aviso ok" style={{flexDirection: 'column'}}>
      <strong>Convite enviado por e-mail.</strong>
      <span className="pequeno">Você também pode copiar o link e enviar por mensagem (vale por 7 dias, uso único):</span>
      <div className="linha" style={{width: '100%'}}>
        <input readOnly value={link} aria-label="Link do convite" style={{flex: 1, marginTop: 0}} onFocus={(e) => e.target.select()} />
        <button
          className="botao pequeno"
          onClick={() => navigator.clipboard?.writeText(link).then(() => setCopiado(true))}>
          {copiado ? 'Copiado' : 'Copiar'}
        </button>
      </div>
    </div>
  );
}
