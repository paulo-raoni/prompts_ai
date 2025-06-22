import os
import json
import re

# --- CONFIGURAÇÕES ---
# O nome da pasta onde o crawler salvou os arquivos .txt
INPUT_DIRECTORY = 'BlackMagic_Prompts'
# O nome do arquivo final que queremos criar
OUTPUT_FILE = 'prompts_database.json'

def parse_prompt_file(file_content):
    """
    Extrai todas as informações de um único arquivo .txt.
    Retorna um dicionário com os dados ou None se o formato for inválido.
    """
    try:
        # Extrai os metadados do cabeçalho
        title = re.search(r"TEMA: (.*)", file_content).group(1).strip()
        category = re.search(r"CATEGORIA: (.*)", file_content).group(1).strip()
        source_url = re.search(r"FONTE: (.*)", file_content).group(1).strip()

        # Listas para armazenar os prompts extraídos
        original_prompts = []
        translated_prompts = []

        # Divide o arquivo em blocos de "PROMPT" usando regex como delimitador
        # Isso é mais robusto do que um simples split.
        prompt_blocks = re.split(r"--- PROMPT \d+ ---", file_content)[1:]

        for block in prompt_blocks:
            # Extrai o prompt original
            original_match = re.search(r"ORIGINAL \(ENGLISH\):\s*```\s*(.*?)\s*```", block, re.DOTALL)
            # Extrai o prompt traduzido
            translated_match = re.search(r"TRADUÇÃO \(PORTUGUÊS\):\s*```\s*(.*?)\s*```", block, re.DOTALL)

            if original_match and translated_match:
                original_prompts.append(original_match.group(1).strip())
                translated_prompts.append(translated_match.group(1).strip())

        # Monta o objeto final para este arquivo
        entry_data = {
            "category": category,
            "title": title,
            "original_prompts": original_prompts,
            "translated_prompts": translated_prompts,
            "source_url": source_url
        }
        return entry_data

    except AttributeError:
        # Ocorre se o regex não encontrar um dos campos (TEMA, CATEGORIA, etc.)
        print(f"  -> AVISO: Formato inválido ou incompleto. Pulando este arquivo.")
        return None
    except Exception as e:
        print(f"  -> ERRO inesperado ao processar o arquivo: {e}")
        return None

def main():
    """
    Função principal que varre o diretório e cria o arquivo JSON.
    """
    if not os.path.exists(INPUT_DIRECTORY):
        print(f"ERRO: O diretório de entrada '{INPUT_DIRECTORY}' não foi encontrado.")
        print("Certifique-se de que o script está na mesma pasta que o diretório gerado pelo crawler.")
        return

    all_data = []
    print(f"--- Iniciando a consolidação do diretório '{INPUT_DIRECTORY}' ---")

    # Varre a árvore de diretórios
    for root, dirs, files in os.walk(INPUT_DIRECTORY):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                print(f"Processando arquivo: {file_path}")

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                parsed_data = parse_prompt_file(content)
                if parsed_data:
                    all_data.append(parsed_data)

    # Escreve a lista completa de dados no arquivo JSON de saída
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # indent=4 cria um arquivo JSON "bonito" e legível
        json.dump(all_data, f, ensure_ascii=False, indent=4)

    print("\n--- Consolidação Concluída! ---")
    print(f"SUCESSO: {len(all_data)} entradas foram processadas e salvas em '{OUTPUT_FILE}'.")

# Garante que o script só será executado quando chamado diretamente
if __name__ == "__main__":
    main()