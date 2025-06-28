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
INPUT_DIR = 'Arsenal_Dev_AI_Raw' 
OUTPUT_FILE = 'prompts_database_structured.json'
# --- O NOME DO NOSSO NOVO ARQUIVO DE TEMPLATE ---
PROMPT_TEMPLATE_FILE = 'structure_prompt_template.txt'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
CONCURRENCY_LIMIT = 5
DEMO_PROCESSING_LIMIT = 20

gemini_model = None
# --- A VARIÁVEL DO PROMPT SERÁ CARREGADA DO ARQUIVO ---
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
            return None

        metadata = parse_txt_header(txt_file_path)
        
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        with open(html_file_path, 'r', encoding='utf-8') as f:
            raw_html = f.read()
        
        try:
            img = Image.open(png_file_path)
            
            # Formata o prompt que foi carregado do arquivo externo
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
            
            cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
            structured_data = json.loads(cleaned_response)
            print(f"   -> Análise concluída: {entry_name}")
            return structured_data

        except Exception as e:
            print(f"      -> ERRO ao processar {entry_name}: {e}")
            return None

async def main():
    is_demo_mode = '--demo' in sys.argv
    
    # Carrega o prompt do arquivo antes de qualquer outra coisa
    if not load_prompt_template():
        return
    if not setup_gemini():
        return
    if not os.path.exists(INPUT_DIR):
        print(f"ERRO: O diretório de entrada '{INPUT_DIR}' não foi encontrado.")
        return

    all_entries = []
    for category_name in os.listdir(INPUT_DIR):
        category_path = os.path.join(INPUT_DIR, category_name)
        if os.path.isdir(category_path):
            for entry_name in os.listdir(category_path):
                entry_path = os.path.join(category_path, entry_name)
                if os.path.isdir(entry_path):
                    all_entries.append((entry_path, entry_name))

    entries_to_process = all_entries[:DEMO_PROCESSING_LIMIT] if is_demo_mode else all_entries
    if is_demo_mode:
        print(f"--- MODO DEMO: Processando as primeiras {len(entries_to_process)} entradas de {len(all_entries)} encontradas. ---")

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