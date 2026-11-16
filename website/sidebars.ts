import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    'licenca',
    {
      type: 'category',
      label: 'Produto',
      collapsed: false,
      items: ['produto/visao', 'produto/perfis', 'produto/jornadas'],
    },
    {
      type: 'category',
      label: 'Funcionalidades',
      collapsed: false,
      items: [
        'funcionalidades/acesso-e-convites',
        'funcionalidades/escola-e-turmas',
        'funcionalidades/cadastro-de-alunos',
        'funcionalidades/notas-e-medias',
        'funcionalidades/frequencia',
        'funcionalidades/comunicacao',
        'funcionalidades/calendario',
        'funcionalidades/provas-e-impressao',
        'funcionalidades/historico-e-anotacoes',
      ],
    },
    {
      type: 'category',
      label: 'Técnico',
      items: [
        'tecnico/arquitetura',
        'tecnico/modelo-de-dados',
        'tecnico/seguranca-e-lgpd',
        'tecnico/desenvolvimento',
      ],
    },
    {
      type: 'category',
      label: 'Decisões (ADRs)',
      items: ['decisoes/stack', 'decisoes/multiescola', 'decisoes/pwa-primeiro', 'decisoes/armazenamento-de-arquivos', 'decisoes/pdf-proprio'],
    },
    'roadmap',
  ],
};

export default sidebars;
