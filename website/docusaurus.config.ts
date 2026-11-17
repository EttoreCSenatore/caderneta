import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Caderneta',
  tagline: 'Notas, avisos e calendário da escola num só lugar.',
  favicon: 'img/favicon.svg',

  future: {
    v4: true,
  },

  url: 'https://ettorecsenatore.github.io',
  baseUrl: '/caderneta/',
  organizationName: 'EttoreCSenatore',
  projectName: 'caderneta',
  trailingSlash: false,

  onBrokenLinks: 'throw',

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },
  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'pt-BR',
    locales: ['pt-BR', 'en'],
    localeConfigs: {
      'pt-BR': {label: 'Português (BR)', htmlLang: 'pt-BR'},
      en: {label: 'English', htmlLang: 'en'},
    },
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          showLastUpdateTime: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
    navbar: {
      title: 'Caderneta',
      logo: {
        alt: 'Logo da Caderneta',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Documentação',
        },
        {to: '/docs/roadmap', label: 'Roadmap', position: 'left'},
        {type: 'localeDropdown', position: 'right'},
        {
          href: 'https://github.com/EttoreCSenatore/caderneta',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Produto',
          items: [
            {label: 'Visão geral', to: '/docs/intro'},
            {label: 'Perfis e permissões', to: '/docs/produto/perfis'},
            {label: 'Notas e médias', to: '/docs/funcionalidades/notas-e-medias'},
          ],
        },
        {
          title: 'Funcionalidades',
          items: [
            {label: 'Comunicação', to: '/docs/funcionalidades/comunicacao'},
            {label: 'Calendário', to: '/docs/funcionalidades/calendario'},
            {label: 'Provas e impressão', to: '/docs/funcionalidades/provas-e-impressao'},
          ],
        },
        {
          title: 'Técnico',
          items: [
            {label: 'Arquitetura', to: '/docs/tecnico/arquitetura'},
            {label: 'Segurança e LGPD', to: '/docs/tecnico/seguranca-e-lgpd'},
            {label: 'Roadmap', to: '/docs/roadmap'},
          ],
        },
      ],
      copyright: `Caderneta © ${new Date().getFullYear()} Ettore Senatore. Feito com Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['json', 'bash', 'python', 'sql'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
