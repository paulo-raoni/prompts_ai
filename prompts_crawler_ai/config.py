import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- CONFIGURAÇÕES GERAIS DO PROJETO ---
PRODUCT_NAME = "Arsenal Dev AI"
BRAND_NAME = "Brazilian Dev"
WEBSITE_URL = "https://arsenaldev.ai"

# --- CONFIGURAÇÕES DE DIRETÓRIOS E ARQUIVOS ---
# Diretórios de saída
DIR_RAW_DATA = 'BlackMagic_Prompts_Raw'
DIR_HTML_FULL = 'HTML_Arsenal_Completo'
DIR_HTML_SAMPLE = 'HTML_Amostra_Gratis'
DIR_PDF_FULL = 'PDF_Arsenal_Completo'
DIR_PDF_SAMPLE = 'PDF_Amostra_Gratis'
DIR_ASSETS = 'assets'
DIR_PROJECT_BLUEPRINT = 'Project_Blueprint_Analysis'

# Arquivos de Banco de Dados (JSON)
DB_CONSOLIDATED = 'prompts_database.json'
DB_TRANSLATED = 'prompts_database_final_PT-BR.json'

# --- CONFIGURAÇÕES DO PIPELINE ---
# Ordem de execução dos scripts no main.py
PIPELINE_SCRIPTS = [
    'crawler.py',
    'consolidate_data.py',
    'translate_database.py',
    'product_factory.py'
    # 'pdf_factory.py' # Descomente quando o script estiver pronto
]

# --- CONFIGURAÇÕES DO CRAWLER (crawler.py) ---
# URL do site alvvo para extração de prompts
CRAWLER_START_URL = os.getenv('START_URL', 'https://aiavalanche.com/')
# Palavra-chave para encontrar o link de login específico do produto
CRAWLER_LOGIN_HINT = os.getenv('PRODUCT_LOGIN_KEYWORD', 'Black Magic')
# Limite de páginas a serem visitadas pelo crawler
CRAWLER_LIMIT = 150

# --- CONFIGURAÇÕES DO ARCHITECT_CRAWLER ---
ARCHITECT_START_URL = os.getenv('START_URL')
ARCHITECT_LOGIN_KEYWORD = os.getenv('PRODUCT_LOGIN_KEYWORD', '')
ARCHITECT_CRAWL_LIMIT = 50

# --- CREDENCIAIS E CHAVES DE API (do .env) ---
# Credenciais para login no site alvo
WEBSITE_USERNAME = os.getenv('WEBSITE_USERNAME')
WEBSITE_PASSWORD = os.getenv('WEBSITE_PASSWORD')

# Chave da API do Google para o serviço de tradução
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# --- CONTEÚDO PARA O PRODUTO (product_factory.py) ---
# Dicas para o usuário final
MASTER_TIPS = [
    "Dica de Mestre: Ao usar um prompt, seja o mais específico possível. Em vez de 'crie um texto', diga 'crie um texto de 3 parágrafos em tom persuasivo sobre...'.",
    "Dica de Mestre: A IA é ótima para gerar a primeira versão. Sempre revise e peça a ela mesma para 'agir como um editor sênior e refinar este texto'.",
    "Dica de Mestre: Use a técnica de 'poucos exemplos' (few-shot). Dê à IA 2 ou 3 exemplos do estilo que você quer antes de fazer seu pedido final."
]

# Prompts para a amostra grátis
PROMOTIONAL_PROMPTS = [
    {"category": "Marketing de Conteúdo", "prompt": "Crie 5 ideias de títulos para um vídeo no YouTube sobre [tópico]. Os títulos devem ser curtos, magnéticos e otimizados para cliques."},
    {"category": "Copywriting (Escrita Persuasiva)", "prompt": "Aja como um copywriter sênior. Escreva um parágrafo persuasivo para um anúncio no Instagram vendendo um [tipo de produto, ex: curso online]. Use a fórmula AIDA."},
    {"category": "Desenvolvimento de Software", "prompt": "Escreva uma função em Python que recebe uma lista de números e retorna apenas os números pares. Adicione comentários explicando o código."}
]

# Links para redes sociais
SOCIAL_LINKS = {
    'Instagram': 'https://www.instagram.com/braziliandev_oficial/',
    'TikTok': 'https://www.tiktok.com/@braziliandev_oficial',
    'YouTube': 'https://www.youtube.com/braziliandev'
}

print("Configurações carregadas com sucesso.")