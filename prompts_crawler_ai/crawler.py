import os
import time
import re
import sys
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

OUTPUT_DIR = 'Arsenal_Dev_AI_Raw'

# --- FUNÇÃO DE PARSE DO MENU (VERSÃO FINAL E PRECISA v5) ---
def parse_menu_structure(soup, base_url):
    """
    Analisa o HTML da página do menu (baseado no debug_menu_page.html)
    para extrair a estrutura de forma precisa, usando o contêiner pai como referência.
    """
    print("   -> Analisando a estrutura do menu principal (Lógica v5)...")
    menu_map = {}
    
    # Encontra todos os contêineres de seção de nível superior
    section_containers = soup.select('div.elementor-element[data-element_type="container"]')
    
    for container in section_containers:
        # Procura um título de seção DENTRO do contêiner atual
        title_element = container.select_one('h2.elementor-heading-title')
        if not title_element:
            continue
            
        section_text_full = title_element.get_text(strip=True)
        # Ignora títulos que não são de seções de menu
        if "Trying to find a prompt?" in section_text_full or "Need help?" in section_text_full:
            continue

        emoji_match = re.match(r'^(\W+)', section_text_full)
        if emoji_match:
            section_emoji = emoji_match.group(1).strip()
            section_title = section_text_full.replace(section_emoji, '', 1).strip()
        else:
            section_emoji = "✨"
            section_title = section_text_full

        # Procura todos os links de prompts DENTRO do mesmo contêiner
        category_links = container.select('h3.elementor-post__title a')
        
        for link in category_links:
            href = link.get('href')
            if not href or href.startswith('#') or not href.strip():
                continue

            full_url = urljoin(base_url, href)
            category_name = link.get_text(strip=True)

            if full_url not in menu_map:
                menu_map[full_url] = {
                    "section": section_title,
                    "category": category_name,
                    "emoji": section_emoji 
                }
            
    print(f"   -> Estrutura do menu mapeada. {len(menu_map)} itens encontrados.")
    return menu_map


# --- FUNÇÃO PRINCIPAL ---
def main():
    is_demo_mode = '--demo' in sys.argv
    if is_demo_mode:
        CRAWL_LIMIT = 20
        print("--- Iniciando Crawler com Playwright (MODO DEMO - Limite de 20 páginas) ---")
    else:
        CRAWL_LIMIT = 200
        print(f"--- Iniciando Crawler com Playwright (Modo Completo - Limite de {CRAWL_LIMIT} páginas) ---")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()

        try:
            if WEBSITE_USERNAME and WEBSITE_PASSWORD:
                print("\n--- Iniciando Rotina de Login com Playwright ---")
                page.goto(START_URL, timeout=60000)
                page.get_by_role("link", name=re.compile("Login", re.IGNORECASE)).click()
                page.get_by_role("link", name="ChatGPT Black Magic Login").click()
                page.locator("#user_login").fill(WEBSITE_USERNAME)
                page.locator("#user_pass").fill(WEBSITE_PASSWORD)
                page.locator("#wp-submit").click()
                page.wait_for_load_state('networkidle', timeout=60000)
                print(f"-> LOGIN BEM-SUCEDIDO! URL atual: {page.url}")
            else:
                print("AVISO: Credenciais não encontradas.")
                page.goto(START_URL, timeout=60000)

        except (PlaywrightTimeoutError, Exception) as e:
            print(f"!!! ERRO CRÍTICO no login: {e}")
            browser.close()
            sys.exit(1)

        start_page_after_login = page.url
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        page_source_menu = page.content()
        
        # --- NOVO BLOCO: Guardar o Menu Principal ---
        print("\n-> Guardando dados da página do menu principal...")
        menu_output_path = os.path.join(OUTPUT_DIR, "_Menu_Principal")
        os.makedirs(menu_output_path, exist_ok=True)
        try:
            # Guarda o screenshot completo
            menu_screenshot_path = os.path.join(menu_output_path, "screenshot_menu.png")
            page.screenshot(path=menu_screenshot_path, full_page=True)
            print(f"   -> Screenshot do menu guardado em: {menu_screenshot_path}")
            
            # Guarda o HTML
            menu_html_path = os.path.join(menu_output_path, "menu_principal.html")
            with open(menu_html_path, 'w', encoding='utf-8') as f:
                f.write(page_source_menu)
            print(f"   -> HTML do menu guardado em: {menu_html_path}")
        except Exception as e:
            print(f"   -> ERRO ao guardar dados do menu: {e}")
        # --- FIM DO NOVO BLOCO ---

        soup_menu = BeautifulSoup(page_source_menu, 'lxml')
        menu_structure_map = parse_menu_structure(soup_menu, start_page_after_login)

        if not menu_structure_map:
            print("!!! ERRO FATAL: Nenhuma estrutura de menu foi extraída. O crawler não pode continuar.")
            browser.close()
            sys.exit(1)
            
        q = deque(menu_structure_map.keys())
        visited_urls = set(menu_structure_map.keys())
        
        page_counter = 0

        while q and page_counter < CRAWL_LIMIT:
            url_to_process = q.popleft()
            page_counter += 1
            print(f"\nProcessando [{page_counter}/{CRAWL_LIMIT}]: {url_to_process}")

            try:
                page.goto(url_to_process, wait_until='domcontentloaded', timeout=60000)
                page_source_prompt = page.content()
                soup_prompt = BeautifulSoup(page_source_prompt, 'lxml')
                
                title_element = soup_prompt.find('title') or soup_prompt.find('h1') or soup_prompt.find('h2')
                title = title_element.get_text(strip=True) if title_element else "Pagina_Sem_Titulo"
                
                menu_info = menu_structure_map.get(url_to_process, {})
                section = menu_info.get("section", "Geral")
                category = menu_info.get("category", "Geral")
                emoji = menu_info.get("emoji", "✨")

                s_category = re.sub(r'[^\w\s-]', '', category).strip().replace(" ", "_")
                s_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
                if not s_title: s_title = f"pagina_{page_counter}"
                
                output_path = os.path.join(OUTPUT_DIR, re.sub(r'[^\w\s-]', '', section).strip().replace(" ", "_"), s_category, s_title)
                
                if os.path.exists(output_path):
                     print(f"   -> AVISO: A pasta '{s_title}' já existe. Pulando.")
                     continue
                
                os.makedirs(output_path, exist_ok=True)
                
                main_content = soup_prompt.find('main', id='content')
                if main_content:
                    page_text = main_content.get_text('\n', strip=True)
                    txt_file_path = os.path.join(output_path, f"{s_title}.txt")
                    with open(txt_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"URL: {url_to_process}\n")
                        f.write(f"SECTION: {section}\n")
                        f.write(f"CATEGORY: {category}\n")
                        f.write(f"EMOJI: {emoji}\n")
                        f.write(f"TITULO_ORIGINAL: {title}\n---\n\n{page_text}")
                    print("   -> Texto bruto enriquecido salvo.")

                html_file_path = os.path.join(output_path, f"{s_title}.html")
                with open(html_file_path, 'w', encoding='utf-8') as f:
                    f.write(page_source_prompt)
                print("   -> Código-fonte HTML salvo.")
                
                screenshot_path = os.path.join(output_path, f"{s_title}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print("   -> Screenshot de página inteira salvo.")
                
            except (PlaywrightTimeoutError, Exception) as e:
                print(f"   -> ERRO CRÍTICO ao processar a página {url_to_process}. Erro: {e}")

        browser.close()
        print("\n--- CRAWLER FINALIZADO ---")

if __name__ == '__main__':
    main()