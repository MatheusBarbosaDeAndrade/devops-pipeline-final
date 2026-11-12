# Etapa 1 – Conceitos fundamentais de DevOps

**Atividade Avaliativa – DevOps na Prática** · DevOps Tools · UNAMA – Universidade da Amazônia
Prof. Rodrigo Silva Marques · Integrantes: ver [README](../README.md#integrantes)

Este relatório explica três temas: o que é DevOps e como ele se relaciona com as metodologias ágeis; a diferença entre CI, Continuous Delivery e Continuous Deployment; e máquinas virtuais × containers. Cada tema traz uma analogia e um exemplo tirado do próprio projeto deste repositório.

---

## 1. O que é DevOps e como se relaciona com as metodologias ágeis

**DevOps** junta *Development* e *Operations*. É um conjunto de princípios culturais, práticas e ferramentas que aproxima as equipes de desenvolvimento e de operações para entregar software com mais rapidez, qualidade e estabilidade. Não é um cargo nem uma ferramenta: é uma forma de trabalhar em que a responsabilidade pelo software vai do código até a produção.

Kim et al. (2018) organizam essa forma de trabalhar em **três caminhos**:

1. **Fluxo:** acelerar o trabalho do desenvolvimento até o cliente.
2. **Feedback:** ter retorno rápido e contínuo de cada etapa.
3. **Aprendizado contínuo:** experimentar e melhorar sempre.

Outra síntese muito usada é o modelo **CALMS**: Cultura, Automação, *Lean*, Medição e Compartilhamento (*Sharing*).

As **metodologias ágeis** foram formalizadas no Manifesto Ágil (BECK et al., 2001). Elas valorizam indivíduos e interações, software funcionando, colaboração com o cliente e resposta a mudanças, e trabalham em ciclos curtos (sprints) com entregas incrementais.

Historicamente, porém, o ágil se concentrou na relação entre o negócio e o time de desenvolvimento. Não adianta produzir um incremento a cada duas semanas se a implantação em produção continua manual, lenta e arriscada. O DevOps **estende os princípios ágeis até a operação** e remove esse gargalo final. Ou seja, **DevOps não substitui o ágil: complementa.**

| Aspecto | Metodologias ágeis | DevOps |
|---|---|---|
| Foco | Colaboração entre negócio e desenvolvimento | Colaboração entre desenvolvimento e operações (e segurança) |
| Escopo | Planejamento e construção do software | Ciclo inteiro: construir, testar, implantar, operar e monitorar |
| Entrega | Incremento ao fim de cada iteração | Implantações frequentes e automatizadas, até várias por dia |
| Feedback | Revisão da sprint com o cliente | Testes automatizados, métricas e logs de produção |
| Práticas típicas | Scrum, Kanban, histórias de usuário, retrospectivas | CI/CD, infraestrutura como código, containers, monitoramento |

> **Analogia: o restaurante.** O ágil é uma cozinha que prepara os pratos em porções pequenas e pede a opinião do cliente a cada rodada. Mas, se o garçom (a operação) trabalha isolado, os pratos esfriam no balcão. DevOps é transformar cozinha e salão em uma só equipe, com uma esteira que leva o prato ao cliente assim que fica pronto e um retorno imediato sobre o que agradou.

**Exemplo no projeto.** Cada `git push` dispara sozinho os testes, o build da imagem, a publicação no registry e a implantação no Kubernetes. Logo depois, o dashboard do Kibana mostra se a nova versão está respondendo com erros ou lentidão. O ciclo *alterar → entregar → observar*, que num processo manual levaria dias, acontece em cerca de **2 min 30 s**: essa foi a duração da primeira execução do pipeline.

---

## 2. Diferença entre CI, Continuous Delivery e Continuous Deployment

**Integração Contínua (CI).** É integrar o código de todos os desenvolvedores num repositório comum várias vezes ao dia. Cada integração é verificada por build e testes automatizados, e assim os erros aparecem minutos depois de serem introduzidos (FOWLER, 2006).

**Entrega Contínua (*Continuous Delivery*).** Amplia a CI: todo commit aprovado gera um artefato pronto para produção. A implantação pode acontecer a qualquer momento, mas depende de uma **decisão humana**, normalmente um botão de aprovação (HUMBLE; FARLEY, 2014).

**Implantação Contínua (*Continuous Deployment*).** Elimina essa aprovação: **toda mudança que passa no pipeline vai para produção automaticamente**. Para isso, exige testes confiáveis e mecanismos de segurança, como *rolling update* e *rollback* automático.

| Característica | CI | CD – Delivery | CD – Deployment |
|---|---|---|---|
| Objetivo | Detectar erros de integração cedo | Ter sempre uma versão pronta para produção | Levar cada mudança aprovada à produção automaticamente |
| Até onde automatiza | Build e testes | Build, testes e homologação | Todo o caminho até a produção |
| Decisão de ir para produção | Não se aplica | **Manual** (botão de aprovação) | **Automática** (sem intervenção humana) |
| Pré-requisitos | Testes automatizados e repositório único | CI madura e ambientes padronizados | Testes confiáveis, monitoramento e rollback |
| Neste projeto | Jobs *1. Testes automatizados* e *2. Build Docker e push (GHCR)* | Imagem versionada `sha-<commit>` no GHCR, pronta para uso | Job *3. Deploy no Kubernetes (Helm)* a cada push na `main` |

**O pipeline deste projeto faz Continuous Deployment.** Depois que os testes passam e a imagem é publicada, o job de deploy roda `helm upgrade --install` **sem nenhuma aprovação manual**. A opção `--atomic` desfaz a atualização sozinha se a nova versão não ficar saudável. Para virar *Continuous Delivery*, bastaria proteger o job de deploy com um *environment* do GitHub que exija aprovação de um revisor.

> **Analogia: a fábrica de bolos.**
> - **CI** é provar cada ingrediente e cada camada assim que fica pronta, para descobrir logo se o açúcar foi trocado por sal.
> - **Continuous Delivery** é manter o bolo pronto e embalado na vitrine, esperando o gerente autorizar a venda.
> - **Continuous Deployment** é a esteira que, ao fim do controle de qualidade, entrega o bolo direto ao cliente, sem esperar autorização.

---

## 3. Máquinas virtuais × containers e as vantagens dos containers

**Máquina virtual (VM).** É uma cópia isolada de uma máquina real, criada por um **hipervisor** que controla o hardware (POPEK; GOLDBERG, 1974). Cada VM roda um **sistema operacional completo, com kernel próprio**, além das bibliotecas e da aplicação. O isolamento é forte, mas as imagens têm vários gigabytes, consomem muita memória e levam minutos para iniciar.

**Container.** É um **processo isolado que compartilha o kernel do sistema hospedeiro**. Usa recursos do próprio Linux: *namespaces*, que isolam processos, rede e sistema de arquivos, e *cgroups*, que limitam CPU e memória. A imagem leva apenas a aplicação e suas dependências, por isso é leve, portátil e inicia rápido (MERKEL, 2014).

| Critério | Máquina virtual | Container |
|---|---|---|
| O que virtualiza | O hardware (hipervisor) | O sistema operacional (namespaces e cgroups) |
| Sistema operacional | Um SO completo por VM | Compartilha o kernel do hospedeiro |
| Tamanho típico | Gigabytes | Megabytes (a imagem deste projeto tem ~227 MB) |
| Inicialização | Minutos | Segundos ou menos |
| Densidade | Poucas VMs por servidor | Dezenas ou centenas por servidor |
| Isolamento | Forte (kernel separado) | Bom, mas depende do kernel compartilhado |
| Uso típico | SOs diferentes, isolamento rígido | Microsserviços, CI/CD, ambientes reprodutíveis |

### Vantagens dos containers

- **Portabilidade.** A mesma imagem roda no notebook, no runner do GitHub Actions e no cluster Kubernetes. Isso acaba com o "na minha máquina funciona".
- **Leveza e velocidade.** Ambientes sobem e são destruídos em segundos. O pipeline cria um cluster Kubernetes inteiro (Kind), implanta, testa e apaga, tudo em pouco mais de 1 minuto.
- **Imutabilidade e versionamento.** Cada imagem tem uma tag. Aqui a tag é o SHA do commit, por exemplo `sha-deda5ec`, o que facilita rastrear e reverter versões.
- **Eficiência de recursos.** Cabem mais aplicações no mesmo servidor.
- **Base para orquestração.** O Kubernetes escala, reinicia e atualiza containers automaticamente.

> **Analogia: casa × apartamento.** Uma VM é uma **casa**: tem fundação, encanamento e estrutura próprios. É bem isolada, mas cara e demorada de construir. Containers são **apartamentos de um mesmo prédio**: compartilham a fundação e a estrutura (o kernel), mas cada um tem sua porta, sua chave e seus móveis (processos e arquivos isolados), e ficam prontos para morar muito mais rápido.

**Exemplo no projeto.** Na Etapa 4, sete serviços sobem ao mesmo tempo com um único `docker compose up` num notebook de 8 GB de RAM: Elasticsearch, Kibana, Filebeat, APM Server, a aplicação e o gerador de tráfego. Fazer isso com sete VMs completas seria inviável.

---

## Referências

BECK, Kent et al. **Manifesto para desenvolvimento ágil de software**. 2001. Disponível em: https://agilemanifesto.org/iso/ptbr/manifesto.html. Acesso em: 12 nov. 2026.

FOWLER, Martin. **Continuous integration**. 2006. Disponível em: https://martinfowler.com/articles/continuousIntegration.html. Acesso em: 12 nov. 2026.

HUMBLE, Jez; FARLEY, David. **Entrega contínua**: como entregar software de forma rápida e confiável. Porto Alegre: Bookman, 2014.

KIM, Gene et al. **Manual de DevOps**: como obter agilidade, confiabilidade e segurança em organizações tecnológicas. Rio de Janeiro: Alta Books, 2018.

MERKEL, Dirk. Docker: lightweight Linux containers for consistent development and deployment. **Linux Journal**, v. 2014, n. 239, mar. 2014.

POPEK, Gerald J.; GOLDBERG, Robert P. Formal requirements for virtualizable third generation architectures. **Communications of the ACM**, v. 17, n. 7, p. 412-421, 1974.
