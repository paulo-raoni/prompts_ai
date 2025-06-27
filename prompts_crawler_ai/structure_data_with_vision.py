import os
import json
import asyncio
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAÇÕES ---
load_dotenv()
INPUT_DIR = 'BlackMagic_Prompts_Raw' 
OUTPUT_FILE = 'prompts_database_structured.json'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
CONCURRENCY_LIMIT = 5
DEMO_PROCESSING_LIMIT = 20 # Limite para o modo demo

gemini_model = None

# --- META-PROMPT PARA ESTRUTURAÇÃO COM VISÃO E HTML ---
META_PROMPT_FOR_STRUCTURING = """
Você é um analista de conteúdo web sênior. Sua tarefa é analisar um conjunto de três ficheiros de uma página web (uma imagem, o seu texto bruto, e o seu código-fonte HTML) para criar um JSON estruturado que represente a ordem e a hierarquia do conteúdo.

**Diretrizes:**
1.  **Analise as Três Fontes:**
    * **Imagem (`.png`):** Use para entender o layout visual, a importância e a ordem dos elementos.
    * **Código HTML (`.html`):** Use como a principal fonte de verdade para a estrutura semântica (tags `<h1>`, `<h2>`, `<p>`, `<code>`).
    * **Texto Bruto (`.txt`):** Use como referência para o conteúdo textual a ser incluído.
2.  **Estruture a Saída:** Crie um array de objetos JSON chamado "content_structure". Cada objeto deve ter duas chaves: "type" e "content". Ignore qualquer texto que seja claramente parte da navegação do site (menus, rodapés, barras laterais). Foque-se no conteúdo principal.
3.  **Refine a Categoria:** A categoria original extraída pelo crawler é uma sugestão. Baseado na sua análise completa do conteúdo, refine esta categoria para ser mais específica e descritiva. Por exemplo, se a categoria original for "Advanced_Prompts" e o conteúdo for sobre SEO, a categoria refinada deve ser "Prompts Avançados para SEO".
4.  **Tipos de Conteúdo Permitidos:**
    * `paragraph`: Para textos introdutórios, explicações ou notas.
    * `subheading`: Para títulos de seção dentro da página.
    * `prompt`: Para os blocos de código ou os prompts em si.

**Exemplo de Saída JSON Esperada:**
```json
{
  "category": "Prompts Avançados para SEO",
  "main_title": "Advanced SEO Prompts",
  "source_url": "[http://example.com/page](http://example.com/page)",
  "content_structure": [
    {
      "type": "paragraph",
      "content": "Here are some advanced prompts to help you with your SEO strategy."
    },
    {
      "type": "subheading",
      "content": "Keyword Research"
    },
    {
      "type": "prompt",
      "content": "Generate 10 long-tail keywords for the topic [your topic]."
    }
  ]
}
```

Analise os três ficheiros a seguir e gere APENAS o JSON estruturado.
"""

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

async def structure_content_task(semaphore, entry_path, entry_name):
    """Função assíncrona que processa uma única entrada (pasta)."""
    async with semaphore:
        print(f"Processando: {entry_name}")
        txt_file_path = os.path.join(entry_path, f"{entry_name}.txt")
        png_file_path = os.path.join(entry_path, f"{entry_name}.png")
        html_file_path = os.path.join(entry_path, f"{entry_name}.html")

        if not (os.path.exists(txt_file_path) and os.path.exists(png_file_path) and os.path.exists(html_file_path)):
            return None

        with open(txt_file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        with open(html_file_path, 'r', encoding='utf-8') as f:
            raw_html = f.read()
        
        try:
            img = Image.open(png_file_path)
            
            print(f"   -> Enviando para análise: {entry_name}")
            response = await gemini_model.generate_content_async([
                META_PROMPT_FOR_STRUCTURING, 
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
    """Função principal assíncrona para orquestrar as tarefas."""
    is_demo_mode = '--demo' in sys.argv
    
    if not setup_gemini():
        return

    if not os.path.exists(INPUT_DIR):
        print(f"ERRO: O diretório de entrada '{INPUT_DIR}' não foi encontrado.")
        return

    all_entries = []
    # Recolhe todas as entradas válidas primeiro
    for category_name in os.listdir(INPUT_DIR):
        category_path = os.path.join(INPUT_DIR, category_name)
        if os.path.isdir(category_path):
            for entry_name in os.listdir(category_path):
                entry_path = os.path.join(category_path, entry_name)
                # Garante que é uma pasta de conteúdo e não um ficheiro aleatório
                if os.path.isdir(entry_path):
                    all_entries.append((entry_path, entry_name))

    # Aplica o limite se estiver em modo demo
    if is_demo_mode:
        print(f"--- MODO DEMO: Processando as primeiras {DEMO_PROCESSING_LIMIT} entradas de {len(all_entries)} encontradas. ---")
        entries_to_process = all_entries[:DEMO_PROCESSING_LIMIT]
    else:
        entries_to_process = all_entries

    tasks = []
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    print(f"\n--- Iniciando Estruturação Paralela de {len(entries_to_process)} entradas ---")

    # Prepara as tarefas para as entradas selecionadas
    for entry_path, entry_name in entries_to_process:
        tasks.append(structure_content_task(semaphore, entry_path, entry_name))

    # Executa as tarefas em paralelo
    results = await asyncio.gather(*tasks)
    
    # Filtra os resultados que falharam (None)
    all_structured_data = [res for res in results if res is not None]
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_structured_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSUCESSO: {len(all_structured_data)} de {len(entries_to_process)} entradas estruturadas e salvas em '{OUTPUT_FILE}'.")

if __name__ == '__main__':
    asyncio.run(main())
