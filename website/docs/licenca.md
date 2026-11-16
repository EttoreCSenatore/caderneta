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

## Documentação e imagens

O texto do site de documentação e os screenshots (feitos só com dados fictícios) estão sob a licença
[**Creative Commons Atribuição-CompartilhaIgual 4.0 Internacional (CC BY-SA 4.0)**](https://creativecommons.org/licenses/by-sa/4.0/deed.pt-br).
Você pode copiar, adaptar e redistribuir, inclusive para fins comerciais, desde que **dê o crédito** e **mantenha a mesma licença** nas versões derivadas. É o equivalente,
para textos e imagens, do espírito da AGPL. O aviso está em [`LICENSE-DOCS.md`](https://github.com/EttoreCSenatore/caderneta/blob/main/LICENSE-DOCS.md).

## O que ainda está em aberto

- **Nome e logotipo "Caderneta":** a licença cobre o código e a documentação, **não** a marca. O registro no INPI é opcional e não será feito por enquanto; antes do
  piloto basta uma consulta rápida e gratuita à base do INPI, porque o serviço de instalação é comercial. Se houver conflito, o nome pode ser trocado.
- **Copyright:** o aviso usa o usuário do GitHub do responsável. Ajuste para o nome legal da pessoa ou da organização titular antes do piloto.

:::note Aviso
Esta página explica a licença em linguagem simples e **não é aconselhamento jurídico**. Em caso de dúvida sobre obrigações, consulte um advogado.
:::
