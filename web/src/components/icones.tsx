const P = {fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round'} as const;

export const Icone = {
  inicio: <svg viewBox="0 0 24 24" {...P}><path d="M3 11l9-8 9 8" /><path d="M5 10v10h14V10" /></svg>,
  avisos: <svg viewBox="0 0 24 24" {...P}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 8 3 8H3s3-1 3-8" /><path d="M10.3 20a2 2 0 0 0 3.4 0" /></svg>,
  autorizacoes: <svg viewBox="0 0 24 24" {...P}><path d="M9 12l2 2 4-4" /><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /></svg>,
  turmas: <svg viewBox="0 0 24 24" {...P}><rect x="3" y="4" width="18" height="14" rx="2" /><path d="M8 21h8M12 18v3" /></svg>,
  alunos: <svg viewBox="0 0 24 24" {...P}><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c.8-3.5 3.4-5.5 6.5-5.5s5.7 2 6.5 5.5" /><circle cx="17" cy="9" r="2.5" /><path d="M17 14.5c2.3 0 4 1.5 4.5 4" /></svg>,
  equipe: <svg viewBox="0 0 24 24" {...P}><circle cx="12" cy="7" r="3.5" /><path d="M5 21c.6-4 3.4-6.5 7-6.5s6.4 2.5 7 6.5" /></svg>,
  importar: <svg viewBox="0 0 24 24" {...P}><path d="M12 3v12M7 10l5 5 5-5" /><path d="M4 17v3h16v-3" /></svg>,
  escola: <svg viewBox="0 0 24 24" {...P}><path d="M3 9l9-5 9 5-9 5-9-5z" /><path d="M7 11.5V17c0 1 2.2 2.5 5 2.5s5-1.5 5-2.5v-5.5" /></svg>,
  sair: <svg viewBox="0 0 24 24" {...P}><path d="M15 4h4v16h-4" /><path d="M10 8l-4 4 4 4M6 12h10" /></svg>,
  saude: <svg viewBox="0 0 24 24" {...P}><path d="M12 21s-8-4.5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 10c0 6.5-8 11-8 11z" /></svg>,
};
