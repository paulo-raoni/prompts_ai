import os
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from dotenv import load_dotenv

# Importações do Selenium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURAÇÕES ---
load_dotenv()
# Usaremos as URLs do nosso .env, tornando o script mais genérico
START_URL = os.getenv('START_URL', 'https://aiavalanche.com/')
# Palavra-chave para encontrar o link de login correto na página de links
LOGIN_URL_HINT = os.getenv('PRODUCT_LOGIN_KEYWORD', 'Black Magic') 
WEBSITE_USERNAME = os.getenv('WEBSITE_USERNAME')
WEBSITE_PASSWORD = os.getenv('WEBSITE_PASSWORD')

# O crawler agora salva em uma pasta para dados brutos
OUTPUT_DIR = 'BlackMagic_Prompts_Raw'
CRAWL_LIMIT = 150 # Limite para não rodar para sempre

# --- FUNÇÃO DE LOGIN ROBUSTA ---
def perform_intelligent_login(driver, wait):
    """
    Executa o fluxo de login multi-etapas que já validamos como o mais eficaz.
    """
    if not (WEBSITE_USERNAME and WEBSITE_PASSWORD):
        print("AVISO: Credenciais não encontradas no .env. O crawler continuará deslogado.")
        return True
        
    print("\n--- Iniciando Rotina de Login Inteligente ---")
    try:
        driver.get(START_URL)
        print(f"1. Acessando página inicial: {START_URL}")

        # Tenta clicar no link de login genérico na landing page
        wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Login"))).click()
        print("2. Navegou para a página de links de login.")
        time.sleep(2) # Pequena pausa para a página carregar
        
        # Na página de links, clica no link específico do produto
        wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, LOGIN_URL_HINT))).click()
        print("3. Navegou para a página de login final.")
        time.sleep(2)

        # Preenche o formulário de login final
        wait.until(EC.visibility_of_element_located((By.ID, "user_login"))).send_keys(WEBSITE_USERNAME)
        driver.find_element(By.ID, "user_pass").send_keys(WEBSITE_PASSWORD)
        driver.find_element(By.ID, "wp-submit").click()
        
        print("4. Credenciais enviadas. Aguardando confirmação...")
        time.sleep(5) # Pausa para o redirecionamento
        print(f"-> LOGIN BEM-SUCEDIDO! URL atual: {driver.current_url}")
        return True
    except Exception as e:
        print(f"!!! ERRO CRÍTICO no login: {e}. O crawler não pode continuar.")
        return False

# --- FUNÇÃO PRINCIPAL DE RASPAGEM ---
def main():
    print(f"--- Iniciando Crawler (Versão Final Refatorada) ---")
    
    # Não forçamos mais a versão. Deixamos a biblioteca tentar a melhor abordagem primeiro.
    driver = uc.Chrome(options=uc.ChromeOptions(), use_subprocess=True)
    wait = WebDriverWait(driver, 15)

    try:
        if not perform_intelligent_login(driver, wait):
            return # Encerra se o login falhar

        print("\n--- FASE DE RASPAGEM DE DADOS BRUTOS ---")
        start_page_after_login = driver.current_url
        urls_to_visit = deque([start_page_after_login])
        visited_urls = set()
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        
        # Usa o domínio raiz para garantir que navegamos em subdomínios (ex: blackmagic.aiavalanche.com)
        root_domain = ".".join(urlparse(START_URL).netloc.split('.')[-2:])

        while urls_to_visit and len(visited_urls) < CRAWL_LIMIT:
            current_url = urls_to_visit.popleft()
            if current_url in visited_urls or 'logout' in current_url:
                continue

            print(f"\nRaspando [{len(visited_urls)+1}/{CRAWL_LIMIT}]: {current_url}")
            visited_urls.add(current_url)
            driver.get(current_url)
            
            try:
                # Espera por um elemento básico para garantir que a página carregou
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except TimeoutException:
                print("   -> Página demorou muito para carregar. Pulando...")
                continue
            
            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            main_content = soup.find('main', id='content')
            if main_content and main_content.find('div', class_='prismjs-default'):
                category_element = main_content.find('h4', class_='elementor-heading-title')
                title_element = main_content.find('h2', class_='elementor-heading-title')
                
                category = category_element.get_text(strip=True) if category_element else "Geral"
                title = title_element.get_text(strip=True) if title_element else f"prompt_{len(visited_urls)}"
                
                s_category = re.sub(r'[^\w\s-]', '', category).strip().replace(" ", "_")
                s_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
                
                prompts_on_page = [code.get_text(strip=True) for code in main_content.select('div.prismjs-default code')]

                if prompts_on_page:
                    output_path = os.path.join(OUTPUT_DIR, s_category, s_title)
                    os.makedirs(output_path, exist_ok=True)
                    
                    file_path = os.path.join(output_path, f"{s_title}.txt")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"URL: {current_url}\n")
                        f.write(f"CATEGORIA_ORIGINAL: {category}\n")
                        f.write(f"TITULO_ORIGINAL: {title}\n")
                        f.write("\n---\n\n")
                        f.write("\n\n---\n\n".join(prompts_on_page))
                    print(f"   -> DADOS EM INGLÊS SALVOS EM: {file_path}")
            else:
                print("   -> Página de navegação. Procurando por novos links...")

            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href or href.startswith(('#', 'mailto:', 'javascript:')):
                    continue
                full_url = urljoin(current_url, href)
                # Verifica se o link pertence ao mesmo domínio raiz
                if root_domain in urlparse(full_url).netloc and full_url not in visited_urls and full_url not in urls_to_visit:
                    urls_to_visit.append(full_url)

    except Exception as e:
        print(f"ERRO NA EXECUÇÃO PRINCIPAL: {e}")
    finally:
        driver.quit()
        print("\n--- RASPAGEM CONCLUÍDA ---")

if __name__ == '__main__':
    main()