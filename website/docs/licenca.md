---
id: licenca
title: Licença
---

# Licença

A Caderneta é software livre sob a **GNU Affero General Public License, versão 3 ou posterior** (`AGPL-3.0-or-later`). O texto completo está no arquivo
[`LICENSE`](https://github.com/EttoreCSenatore/caderneta/blob/main/LICENSE) do repositório.

## O que isso permite

- **Usar** a Caderneta em qualquer escola, inclusive instalando em servidor próprio.
- **Estudar e auditar** o código. Isso importa aqui: o sistema guarda dados de crianças e de saúde, e a escola pode ver como são tratados.
- **Modificar** e **distribuir** o código, sempre sob a mesma licença.
- **Cobrar** por hospedagem, suporte e implantação.

## O que ela exige

- Quem **modifica** a Caderneta e a oferece como **serviço pela internet** precisa dar, a quem usa o serviço, acesso ao **código-fonte da versão modificada**
  (seção 13 da AGPL). É a diferença da AGPL para a GPL comum, que não cobre o uso em rede.
- Distribuir cópias exige manter o aviso de copyright e a licença, e entregar o código-fonte.
- Trabalhos derivados continuam sob a AGPL. Não dá para fechar uma versão modificada.

Não é necessário publicar nada para **apenas usar** a Caderneta sem alterá-la, nem as configurações e os dados da sua escola.

## Dependências de terceiros

A API (Python) e o app web usam componentes de código aberto com licenças permissivas (MIT, BSD, Apache-2.0, ISC) e uma biblioteca LGPL (`psycopg`), todas
**compatíveis** com a AGPL. A lista completa, com os textos das licenças, está em
[`THIRD_PARTY_NOTICES.md`](https://github.com/EttoreCSenatore/caderneta/blob/main/THIRD_PARTY_NOTICES.md).

O CI verifica a cada alteração (`scripts/auditar-licencas.py`) e **reprova** a mudança se entrar uma dependência de runtime com licença desconhecida, proprietária ou
incompatível (por exemplo GPL-2.0 apenas, SSPL ou "uso não comercial").

## O que ainda está em aberto

- **Documentação e imagens:** o texto do site e os screenshots (com dados fictícios) ainda não têm uma licença própria definida. Até a decisão, valem os direitos
  reservados do projeto. A decisão (por exemplo CC BY 4.0 ou a própria AGPL) fica para o [M8](./roadmap.md#m8-conformidade-e-segurança).
- **Nome e logotipo "Caderneta":** a licença cobre o código, **não** a marca. A checagem de disponibilidade e o registro (INPI) também estão no M8.
- **Copyright:** o aviso usa o usuário do GitHub do responsável. Ajuste para o nome legal da pessoa ou da organização titular antes do piloto.

:::note Aviso
Esta página explica a licença em linguagem simples e **não é aconselhamento jurídico**. Em caso de dúvida sobre obrigações, consulte um advogado.
:::
