import os
import json
import sys
import time
from dotenv import load_dotenv
import google.generativeai as genai

# --- CONFIGURAÇÕES ---
load_dotenv()
INPUT_FILE = 'prompts_database.json'
OUTPUT_FILE = 'prompts_database_final_PT-BR.json'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

gemini_model = None
translation_cache = {}

def setup_gemini():
    """Configura o modelo Gemini para tradução."""
    global gemini_model
    if not GOOGLE_API_KEY:
        print("AVISO: GOOGLE_API_KEY não encontrada no .env. A tradução não será executada.")
        return False
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("API do Gemini configurada com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao configurar a API do Gemini: {e}")
        return False

def translate_text(text_to_translate):
    """Traduz um texto para português, usando cache para evitar chamadas repetidas."""
    if not gemini_model or not text_to_translate:
        return text_to_translate
    if text_to_translate in translation_cache:
        return translation_cache[text_to_translate]
    
    print(f"   -> Traduzindo: '{text_to_translate[:60]}...'")
    try:
        # Prompt otimizado para a tarefa
        prompt = f"Traduza o seguinte texto do inglês para o Português do Brasil. Mantenha a formatação original, incluindo quebras de linha, e não traduza termos técnicos entre colchetes como [placeholder]. O texto a ser traduzido é: '{text_to_translate}'"
        response = gemini_model.generate_content(prompt)
        translated = response.text.strip()
        translation_cache[text_to_translate] = translated
        time.sleep(1)  # Pausa para respeitar os limites da API
        return translated
    except Exception as e:
        print(f"   -> Falha na tradução: {e}")
        return f"FALHA_NA_TRADUCAO: {text_to_translate}"

def main():
    if not setup_gemini():
        sys.exit("Encerrando script. API do Gemini não pôde ser configurada.")

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data_to_translate = json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de entrada '{INPUT_FILE}' não encontrado. Execute 'consolidate_data.py' primeiro.")
        return
    
    translated_data = []
    print(f"\n--- Iniciando Tradução Completa de {len(data_to_translate)} entradas ---")

    for i, entry in enumerate(data_to_translate):
        print(f"Processando entrada {i+1}/{len(data_to_translate)}: '{entry['title']}'")
        
        # Cria um novo dicionário com todos os campos traduzidos
        new_entry = {
            "category": translate_text(entry['category']),
            "title": translate_text(entry['title']),
            "translated_prompts": [translate_text(p) for p in entry['original_prompts']],
            "source_url": entry['source_url']
        }
        translated_data.append(new_entry)
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, indent=4, ensure_ascii=False)

    print(f"\nSUCESSO: Base de dados 100% traduzida e salva em '{OUTPUT_FILE}'.")

if __name__ == '__main__':
    main()