import os
import time
import re
import requests
import hashlib
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from dotenv import load_dotenv
from PIL import Image

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# --- CONFIGURAÇÕES ---
load_dotenv()
START_URL = os.getenv('START_URL', 'https://aiavalanche.com/')
LOGIN_URL_HINT = os.getenv('PRODUCT_LOGIN_KEYWORD', 'Black Magic') 
WEBSITE_USERNAME = os.getenv('WEBSITE_USERNAME')
WEBSITE_PASSWORD = os.getenv('WEBSITE_PASSWORD')

OUTPUT_DIR = 'BlackMagic_Prompts_Raw'
CRAWL_LIMIT = 200

# --- FUNÇÕES AUXILIARES ---

def perform_intelligent_login(driver, wait):
    """Executa o fluxo de login multi-etapas."""
    if not (WEBSITE_USERNAME and WEBSITE_PASSWORD):
        print("AVISO: Credenciais não encontradas. O crawler continuará deslogado.")
        return True
    print("\n--- Iniciando Rotina de Login Inteligente ---")
    try:
        driver.get(START_URL)
        wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Login"))).click()
        time.sleep(2)
        wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, LOGIN_URL_HINT))).click()
        time.sleep(2)
        wait.until(EC.visibility_of_element_located((By.ID, "user_login"))).send_keys(WEBSITE_USERNAME)
        driver.find_element(By.ID, "user_pass").send_keys(WEBSITE_PASSWORD)
        driver.find_element(By.ID, "wp-submit").click()
        time.sleep(5)
        print(f"-> LOGIN BEM-SUCEDIDO! URL atual: {driver.current_url}")
        return True
    except Exception as e:
        print(f"!!! ERRO CRÍTICO no login: {e}")
        return False

def capture_stitched_screenshot(driver, path):
    """Rola a página e tira múltiplos screenshots, costurando-os numa imagem final."""
    print("   -> Iniciando captura de screenshot costurado...")
    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(1)
    viewport_height = driver.execute_script("return window.innerHeight")
    total_height = driver.execute_script("return document.body.scrollHeight")
    if total_height == 0: 
        print("   -> AVISO: Página com altura zero, screenshot pode estar vazio.")
        return False
    
    stitched_image = Image.new('RGB', (1280, total_height))
    y_offset = 0
    while y_offset < total_height:
        driver.execute_script(f"window.scrollTo(0, {y_offset})")
        time.sleep(0.5)
        png_data = driver.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(png_data))
        stitched_image.paste(screenshot, (0, y_offset))
        y_offset += viewport_height
        
    try:
        stitched_image.save(path)
        print(f"   -> Screenshot costurado salvo com sucesso: {os.path.basename(path)}")
        return True
    except Exception as e:
        print(f"   -> ERRO ao salvar screenshot costurado: {e}")
        return False

# --- FUNÇÃO PRINCIPAL ---

def main():
    print("--- Iniciando Crawler (v14.0 - Nomes Descritivos) ---")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.set_window_size(1280, 800)
    wait = WebDriverWait(driver, 20)

    try:
        if not perform_intelligent_login(driver, wait):
            return

        start_page_after_login = driver.current_url
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
                driver.get(url_to_process)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'lxml')
                
                # --- LÓGICA DE NOMEAÇÃO E EXTRAÇÃO (ATUALIZADA) ---
                
                # Prioriza a tag <title> do HTML para nomes mais descritivos
                title_element = soup.find('title')
                if not title_element or not title_element.get_text(strip=True):
                    # Se não houver <title>, usa o <h1> ou <h2> como fallback
                    title_element = soup.find('h1') or soup.find('h2')
                
                title = title_element.get_text(strip=True) if title_element else "Pagina_Sem_Titulo"

                # Define a categoria (se existir) ou usa "Navegacao" como padrão
                main_content = soup.find('main', id='content')
                category_element = main_content.find('h4', class_='elementor-heading-title') if main_content else None
                category = category_element.get_text(strip=True) if category_element else "Navegacao"
                
                s_category = re.sub(r'[^\w\s-]', '', category).strip().replace(" ", "_")
                
                # Usa apenas o título da página para nomear, de forma mais limpa
                s_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
                if not s_title: s_title = f"pagina_{page_counter}"
                
                # Lógica para evitar colisões de nome, criando versões.
                original_s_title = s_title
                output_path = os.path.join(OUTPUT_DIR, s_category, s_title)
                version = 2
                while os.path.exists(output_path):
                    print(f"   -> AVISO: A pasta '{s_title}' já existe. Tentando versão {version}...")
                    s_title = f"{original_s_title}_v{version}"
                    output_path = os.path.join(OUTPUT_DIR, s_category, s_title)
                    version += 1
                
                os.makedirs(output_path, exist_ok=True)
                
                # Salva o texto bruto (se houver conteúdo principal)
                if main_content:
                    page_text = main_content.get_text('\n', strip=True)
                    txt_file_path = os.path.join(output_path, f"{s_title}.txt")
                    with open(txt_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"URL: {url_to_process}\nCATEGORIA_ORIGINAL: {category}\nTITULO_ORIGINAL: {title}\n---\n\n{page_text}")
                    print(f"   -> Texto bruto salvo.")
                else:
                    print("   -> Página sem conteúdo principal (<main>), salvando apenas HTML e screenshot.")

                # Salva o HTML completo
                html_file_path = os.path.join(output_path, f"{s_title}.html")
                with open(html_file_path, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"   -> Código-fonte HTML salvo.")
                
                # Salva o screenshot costurado
                capture_stitched_screenshot(driver, os.path.join(output_path, f"{s_title}.png"))

                # Adiciona novos links à fila
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
                
            except Exception as e:
                print(f"   -> ERRO CRÍTICO ao processar a página. Erro: {e}")

    except Exception as e:
        print(f"ERRO NA EXECUÇÃO PRINCIPAL: {e}")
    finally:
        driver.quit()
        print("\n--- CRAWLER FINALIZADO ---")

if __name__ == '__main__':
    main()
