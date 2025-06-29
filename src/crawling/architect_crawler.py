import os
import time
import json
from collections import Counter, deque
from dotenv import load_dotenv
import google.generativeai as genai
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

# Importações do Selenium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURAÇÕES ---
load_dotenv()
START_URL = os.getenv('START_URL')
WEBSITE_USERNAME = os.getenv('WEBSITE_USERNAME')
WEBSITE_PASSWORD = os.getenv('WEBSITE_PASSWORD')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PRODUCT_LOGIN_KEYWORD = os.getenv('PRODUCT_LOGIN_KEYWORD', '') # Opcional
OUTPUT_DIR = 'Project_Blueprint_Analysis'
CRAWL_LIMIT = 50 # Limite de segurança para não rodar infinitamente

# --- CONFIGURAÇÃO DA API DO GEMINI ---
try:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY não encontrada no arquivo .env.")
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-pro')
    print("API do Gemini configurada com sucesso.")
except Exception as e:
    print(f"Erro ao configurar a API do Gemini: {e}")
    gemini_model = None

# --- META-PROMPT DO PRODUCT MANAGER / ARQUITETO ---
ARCHITECT_META_PROMPT = """
Você é um Product Manager e Arquiteto de Soluções Sênior do Silicon Valley, com experiência em criar produtos digitais SaaS de sucesso. Sua tarefa é analisar um dossiê sobre o conteúdo e a estrutura de um site de referência para criar um Documento de Requisitos de Produto (PRD) e um Blueprint Técnico para um novo concorrente, chamado "Brazilian Dev AI", focado no mercado brasileiro.

O resultado NÃO deve ser uma cópia, mas sim um projeto profissional, bem estruturado e com uma estratégia de negócio clara, inspirado nas funcionalidades observadas.

**Incorpore obrigatoriamente a seguinte nova feature no plano:**
* **Hub de IAs Gratuito:** Na barra de navegação principal, deve haver um link proeminente para uma ferramenta gratuita, um "Hub de IAs", inspirado no `catai.com.br`. O objetivo é gerar valor, atrair usuários e criar uma oportunidade de upsell para o produto principal.

O documento final deve ser um Markdown detalhado, cobrindo os seguintes tópicos:

1.  **Visão Geral e Posicionamento do Produto:** Conceito do "Brazilian Dev AI", público-alvo, proposta de valor e a estratégia da isca de valor "Hub de IAs Gratuito".
2.  **Jornada do Usuário (User Journey):** Descreva a jornada desde um novo visitante atraído pelo Hub Gratuito até um cliente pagante da ferramenta principal.
3.  **Arquitetura e Stack de Tecnologia Recomendada:** Sugira e justifique uma stack completa.
4.  **Modelo de Dados (Schema do Banco de Dados):** Defina as tabelas, campos e relacionamentos.
5.  **Requisitos Funcionais Detalhados:** Autenticação, Hub de IAs, Ferramenta Principal, Fluxo de Compra e Estratégia de Pós-Venda (infira um funil com upsells e bundles).
6.  **Requisitos Não-Funcionais:** Performance, Escalabilidade e Segurança.

A seguir, o dossiê para sua análise:
"""

# --- FUNÇÕES AUXILIARES ---

def get_root_domain(url):
    """Extrai o domínio raiz de uma URL."""
    try:
        domain = urlparse(url).netloc
        parts = domain.split('.')
        if len(parts) > 1: return ".".join(parts[-2:])
        return domain
    except: return None

def analyze_page_content(soup):
    """Analisa o HTML para extrair conteúdo e estrutura, incluindo indícios de checkout."""
    analysis = {'title': soup.title.string.strip() if soup.title else 'Sem Título', 'headlines': [], 'features': [], 'faqs': [], 'is_checkout_page': False}
    try:
        analysis['headlines'] = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2'])]
        payment_keywords = ['card', 'cvc', 'expiry', 'billing', 'checkout', 'payment', 'pagamento', 'cartão']
        page_text_lower = soup.get_text().lower()
        if any(keyword in page_text_lower for keyword in payment_keywords):
            analysis['is_checkout_page'] = True
            print("   -> DETECÇÃO: Esta parece ser uma página de checkout/pagamento.")
            analysis['checkout_form_fields'] = [{'name': inp.get('name', 'N/A'), 'id': inp.get('id', 'N/A'), 'type': inp.get('type', 'N/A')} for inp in soup.find_all('input')]
            scripts = [s.get('src') for s in soup.find_all('script') if s.get('src')]
            if any("stripe.com" in s for s in scripts): analysis['payment_gateway'] = 'Stripe'
            elif any("paypal.com" in s for s in scripts): analysis['payment_gateway'] = 'PayPal'
            else: analysis['payment_gateway'] = 'Desconhecido ou integrado'
    except Exception as e:
        print(f"   -> Erro menor durante análise da página: {e}")
    return analysis

def perform_hybrid_login(driver, wait):
    """Executa o fluxo de login adaptativo e completo."""
    if not (WEBSITE_USERNAME and WEBSITE_PASSWORD):
        print("Credenciais não encontradas no .env. O crawler continuará deslogado.")
        return True # Retorna True para continuar mesmo sem login
    print("\n--- Iniciando Rotina de Login Híbrida ---")
    try:
        driver.get(START_URL)
        print(f"1. Acessando: {START_URL}")
        time.sleep(2)
        try:
            print("2. Procurando por um link de login genérico...")
            login_link_texts = ["Login", "Sign In", "Entrar", "Acessar"]
            login_link_found = False
            for text in login_link_texts:
                try:
                    login_link = wait.until(EC.element_to_be_clickable((By.XPATH, f".//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')] | .//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]")))
                    print(f"   -> Link de login genérico '{text}' encontrado. Clicando...")
                    url_antes_clique = driver.current_url
                    login_link.click()
                    wait.until(lambda d: d.current_url != url_antes_clique)
                    print(f"   -> Navegou para nova página: {driver.current_url}")
                    login_link_found = True
                    break
                except TimeoutException: continue
            if not login_link_found: print("   -> Nenhum link de login genérico encontrado. Prosseguindo...")
        except Exception as e: print(f"   -> Erro ao procurar link de login genérico: {e}. Prosseguindo...")

        print("3. Investigando página atual para encontrar formulário ou link específico...")
        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
            print("   -> Formulário de login encontrado diretamente nesta página!")
        except TimeoutException:
            print("   -> Formulário não encontrado. Procurando por link específico com a palavra-chave...")
            if not PRODUCT_LOGIN_KEYWORD: raise Exception("Página intermediária detectada, mas PRODUCT_LOGIN_KEYWORD não foi definido no .env.")
            specific_link = wait.until(EC.element_to_be_clickable((By.XPATH, f".//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{PRODUCT_LOGIN_KEYWORD.lower()}')]")))
            print(f"   -> Link específico '{PRODUCT_LOGIN_KEYWORD}' encontrado. Clicando...")
            specific_link.click()

        print("4. Preenchendo credenciais no formulário final...")
        user_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name*='user'], input[id*='user'], input[name*='log']")))
        pass_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        user_field.send_keys(WEBSITE_USERNAME)
        pass_field.send_keys(WEBSITE_PASSWORD)
        submit_button.click()
        print("5. Aguardando confirmação do login...")
        time.sleep(5)
        print(f"   -> LOGIN REALIZADO COM SUCESSO! URL final: {driver.current_url}")
        return True
    except Exception as e:
        print(f"Ocorreu um erro crítico durante a rotina de login: {e}")
        return False

# --- FUNÇÃO PRINCIPAL ---
def main():
    if not START_URL:
        print("ERRO: A variável START_URL não está definida no .env.")
        return

    print(f"--- Iniciando Arquiteto-Robô v6.0 (Product Manager) ---")
    driver = uc.Chrome(options=uc.ChromeOptions())
    wait = WebDriverWait(driver, 15)
    site_analysis = {}
    
    try:
        if not perform_hybrid_login(driver, wait):
            raise Exception("Login falhou. Encerrando o crawler.")
        
        print("\n--- FASE 1: Análise Estrutural (Exploração Completa) ---")
        urls_to_visit = deque([driver.current_url])
        visited_urls = set()
        root_domain_to_match = get_root_domain(START_URL)
        print(f"Domínio raiz alvo para análise: {root_domain_to_match}")
        
        if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
        
        while urls_to_visit and len(visited_urls) < CRAWL_LIMIT:
            current_url = urls_to_visit.popleft()
            if current_url in visited_urls or 'logout' in current_url: continue
            
            print(f"\nAnalisando [{len(visited_urls)+1}/{CRAWL_LIMIT}]: {current_url}")
            visited_urls.add(current_url)
            driver.get(current_url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1.5)
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            page_analysis = analyze_page_content(soup)
            site_analysis[current_url] = page_analysis
            
            if page_analysis.get('is_checkout_page'):
                try:
                    sanitized_url = re.sub(r'https?://', '', current_url).replace('/', '_').replace('?', '_')
                    screenshot_filename = f"CHECKOUT_{sanitized_url[:100]}.png"
                    screenshot_path = os.path.join(OUTPUT_DIR, screenshot_filename)
                    driver.save_screenshot(screenshot_path)
                    print(f"   -> SCREENSHOT da página de checkout salvo em: {screenshot_path}")
                except Exception as e:
                    print(f"   -> Não foi possível salvar o screenshot: {e}")

            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href or href.startswith(('#', 'mailto:', 'javascript:')): continue
                full_url = urljoin(current_url, href)
                
                if get_root_domain(full_url) == root_domain_to_match:
                    if full_url not in visited_urls and full_url not in urls_to_visit:
                        urls_to_visit.append(full_url)
        
        print(f"\n--- FASE 2: Compilando Dossiê Técnico. {len(site_analysis)} páginas analisadas. ---")
        dossie_tecnico = json.dumps(site_analysis, indent=2, ensure_ascii=False)

        if not gemini_model: raise Exception("Modelo Gemini não foi inicializado.")
            
        print("\n--- FASE 3: Gerando o Blueprint do Projeto com Gemini ---")
        full_prompt = ARCHITECT_META_PROMPT + "\n\n" + dossie_tecnico
        
        response = gemini_model.generate_content(full_prompt)
        
        final_blueprint_file = "PROJETO_GERADO.md"
        with open(final_blueprint_file, "w", encoding='utf-8') as f:
            f.write(response.text)
        
        print("\n--- PROCESSO FINALIZADO! ---")
        print(f"SUCESSO: O Prompt Mestre foi gerado e salvo no arquivo '{final_blueprint_file}'")

    except Exception as e:
        print(f"ERRO NA EXECUÇÃO PRINCIPAL: {e}")
    finally:
        driver.quit()
        print("\n--- NAVEGADOR FECHADO. ---")

if __name__ == "__main__":
    main()