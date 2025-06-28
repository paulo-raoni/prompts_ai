import os
import time
import re
import sys  # Importado para melhorar o tratamento de erro
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from dotenv import load_dotenv

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- CONFIGURAÇÕES ---
load_dotenv()
START_URL = os.getenv('START_URL', 'https://aiavalanche.com/')
LOGIN_URL_HINT = os.getenv('PRODUCT_LOGIN_KEYWORD', 'Black Magic') 
WEBSITE_USERNAME = os.getenv('WEBSITE_USERNAME')
WEBSITE_PASSWORD = os.getenv('WEBSITE_PASSWORD')

OUTPUT_DIR = 'BlackMagic_Prompts_Raw'

# --- FUNÇÃO PRINCIPAL (Adaptada para Playwright) ---

def main():
    is_demo_mode = '--demo' in sys.argv
    if is_demo_mode:
        CRAWL_LIMIT = 20
        print("--- Iniciando Crawler com Playwright (MODO DEMO - Limite de 20 páginas) ---")
    else:
        CRAWL_LIMIT = 200
        print(f"--- Iniciando Crawler com Playwright (Modo Completo - Limite de {CRAWL_LIMIT} páginas) ---")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()

        try:
            if WEBSITE_USERNAME and WEBSITE_PASSWORD:
                print("\n--- Iniciando Rotina de Login com Playwright ---")
                page.goto(START_URL, timeout=60000)
                page.get_by_role("link", name=re.compile("Login", re.IGNORECASE)).click()
                
                # 1. CORREÇÃO: Usamos o nome exato do link de login para evitar ambiguidade.
                # O log de erro nos informou que o nome do link correto é "ChatGPT Black Magic Login".
                page.get_by_role("link", name="ChatGPT Black Magic Login").click()
                
                page.locator("#user_login").fill(WEBSITE_USERNAME)
                page.locator("#user_pass").fill(WEBSITE_PASSWORD)
                page.locator("#wp-submit").click()
                
                page.wait_for_load_state('networkidle', timeout=60000)
                print(f"-> LOGIN BEM-SUCEDIDO! URL atual: {page.url}")
            else:
                print("AVISO: Credenciais não encontradas. O crawler continuará deslogado.")
                page.goto(START_URL, timeout=60000)

        except (PlaywrightTimeoutError, Exception) as e:
            print(f"!!! ERRO CRÍTICO no login: {e}")
            browser.close()
            # 2. CORREÇÃO: O script agora termina com um código de erro.
            # Isso fará com que o `main.py` pare o pipeline imediatamente.
            sys.exit(1)
            
        start_page_after_login = page.url
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        q = deque([start_page_after_login])
        visited_urls = {start_page_after_login}
        root_domain = ".".join(urlparse(START_URL).netloc.split('.')[-2:])
        
        page_counter = 0

        while q and page_counter < CRAWL_LIMIT:
            url_to_process = q.popleft()
            page_counter += 1
            print(f"\nProcessando [{page_counter}/{CRAWL_LIMIT}]: {url_to_process}")

            try:
                page.goto(url_to_process, wait_until='domcontentloaded', timeout=60000)
                page_source = page.content()
                soup = BeautifulSoup(page_source, 'lxml')
                
                title_element = soup.find('title') or soup.find('h1') or soup.find('h2')
                title = title_element.get_text(strip=True) if title_element else "Pagina_Sem_Titulo"
                
                main_content = soup.find('main', id='content')
                category_element = main_content.find('h4', class_='elementor-heading-title') if main_content else None
                category = category_element.get_text(strip=True) if category_element else "Navegacao"
                
                s_category = re.sub(r'[^\w\s-]', '', category).strip().replace(" ", "_")
                s_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
                if not s_title: s_title = f"pagina_{page_counter}"
                
                original_s_title = s_title
                output_path = os.path.join(OUTPUT_DIR, s_category, s_title)
                version = 2
                while os.path.exists(output_path):
                    s_title = f"{original_s_title}_v{version}"
                    output_path = os.path.join(OUTPUT_DIR, s_category, s_title)
                    version += 1
                
                os.makedirs(output_path, exist_ok=True)
                
                if main_content:
                    page_text = main_content.get_text('\n', strip=True)
                    txt_file_path = os.path.join(output_path, f"{s_title}.txt")
                    with open(txt_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"URL: {url_to_process}\nCATEGORIA_ORIGINAL: {category}\nTITULO_ORIGINAL: {title}\n---\n\n{page_text}")
                    print("   -> Texto bruto salvo.")

                html_file_path = os.path.join(output_path, f"{s_title}.html")
                with open(html_file_path, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print("   -> Código-fonte HTML salvo.")
                
                screenshot_path = os.path.join(output_path, f"{s_title}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"   -> Screenshot de página inteira salvo com sucesso: {os.path.basename(screenshot_path)}")

                links_on_page = soup.find_all('a', href=True)
                for link in links_on_page:
                    href = link['href']
                    if href:
                        full_url = urljoin(url_to_process, href)
                        if root_domain in urlparse(full_url).netloc and '#' not in full_url:
                             if not any(ext in full_url.lower() for ext in ['.jpg', '.png', '.zip', '.pdf', 'logout']):
                                if full_url not in visited_urls:
                                    visited_urls.add(full_url)
                                    q.append(full_url)
                
            except (PlaywrightTimeoutError, Exception) as e:
                print(f"   -> ERRO CRÍTICO ao processar a página {url_to_process}. Erro: {e}")

        browser.close()
        print("\n--- CRAWLER FINALIZADO ---")

if __name__ == '__main__':
    main()