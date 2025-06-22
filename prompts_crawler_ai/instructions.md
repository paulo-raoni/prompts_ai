# Projeto Brazilian Dev AI - Pipeline de Extração de Dados

## 1. Descrição do Projeto

Este projeto contém um conjunto de scripts em Python projetados para executar um pipeline completo de extração, consolidação e tradução de prompts de IA. O objetivo final é gerar uma base de dados estruturada em JSON, que servirá como o "cérebro" para o agente de IA "Brazilian Dev AI".

O processo é dividido em três etapas principais:
1.  **Crawling:** Navega em um site alvo para extrair dados brutos de prompts.
2.  **Consolidação:** Unifica os dados brutos em um único arquivo JSON.
3.  **Tradução:** Utiliza a API do Google Gemini para traduzir os prompts para o português.

## 2. Estrutura de Arquivos

A pasta do projeto está organizada da seguinte forma:

-   `BlackMagic_Prompts/`: Diretório onde o `crawler.py` salva os dados brutos extraídos, organizados por categoria e título.
-   `.env`: Arquivo de configuração para armazenar chaves de API secretas (Google Gemini) e credenciais de login do site. **Este arquivo não deve ser compartilhado.**
-   `crawler.py`: Script principal (Crawler v6.3) que utiliza Selenium para navegar no site, fazer login e extrair o conteúdo dos prompts, salvando-os na pasta `BlackMagic_Prompts`.
-   `consolidate_data.py`: Script que lê os arquivos `.txt` da pasta `BlackMagic_Prompts` e os unifica em um único arquivo JSON (`prompts_database.json`).
-   `translate_database.py`: Script final (v2) que lê o JSON consolidado, identifica prompts que precisam de tradução e utiliza a API do Gemini para preencher os dados em português, gerando o arquivo final.
-   `instructions.md`: Este arquivo de instruções.
-   `prompts_database.json`: Arquivo JSON intermediário gerado pelo `consolidate_data.py`.
-   `prompts_database_translated.json`: **O artefato final.** Este é o arquivo JSON completo e traduzido, pronto para ser usado pelo agente de IA.

## 3. Pré-requisitos

Antes de executar, certifique-se de que você tem o seguinte instalado:
-   Python 3.8 ou superior
-   Pip (gerenciador de pacotes do Python)
-   Google Chrome (ou o navegador para o qual você tem o WebDriver)
-   ChromeDriver correspondente à sua versão do Chrome (colocado na mesma pasta do projeto)

## 4. Instalação e Configuração

Siga estes passos **uma única vez** para preparar o ambiente.

**1. Instale as dependências:**
Abra um terminal nesta pasta e execute o seguinte comando para instalar todas as bibliotecas Python necessárias:
```bash
pip install requests beautifulsoup4 lxml python-dotenv google-generativeai selenium undetected-chromedriver