import os
import time
import requests
import google.generativeai as genai
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import collections
import re
from dotenv import load_dotenv

# Importações do Selenium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException # <- NOVO: Importa a exceção específica

# --- CONFIGURAÇÕES E CARREGAMENTO DE VARIÁVEIS ---
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
WEBSITE_USERNAME = os.getenv('WEBSITE_USERNAME')
WEBSITE_PASSWORD = os.getenv('WEBSITE_PASSWORD')

LOGIN_URL = 'https://blackmagic.aiavalanche.com/mylogin/'
BASE_URL = 'https://blackmagic.aiavalanche.com/'
OUTPUT_DIR = 'BlackMagic_Prompts'
POLITE_WAIT_TIME = 2

# --- CONFIGURAÇÃO DA API DO GEMINI ---
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("API do Gemini configurada com sucesso.")
    except Exception as e:
        print(f"Erro ao configurar a API do Gemini: {e}")
        gemini_model = None
else:
    print("AVISO: GOOGLE_API_KEY não encontrada no .env.")
    gemini_model = None

# --- FUNÇÕES AUXILIARES (sem alteração) ---
def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.replace(' ', '_')
    return name[:100]

def translate_prompts_with_gemini(prompts_to_translate):
    if not gemini_model:
        return ["Tradução pulada."] * len(prompts_to_translate)
    meta_prompt = """
    Você é um tradutor especialista... (meta-prompt completo omitido por brevidade)
    """
    try:
        formatted_prompts = json.dumps(prompts_to_translate, indent=2, ensure_ascii=False)
        full_prompt_for_api = meta_prompt + "\n" + formatted_prompts
        print(f"  -> Enviando {len(prompts_to_translate)} prompts para tradução...")
        response = gemini_model.generate_content(full_prompt_for_api)
        cleaned_json_string = response.text.strip().replace('```json', '').replace('```', '')
        translated_data = json.loads(cleaned_json_string)
        print("  -> Tradução recebida com sucesso.")
        return translated_data.get("translations", [])
    except Exception as e:
        print(f"  ! Erro durante a tradução com o Gemini: {e}")
        return [f"Erro na tradução: {e}"] * len(prompts_to_translate)

def download_video(video_url, folder_path, file_name):
    try:
        print(f"  -> Baixando vídeo: {video_url}")
        video_response = requests.get(video_url, stream=True, timeout=30)
        video_response.raise_for_status()
        video_file_path = os.path.join(folder_path, f"{file_name}.mp4")
        with open(video_file_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  -> Vídeo salvo em: {video_file_path}")
        return True
    except requests.RequestException as e:
        print(f"  ! Falha ao baixar o vídeo: {e}")
        return False

# --- LÓGICA PRINCIPAL ---
print("Configurando o driver 'undetected-chromedriver'...")
driver = uc.Chrome(options=uc.ChromeOptions())
print("Driver configurado.")

try:
    # ETAPA DE LOGIN
    print("\n--- Iniciando Etapa de Login ---")
    if not WEBSITE_USERNAME or not WEBSITE_PASSWORD:
        raise ValueError("Usuário ou senha não encontrados no arquivo .env. Encerrando.")
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)
    print("Aguardando página de login carregar...")
    user_field = wait.until(EC.visibility_of_element_located((By.ID, 'user_login')))
    print("Página de login carregada. Preenchendo credenciais...")
    user_field.send_keys(WEBSITE_USERNAME)
    driver.find_element(By.ID, 'user_pass').send_keys(WEBSITE_PASSWORD)
    driver.find_element(By.ID, 'wp-submit').click()
    print("Credenciais enviadas. Aguardando redirecionamento...")
    wait.until(EC.url_changes(LOGIN_URL))
    if "mylogin" in driver.current_url:
        print("!!! ALERTA: O login pode ter falhado. O script ainda está na página de login.")
    else:
        print(f"Login bem-sucedido! URL atual: {driver.current_url}")

    # ETAPA DE CRAWLING
    print("\n--- Iniciando Crawler 6.3 (Resiliente) ---")
    urls_to_visit = collections.deque([BASE_URL])
    visited_urls = {LOGIN_URL}

    while urls_to_visit:
        current_url = urls_to_visit.popleft()
        normalized_url = current_url.strip('/')
        
        if current_url in visited_urls or normalized_url in visited_urls:
            continue
        
        print(f"\nVisitando: {current_url}")
        visited_urls.add(current_url)
        visited_urls.add(normalized_url)

        try:
            driver.get(current_url)
            
            # ######################################################
            # ## PLANO DE CONTINGÊNCIA IMPLEMENTADO AQUI
            # ######################################################
            try:
                print("  -> TENTATIVA: Esperando pelo conteúdo principal (até 20s)...")
                wait.until(EC.visibility_of_element_located((By.ID, "content")))
                print("  -> SUCESSO: Conteúdo principal encontrado.")
            except TimeoutException:
                print("  -> AVISO: A 'espera inteligente' falhou (normal na pág. inicial). Usando espera fixa de 5s como contingência.")
                time.sleep(5)
            
            page_html = driver.page_source
            soup = BeautifulSoup(page_html, 'lxml')
            
            all_links_on_page = soup.find_all('a', href=True)
            main_content = soup.find('main', id='content') or soup.find('body')
            
            if main_content:
                category_class = next((c for c in main_content.get('class', []) if c.startswith('category-')), None)
                if category_class:
                    print("     -> Esta é uma página de prompt. Extraindo dados...")
                    category_name = category_class.replace('category-', '').replace('-', ' ').title()
                    s_category_name = sanitize_filename(category_name)
                    page_title_element = main_content.find('h2', class_='elementor-heading-title')
                    page_title = page_title_element.get_text(strip=True) if page_title_element else "Prompt_Sem_Titulo"
                    s_page_title = sanitize_filename(page_title)
                    prompt_folder_path = os.path.join(OUTPUT_DIR, s_category_name, s_page_title)
                    os.makedirs(prompt_folder_path, exist_ok=True)
                    prompts_on_page = [code.get_text(strip=True) for code in main_content.select('div.prismjs-default code')]

                    if prompts_on_page:
                        translated_prompts = translate_prompts_with_gemini(prompts_on_page)
                        text_file_path = os.path.join(prompt_folder_path, f"{s_page_title}.txt")
                        with open(text_file_path, 'w', encoding='utf-8') as f:
                            f.write(f"TEMA: {page_title}\nCATEGORIA: {category_name}\nFONTE: {current_url}\n\n{'='*50}\n\n")
                            for i, (original, translated) in enumerate(zip(prompts_on_page, translated_prompts), 1):
                                f.write(f"--- PROMPT {i} ---\n\nORIGINAL (ENGLISH):\n```\n{original}\n```\n\nTRADUÇÃO (PORTUGUÊS):\n```\n{translated}\n```\n\n---\n")
                        print(f"  -> Arquivo de texto salvo em: {text_file_path}")
                    video_element = main_content.find('video', class_='elementor-video')
                    if video_element and video_element.get('src'):
                        download_video(video_element['src'], prompt_folder_path, s_page_title)
                else:
                    print("     -> Esta não é uma página de prompt. Apenas buscando links.")

                for link in all_links_on_page:
                    full_url = urljoin(BASE_URL, link['href'])
                    parsed_url = urlparse(full_url)
                    clean_url = parsed_url._replace(query='', fragment='').geturl()
                    if parsed_url.netloc == urlparse(BASE_URL).netloc and clean_url not in visited_urls and clean_url not in urls_to_visit:
                        urls_to_visit.append(clean_url)
                print(f"  -> Status da fila: {len(urls_to_visit)} URLs para visitar.")
        except Exception as e:
            print(f"  ! Erro ao processar {current_url}: {e}")
except Exception as e:
    print(f"ERRO FATAL: {e}")
finally:
    driver.quit()
    print("\n--- NAVEGADOR FECHADO. OPERAÇÃO FINALIZADA! ---")