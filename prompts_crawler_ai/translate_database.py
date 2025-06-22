import os
import json
import time
from dotenv import load_dotenv
import google.generativeai as genai

# --- CONFIGURAÇÕES ---
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DATABASE_FILE = 'prompts_database.json'
OUTPUT_FILE = 'prompts_database_translated.json' # Salva em um novo arquivo para segurança

# --- CONFIGURAÇÃO DA API DO GEMINI ---
if not GOOGLE_API_KEY:
    print("ERRO: GOOGLE_API_KEY não encontrada no arquivo .env.")
    exit()

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("API do Gemini configurada com sucesso.")
except Exception as e:
    print(f"Erro ao configurar a API do Gemini: {e}")
    exit()

# --- META-PROMPT DE TRADUÇÃO (O CÉREBRO DA QUALIDADE) ---
META_PROMPT = """
Você é um tradutor especialista em engenharia de prompts para IAs Generativas, com foco em tradução do Inglês para o Português do Brasil. Sua tarefa é traduzir a lista de prompts a seguir, que são instruções para modelos como GPT-4 e Gemini. A precisão técnica é mais importante que a tradução literal.

**Siga estas regras RIGOROSAMENTE:**
1.  **NÃO traduza placeholders:** Mantenha qualquer texto dentro de colchetes `[]` (como `[product/service]` ou `[target audience]`) exatamente como está no original em inglês. Eles são variáveis que o usuário final irá preencher.
2.  **Preserve a estrutura:** Mantenha a formatação original, incluindo quebras de linha, listas e a estrutura geral do prompt.
3.  **Cuidado com termos técnicos:** Para termos técnicos ou jargões de marketing comuns (ex: 'ROI', 'call-to-action', 'framework', 'A/B testing'), use o termo em português mais comum no mercado brasileiro. Se não houver um bom equivalente, mantenha o termo em inglês ou use o formato 'termo em inglês (equivalente em português)'.
4.  **Tom de voz:** Mantenha o tom de voz direto, imperativo e instrucional do prompt original.
5.  **Formato da Resposta:** Responda APENAS com um objeto JSON contendo uma única chave "translations", que contém uma lista de strings. Cada string na lista deve ser um prompt traduzido, na mesma ordem em que foram recebidos.

Aqui está a lista de prompts para traduzir:
"""

def needs_translation(entry):
    """
    Verifica de forma inteligente se uma entrada precisa ser traduzida ou retraduzida.
    """
    # 1. Verifica se o campo não existe, não é uma lista ou está vazio.
    if "translated_prompts" not in entry or not isinstance(entry["translated_prompts"], list) or not entry["translated_prompts"]:
        return True
    
    # 2. Verifica se a quantidade de originais e traduções é diferente.
    if len(entry.get("original_prompts", [])) != len(entry["translated_prompts"]):
        return True

    # 3. Verifica se alguma das traduções contém uma mensagem de erro.
    for prompt_text in entry["translated_prompts"]:
        # Verificação mais robusta, procurando por substrings de erro.
        if "erro na tradução" in prompt_text.lower() or "tradução pulada" in prompt_text.lower():
            return True # Encontrou um erro, precisa traduzir novamente.
            
    # Se passou por todas as verificações, a tradução está OK.
    return False

def translate_batch(batch_of_prompts):
    """Envia um lote de prompts para a API e retorna as traduções."""
    try:
        formatted_prompts = json.dumps(batch_of_prompts, indent=2, ensure_ascii=False)
        full_prompt_for_api = META_PROMPT + "\n" + formatted_prompts
        
        print("  -> Enviando lote para a API do Gemini...")
        # Adiciona um timeout para evitar que o script fique preso indefinidamente
        response = gemini_model.generate_content(full_prompt_for_api, request_options={'timeout': 120})
        
        cleaned_json_string = response.text.strip().replace('```json', '').replace('```', '')
        translated_data = json.loads(cleaned_json_string)
        
        print("  -> Tradução recebida com sucesso.")
        return translated_data.get("translations", [])
    except Exception as e:
        print(f"  ! ERRO NO LOTE DE TRADUÇÃO: {e}")
        return [f"Erro na tradução: {e}"] * len(batch_of_prompts)

def main():
    if not os.path.exists(DATABASE_FILE):
        print(f"ERRO: Arquivo '{DATABASE_FILE}' não encontrado. Execute o 'consolidate_data.py' primeiro.")
        return

    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    print(f"--- Iniciando tradução inteligente de {len(all_data)} entradas em '{DATABASE_FILE}' ---")

    for i, entry in enumerate(all_data):
        print(f"\nProcessando entrada {i+1}/{len(all_data)}: '{entry['title']}'")
        
        if not needs_translation(entry):
            print("  -> Verificação de qualidade OK. Pulando.")
            continue

        print("  -> Necessita tradução ou retradução. Iniciando processo...")
        if entry.get("original_prompts"):
            translations = translate_batch(entry["original_prompts"])
            
            if len(translations) == len(entry["original_prompts"]):
                entry["translated_prompts"] = translations
                print("  -> Entrada atualizada com sucesso.")
            else:
                print("  -> AVISO: O número de traduções não corresponde ao de originais. Marcando como erro.")
                entry["translated_prompts"] = [f"Erro: contagem de tradução incorreta."] * len(entry["original_prompts"])
            
            # Pausa para não exceder os limites de requisições por minuto da API
            time.sleep(2) 

    # Salva em um novo arquivo para não sobrescrever o original em caso de erro
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n--- Processo Finalizado! ---")
    print(f"O arquivo '{OUTPUT_FILE}' foi criado com todas as traduções verificadas e corrigidas.")

if __name__ == "__main__":
    main()