import {renderToStaticMarkup} from 'react-dom/server';
import {describe, expect, it} from 'vitest';
import {Markdown} from './markdown';

const html = (t: string) => renderToStaticMarkup(<Markdown texto={t} />);

describe('Markdown dos textos legais', () => {
  it('monta títulos, parágrafos, listas e negrito', () => {
    expect(html('# Título\n## Seção\n### Item\nTexto **forte**.\n- um\n- dois\n\nFim')).toBe(
      '<div class="texto-legal"><h1>Título</h1><h2>Seção</h2><h3>Item</h3><p>Texto <strong>forte</strong>.</p>' +
        '<ul><li>um</li><li>dois</li></ul><p>Fim</p></div>',
    );
  });
  it('escapa HTML cru em vez de interpretar', () => {
    const h = html('<script>alert(1)</script> <img src=x onerror=alert(1)>');
    expect(h).not.toContain('<script');
    expect(h).not.toContain('<img');
    expect(h).toContain('&lt;script&gt;');
  });
  it('só cria link para rota do app ou https', () => {
    expect(html('[meus dados](/meus-dados)')).toContain('<a href="/meus-dados">meus dados</a>');
    expect(html('[ANPD](https://www.gov.br/anpd)')).toContain('<a href="https://www.gov.br/anpd">ANPD</a>');
    for (const ruim of ['javascript:alert(1)', 'data:text/html,oi', 'http://inseguro.com', '//outro-site.com']) {
      const h = html(`[clique](${ruim})`);
      expect(h, ruim).not.toContain('<a');
      expect(h).toContain('clique');
    }
  });
});
