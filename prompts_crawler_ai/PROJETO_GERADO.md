## Documento de Requisitos de Produto (PRD) & Blueprint Técnico - Brazilian Dev AI

**1. Visão Geral e Posicionamento do Produto**

O **Brazilian Dev AI** é uma plataforma SaaS que visa capacitar desenvolvedores brasileiros a otimizar seu fluxo de trabalho e aprimorar suas habilidades com o auxílio da Inteligência Artificial. O público-alvo inclui desenvolvedores de software de todos os níveis, desde estudantes até profissionais experientes, que buscam soluções para automação de tarefas, geração de código, aprendizado e aprimoramento de prompts.

**Proposta de Valor:**

*   **Ferramenta Principal (Produto Pago):**  Um conjunto robusto de ferramentas de IA especificamente projetadas para as necessidades dos desenvolvedores brasileiros, incluindo geração de código otimizada para frameworks populares no Brasil,  assistente de depuração inteligente,  geração de documentação automatizada,  análise de código e sugestões de refatoração, e treinamento personalizado em prompts para diferentes LLMs.
*   **Hub de IAs Gratuito (Isca de Valor):** Um agregador gratuito de ferramentas de IA, similar ao catai.com.br, com curadoria voltada para as necessidades dos desenvolvedores, oferecendo acesso a uma variedade de recursos úteis, como geradores de código simples, formatadores de texto, validadores de regex, etc.  Este hub serve como porta de entrada para a plataforma, gerando leads qualificados e criando oportunidades de upsell para a ferramenta principal paga.

**Estratégia de Negócio:**

A estratégia central é o modelo *freemium*, alavancando o Hub de IAs Gratuito para atrair um grande volume de usuários e convertê-los em clientes pagantes da ferramenta principal. A conversão será impulsionada pela demonstração do valor da plataforma completa, oferecendo funcionalidades premium que resolvem problemas mais complexos e otimizam o fluxo de trabalho de forma mais significativa.


**2. Jornada do Usuário (User Journey)**

1.  **Descoberta:** O usuário descobre o Brazilian Dev AI através de mecanismos de busca, redes sociais ou indicações, buscando por ferramentas de IA gratuitas para desenvolvedores.
2.  **Engajamento com o Hub Gratuito:** O usuário acessa o Hub de IAs e experimenta as ferramentas disponíveis, percebendo o valor e a utilidade dos recursos.
3.  **Conscientização da Ferramenta Principal:** Através de banners, notificações sutis e calls-to-action estratégicos dentro do Hub Gratuito, o usuário é apresentado à ferramenta principal e seus benefícios premium.
4.  **Teste da Ferramenta Principal:** O usuário se inscreve para um período de teste gratuito da ferramenta principal, explorando as funcionalidades avançadas e experimentando o poder da plataforma completa.
5.  **Conversão:** Convencido pelo valor da ferramenta principal, o usuário se torna um cliente pagante, optando por um dos planos de assinatura disponíveis.
6.  **Retenção e Upsell:** O usuário continua utilizando a plataforma, se beneficiando de atualizações constantes, suporte dedicado e novas funcionalidades.  Recebe ofertas personalizadas para upgrades de planos e bundles complementares, maximizando o valor do produto.

**3. Arquitetura e Stack de Tecnologia Recomendada**

*   **Frontend:** React, Next.js (SSR para SEO), TypeScript (tipagem forte para escalabilidade)
*   **Backend:** Node.js com NestJS (arquitetura robusta e escalável), TypeScript
*   **Banco de Dados:** PostgreSQL (flexibilidade, robustez e suporte a JSONField para dados não estruturados)
*   **API Gateway:** AWS API Gateway ou Kong (gerenciamento de APIs, segurança e escalabilidade)
*   **Cache:** Redis (cache de dados para performance)
*   **Hospedagem:** AWS (infraestrutura escalável e confiável), ou alternativas como Google Cloud ou Azure.
*   **Integrações com LLMs:** APIs de provedores como OpenAI, Cohere, Anthropic, etc., abstraídas por uma camada interna para facilitar a troca e comparação de modelos.
*   **Fila de Tarefas:** RabbitMQ ou SQS (para processamento assíncrono de tarefas intensivas, como geração de código)
*   **Monitoramento:** Datadog, New Relic ou Prometheus/Grafana (monitoramento de performance e erros)
*   **CI/CD:** GitHub Actions ou GitLab CI (automação de builds e deployments)

**Justificativa:**

Esta stack oferece um equilíbrio entre performance, escalabilidade, custo-benefício e familiaridade para desenvolvedores, sendo ideal para um produto SaaS em crescimento. A utilização de TypeScript garante a manutenibilidade do código, enquanto o Node.js e o NestJS fornecem uma base sólida e escalável para o backend. O PostgreSQL oferece flexibilidade e performance para o armazenamento de dados, e a integração com provedores de LLMs garante acesso às tecnologias de IA mais recentes.

**4. Modelo de Dados (Schema do Banco de Dados)**

*   **Usuários:** `id (UUID, PK), nome, email, senha (hashed), data_criacao, ultimo_login, plano_id (FK), status (ativo/inativo)`
*   **Planos:** `id (UUID, PK), nome (ex: Gratuito, Básico, Pro), preco, limite_uso, recursos`
*   **Hub de IAs:** `id (UUID, PK), nome, descricao, url, categoria, tags`
*   **Histórico de Uso (Hub Gratuito):**  `id (UUID, PK), usuario_id (FK), ferramenta_ia_id (FK), data_uso`
*   **Projetos (Ferramenta Principal):** `id (UUID, PK), usuario_id (FK), nome, descricao, data_criacao`
*   **Gerações de Código:** `id (UUID, PK), projeto_id (FK), prompt, codigo_gerado, modelo_usado, data_geracao`
*   **Pagamentos:**  `id (UUID, PK), usuario_id (FK), plano_id (FK), data_pagamento, valor, status (pago/pendente/falha)`


**5. Requisitos Funcionais Detalhados**

*   **Autenticação:** Login/cadastro via email/senha, integração com Google/GitHub (OAuth), sistema de recuperação de senha.
*   **Hub de IAs:**  Listagem de ferramentas de IA por categoria, busca por palavra-chave, página detalhada de cada ferramenta com descrição e link externo, sistema de avaliação e comentários (opcional).
*   **Ferramenta Principal:**  Interface intuitiva para criação e gerenciamento de projetos,  integração com IDEs populares (VS Code, IntelliJ, etc.),  geração de código com suporte a múltiplas linguagens e frameworks,  assistente de depuração com análise de código e sugestões de correção, documentação automatizada,  treinamento personalizado em prompts com feedback interativo e histórico de prompts.
*   **Fluxo de Compra:**  Página de planos com descrição detalhada de cada um,  integração com gateway de pagamento (Stripe, PagSeguro, etc.),  geração de notas fiscais eletrônicas,  área do usuário para gerenciamento de assinaturas e dados de pagamento.
*   **Estratégia de Pós-Venda:**  Email de boas-vindas com dicas de uso,  notificações sobre novas funcionalidades e atualizações,  sistema de suporte via chat e email,  programa de afiliados,  upsells para planos superiores com mais recursos e limites de uso, bundles complementares com templates e treinamentos específicos.


**6. Requisitos Não-Funcionais**

*   **Performance:** Tempo de resposta rápido para todas as funcionalidades, especialmente para a geração de código.
*   **Escalabilidade:** Arquitetura capaz de suportar um grande número de usuários e requisições concorrentes.
*   **Segurança:** Proteção contra ataques comuns, dados sensíveis criptografados, conformidade com a LGPD.


Este PRD e Blueprint Técnico fornecem uma base sólida para o desenvolvimento do Brazilian Dev AI. À medida que o projeto evolui, este documento deverá ser atualizado e refinado com mais detalhes e especificações.
