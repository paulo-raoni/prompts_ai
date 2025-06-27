import os
import json
import re

# O diretório onde o crawler.py salva os dados brutos
INPUT_DIR = 'BlackMagic_Prompts_Raw' 
# O arquivo de saída que servirá de entrada para o tradutor
OUTPUT_FILE = 'prompts_database.json'

def main():
    """
    Lê os arquivos .txt gerados pelo crawler e os consolida em um único JSON.
    """
    if not os.path.exists(INPUT_DIR):
        print(f"ERRO: O diretório de entrada '{INPUT_DIR}' não foi encontrado.")
        print("Certifique-se de que o script 'crawler.py' foi executado primeiro.")
        return

    all_data = []
    print(f"--- Iniciando Consolidação de '{INPUT_DIR}' ---")

    # Percorre a estrutura de pastas: Categoria -> Título -> arquivo.txt
    for category_name in os.listdir(INPUT_DIR):
        category_path = os.path.join(INPUT_DIR, category_name)
        if os.path.isdir(category_path):
            for entry_name in os.listdir(category_path):
                entry_path = os.path.join(category_path, entry_name)
                if os.path.isdir(entry_path):
                    txt_file_name = f"{entry_name}.txt"
                    txt_file_path = os.path.join(entry_path, txt_file_name)

                    if os.path.exists(txt_file_path):
                        print(f"Processando: {txt_file_path}")
                        with open(txt_file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        metadata = {}
                        prompts_content = ""
                        # Extrai metadados e o bloco de prompts
                        for line in lines:
                            if line.startswith("URL:"):
                                metadata['source_url'] = line.split(":", 1)[1].strip()
                            elif line.startswith("CATEGORIA_ORIGINAL:"):
                                metadata['category'] = line.split(":", 1)[1].strip()
                            elif line.startswith("TITULO_ORIGINAL:"):
                                metadata['title'] = line.split(":", 1)[1].strip()
                            elif "---" not in line:
                                prompts_content += line
                        
                        # Separa os múltiplos prompts dentro do arquivo
                        original_prompts = [p.strip() for p in prompts_content.split('---') if p.strip()]

                        entry_data = {
                            "category": metadata.get('category', category_name.replace('_', ' ')),
                            "title": metadata.get('title', entry_name.replace('_', ' ')),
                            "original_prompts": original_prompts,
                            "source_url": metadata.get('source_url', '')
                        }
                        all_data.append(entry_data)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nSUCESSO: {len(all_data)} entradas consolidadas em '{OUTPUT_FILE}'.")

if __name__ == '__main__':
    main()