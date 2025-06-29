import os
import json
import asyncio
import sys
import re
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAÇÕES ---
load_dotenv()
INPUT_DIR = 'output/Arsenal_Dev_AI_Raw' 
OUTPUT_FILE = 'output/prompts_database_structured.json'
PROMPT_TEMPLATE_FILE = 'templates/structure_prompt_template.txt'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
CONCURRENCY_LIMIT = 5
DEMO_PROCESSING_LIMIT = 5

gemini_model = None
prompt_template_content = ""

def load_prompt_template():
    """Carrega o conteúdo do prompt a partir do arquivo de template."""
    global prompt_template_content
    try:
        with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            prompt_template_content = f.read()
        return True
    except FileNotFoundError:
        print(f"ERRO FATAL: O arquivo de template do prompt '{PROMPT_TEMPLATE_FILE}' não foi encontrado.")
        return False

def setup_gemini():
    """Configura o modelo Gemini com capacidade de visão."""
    global gemini_model
    if not GOOGLE_API_KEY:
        print("AVISO: GOOGLE_API_KEY não encontrada. A estruturação não será executada.")
        return False
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        print("API do Gemini (Vision) configurada com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao configurar a API do Gemini: {e}")
        return False

def parse_txt_header(file_path):
    """Lê o cabeçalho de um arquivo .txt e extrai os metadados."""
    metadata = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == '---':
                break
            match = re.match(r'([^:]+):\s*(.*)', line)
            if match:
                key = match.group(1).strip().lower().replace("_", "")
                value = match.group(2).strip()
                metadata[key] = value
    return metadata

async def structure_content_task(semaphore, entry_path, entry_name):
    """Função assíncrona que processa uma única entrada (pasta)."""
    async with semaphore:
        print(f"Processando: {entry_name}")
        txt_file_path = os.path.join(entry_path, f"{entry_name}.txt")
        png_file_path = os.path.join(entry_path, f"{entry_name}.png")
        html_file_path = os.path.join(entry_path, f"{entry_name}.html")

        if not (os.path.exists(txt_file_path) and os.path.exists(png_file_path) and os.path.exists(html_file_path)):
            print(f"      -> AVISO: Faltando arquivos para '{entry_name}'. Pulando.")
            return None

        metadata = parse_txt_header(txt_file_path)
        
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        with open(html_file_path, 'r', encoding='utf-8') as f:
            raw_html = f.read()
        
        try:
            img = Image.open(png_file_path)
            
            prompt = prompt_template_content.format(
                section=metadata.get('section', 'Geral'),
                category=metadata.get('category', 'Geral'),
                emoji=metadata.get('emoji', '✨'),
                main_title=metadata.get('titulooriginal', 'Sem Título'),
                source_url=metadata.get('url', '')
            )
            
            print(f"   -> Enviando para análise: {entry_name}")
            response = await gemini_model.generate_content_async([
                prompt, 
                "--- TEXTO BRUTO ---\n" + raw_text, 
                "--- CÓDIGO-FONTE HTML ---\n" + raw_html,
                img
            ])
            
            # Adiciona uma verificação para garantir que a resposta não está vazia ou bloqueada
            if not response.parts:
                print(f"      -> ERRO: A API retornou uma resposta vazia para '{entry_name}'. Possivelmente bloqueado por segurança.")
                return None

            cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
            structured_data = json.loads(cleaned_response)
            print(f"   -> Análise concluída: {entry_name}")
            return structured_data

        except Exception as e:
            # --- TRATAMENTO DE ERRO MELHORADO ---
            # Imprime o erro exato que está a acontecer
            print(f"      -> ERRO FATAL AO PROCESSAR '{entry_name}': {e}")
            # Você pode descomentar a linha abaixo para fazer o pipeline parar imediatamente
            # sys.exit(1) 
            return None

async def main():
    is_demo_mode = '--demo' in sys.argv
    
    if not load_prompt_template():
        return
    if not setup_gemini():
        return
    if not os.path.exists(INPUT_DIR):
        print(f"ERRO: O diretório de entrada '{INPUT_DIR}' não foi encontrado.")
        return

    all_entries = []
    # Lógica corrigida para encontrar as pastas corretas
    for root, dirs, files in os.walk(INPUT_DIR):
        # Estamos à procura de pastas que contenham um .txt, .png e .html com o mesmo nome da pasta
        if os.path.basename(root) + ".txt" in files:
            entry_path = root
            entry_name = os.path.basename(root)
            all_entries.append((entry_path, entry_name))

    entries_to_process = all_entries[:DEMO_PROCESSING_LIMIT] if is_demo_mode else all_entries
    if is_demo_mode:
        print(f"--- MODO DEMO: Processando as primeiras {len(entries_to_process)} entradas de {len(all_entries)} encontradas. ---")

    if not entries_to_process:
        print("AVISO: Nenhuma entrada válida foi encontrada para processar.")
        # Cria um arquivo vazio para não quebrar o resto do pipeline em caso de 0 entradas
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return

    tasks = []
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    print(f"\n--- Iniciando Estruturação Paralela de {len(entries_to_process)} entradas ---")

    for entry_path, entry_name in entries_to_process:
        tasks.append(structure_content_task(semaphore, entry_path, entry_name))

    results = await asyncio.gather(*tasks)
    all_structured_data = [res for res in results if res is not None]
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_structured_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSUCESSO: {len(all_structured_data)} de {len(entries_to_process)} entradas estruturadas e salvas em '{OUTPUT_FILE}'.")

if __name__ == '__main__':
    asyncio.run(main())