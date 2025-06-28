import os
import json
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# --- CONFIGURAÇÕES ---
load_dotenv()
INPUT_FILE = 'prompts_database_structured.json' 
OUTPUT_FILE = 'prompts_database_final.json' 
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PRODUCT_NAME = "Arsenal Dev AI"
OLD_BRAND_NAME = "Black Magic"
NEW_BRAND_NAME = "Brazilian Dev" 
OLD_SITE_NAME = "aiavalanche"

CACHE_FILE = 'translation_cache_structured.json'
CONCURRENCY_LIMIT = 5
gemini_model = None

# --- ESTRATÉGIA DE CORREÇÃO DE FORMATAÇÃO ---
# Para evitar que a interface de chat quebre a formatação, 
# o prompt agora é construído em duas partes.

PROMPT_HEADER = f"""
Você é um especialista em localização de software. Sua tarefa é traduzir o conteúdo do seguinte objeto JSON para o Português do Brasil.

**Diretrizes Críticas:**
1.  **Traduza APENAS os valores de texto.** Não altere as chaves nem a estrutura do objeto.
2.  **NÃO traduza o valor da chave "emoji".** Mantenha o emoji original que receber.
3.  **Tom e Estilo:** Mantenha um tom profissional e acessível.
4.  **Substituição de Marca do Produto:** Qualquer menção a '{OLD_BRAND_NAME}' ou 'Magia Negra' deve ser **obrigatoriamente substituída** por '{PRODUCT_NAME}'.
5.  **Substituição de Marca do Site:** Qualquer menção a '{OLD_SITE_NAME}', 'avalanche ai' ou 'avalanche.ai' deve ser **obrigatoriamente substituída** por '{NEW_BRAND_NAME}'.
6.  **Formato de Saída:** Sua resposta deve ser **APENAS** o objeto JSON completo com os valores traduzidos.

**Objeto JSON para traduzir:**
"""

# A parte que causava o problema de formatação agora está isolada.
JSON_BLOCK_TEMPLATE = """```json
{json_to_translate}
```"""

# O template final é a junção das duas partes.
TRANSLATION_PROMPT_TEMPLATE = PROMPT_HEADER + JSON_BLOCK_TEMPLATE


def setup_gemini():
    global gemini_model
    if not GOOGLE_API_KEY:
        print("AVISO: GOOGLE_API_KEY não encontrada.")
        return False
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        print("API do Gemini configurada com sucesso.")
        return True
    except Exception as e:
        print(f"Erro ao configurar a API do Gemini: {e}")
        return False

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError: return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

async def translate_entry_task(semaphore, entry_to_translate):
    async with semaphore:
        title = entry_to_translate.get('main_title', 'Sem Título')
        print(f"Processando: '{title}'")
        # A lógica de formatação do prompt usa o novo template
        json_string = json.dumps(entry_to_translate, indent=2, ensure_ascii=False)
        prompt = TRANSLATION_PROMPT_TEMPLATE.format(json_to_translate=json_string)

        try:
            print(f"   -> Enviando para tradução: '{title}'")
            response = await gemini_model.generate_content_async(prompt)
            cleaned_response = response.text.strip().lstrip("```json").rstrip("```").strip()
            translated_data = json.loads(cleaned_response)
            print(f"   -> Tradução concluída: '{title}'")
            return translated_data
        except Exception as e:
            print(f"      -> ERRO ao traduzir '{title}': {e}")
            return entry_to_translate

async def main():
    if not setup_gemini(): return
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)
        if not structured_data:
            print(f"AVISO: O ficheiro de entrada '{INPUT_FILE}' está vazio.")
            return
    except Exception as e:
        print(f"ERRO ao ler o ficheiro de entrada: {e}")
        return

    translation_cache = load_cache()
    final_translated_data = []
    tasks = []
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    print(f"\n--- Iniciando Tradução Estrutural Paralela (limite de {CONCURRENCY_LIMIT} tarefas) ---")

    for entry in structured_data:
        entry_hash = str(hash(json.dumps(entry, sort_keys=True)))
        if entry_hash in translation_cache:
            final_translated_data.append(translation_cache[entry_hash])
        else:
            tasks.append((entry_hash, translate_entry_task(semaphore, entry)))

    if tasks:
        print(f"Enviando {len(tasks)} novas entradas para tradução...")
        task_results = await asyncio.gather(*[task for _, task in tasks])
        for (entry_hash, _), result in zip(tasks, task_results):
            final_translated_data.append(result)
            translation_cache[entry_hash] = result
        save_cache(translation_cache)

    print(f"\nProcessamento concluído. A gravar {len(final_translated_data)} entradas totais em '{OUTPUT_FILE}'...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_translated_data, f, indent=4, ensure_ascii=False)
    print(f"\nSUCESSO: {len(final_translated_data)} entradas traduzidas e salvas em '{OUTPUT_FILE}'.")

if __name__ == '__main__':
    asyncio.run(main())