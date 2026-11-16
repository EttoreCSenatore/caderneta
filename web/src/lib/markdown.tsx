import type {ReactNode} from 'react';

/** Renderizador mínimo para os textos legais: títulos, parágrafos, listas, **negrito** e [links](/rota). Sem HTML cru. */
function inline(t: string): ReactNode[] {
  const partes: ReactNode[] = [];
  const re = /\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)]+)\)/g;
  let i = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(t))) {
    if (m.index > i) partes.push(t.slice(i, m.index));
    if (m[1] !== undefined) partes.push(<strong key={m.index}>{m[1]}</strong>);
    else {
      const href = m[3];
      partes.push(href.startsWith('/') || href.startsWith('https://') ? <a key={m.index} href={href}>{m[2]}</a> : m[2]);
    }
    i = m.index + m[0].length;
  }
  if (i < t.length) partes.push(t.slice(i));
  return partes;
}

export function Markdown({texto}: {texto: string}) {
  const blocos: ReactNode[] = [];
  let lista: string[] = [];
  const fechaLista = () => {
    if (lista.length) blocos.push(<ul key={`l${blocos.length}`}>{lista.map((x, i) => <li key={i}>{inline(x)}</li>)}</ul>);
    lista = [];
  };
  for (const linha of texto.split('\n')) {
    const l = linha.trimEnd();
    if (l.startsWith('- ')) {
      lista.push(l.slice(2));
      continue;
    }
    fechaLista();
    if (!l.trim()) continue;
    if (l.startsWith('### ')) blocos.push(<h3 key={blocos.length}>{inline(l.slice(4))}</h3>);
    else if (l.startsWith('## ')) blocos.push(<h2 key={blocos.length}>{inline(l.slice(3))}</h2>);
    else if (l.startsWith('# ')) blocos.push(<h1 key={blocos.length}>{inline(l.slice(2))}</h1>);
    else blocos.push(<p key={blocos.length}>{inline(l)}</p>);
  }
  fechaLista();
  return <div className="texto-legal">{blocos}</div>;
}
