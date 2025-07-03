# Arsenal de Prompts AI

Um sistema completo para extrair, gerenciar e apresentar uma coleção de prompts de IA, com um painel de administração web para controle total do conteúdo.

-----

### 📖 Tabela de Conteúdos

1.  [Funcionalidades Principais](https://www.google.com/search?q=%23-funcionalidades-principais)
2.  [Tecnologias Utilizadas](https://www.google.com/search?q=%23%EF%B8%8F-tecnologias-utilizadas)
3.  [Estrutura do Projeto](https://www.google.com/search?q=%23-estrutura-do-projeto)
4.  [Guia de Utilização](https://www.google.com/search?q=%23-guia-de-utiliza%C3%A7%C3%A3o)
      - [Pré-requisitos](https://www.google.com/search?q=%23pr%C3%A9-requisitos)
      - [Instalação](https://www.google.com/search?q=%23instala%C3%A7%C3%A3o)
      - [Como Executar](https://www.google.com/search?q=%23como-executar)

-----

## ✨ Funcionalidades Principais

  - **🤖 Extração de Dados**: Scripts para fazer *web scraping* e coletar prompts de websites externos.
  - **✍️ Gerenciamento de Conteúdo (CRUD)**: Um painel de administração web completo para Criar, Ler, Atualizar e Excluir prompts.
  - **⚡ Regeneração com Um Clique**: Botão no painel de administração para gerar o site estático final com todas as alterações recentes.
  - **🖥️ Pré-visualização Integrada**: Acesse e navegue no site gerado diretamente a partir do ambiente do painel de administração.
  - **💾 Base de Dados JSON**: Utiliza um arquivo `.json` como banco de dados, facilitando a portabilidade e a edição manual, se necessário.

-----

## 🛠️ Tecnologias Utilizadas

  - **Backend**: Python, Flask
  - **Frontend**: HTML5, Tailwind CSS
  - **Formato de Dados**: JSON

-----

## 📂 Estrutura do Projeto

A estrutura de arquivos foi pensada para ser modular e organizada, separando as responsabilidades de cada parte do sistema.

```sh
/
|-- admin_panel/            # Aplicação Flask para o painel de administração.
|   |-- admin.py            # Lógica do servidor e das rotas do painel.
|   +-- templates/          # Arquivos HTML do painel.
|
|-- src/                    # Código-fonte principal da aplicação.
|   |-- crawling/           # Módulos de web scraping.
|   |-- generation/         # Módulo gerador do site estático.
|   |   +-- product_factory.py
|   +-- processing/         # Módulos para processar e limpar dados.
|
|-- output/                 # Arquivos gerados pela aplicação.
|   |-- HTML_Arsenal_Completo/ # O site HTML estático final.
|   +-- prompts_database_final.json  # O banco de dados.
|
+-- main.py                 # Ponto de entrada para o fluxo de extração.
+-- requirements.txt        # Lista de dependências Python.
+-- README.md               # Este arquivo.
```

-----

## 🚀 Guia de Utilização

Siga estes passos para configurar e rodar o projeto localmente.

### Pré-requisitos

  - Python (versão 3.10 ou superior)
  - `pip` (gerenciador de pacotes do Python)

### Instalação

1.  **Clone o repositório:**

    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd <NOME_DO_DIRETORIO>
    ```

2.  **Crie e ative um ambiente virtual** (altamente recomendado):

    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows
    .\venv\Scripts\activate

    # Ativar no macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

### Como Executar

O projeto tem dois fluxos de trabalho principais:

#### 1\. Extração Inicial de Dados

Este passo só é necessário para popular o banco de dados pela primeira vez a partir da fonte.

```bash
python main.py
```

Para um teste rápido, execute `python main.py --demo` e o crawler irá coletar apenas 5 páginas.

Este comando irá executar os scripts de extração e processamento, criando o arquivo `output/prompts_database_final.json`.

#### 2\. Gerenciamento e Visualização (Painel de Administração)

Este é o fluxo principal para o dia a dia: gerenciar conteúdo e regenerar o site.

1.  **Inicie o servidor do painel de administração:**

    ```bash
    python admin_panel/admin.py
    ```

2.  **Acesse o painel no seu navegador:**
    [link suspeito removido]

3.  **Fluxo de trabalho no painel:**

      - Faça suas alterações (adicione, edite ou exclua prompts).
      - Clique em **`Regenerar Site`** para aplicar as alterações ao site estático.
      - Clique em **`Ver Site`** para abrir a versão atualizada em uma nova aba.