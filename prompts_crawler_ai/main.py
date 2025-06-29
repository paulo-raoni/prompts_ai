import subprocess
import sys
import time

# --- CONFIGURAÇÃO DO PIPELINE ---
PIPELINE_SCRIPTS = [
    'src/crawling/crawler.py',
    'src/processing/structure_data_with_vision.py',
    'src/processing/translate_database.py',
    'src/generation/product_factory.py'
]

def run_script(script_name, is_demo_mode):
    """
    Executa um script Python, passando o modo de execução (demo ou completo).
    """
    mode_text = '(Modo DEMO)' if is_demo_mode else '(Modo COMPLETO)'
    print(f"\n{'='*25}\n-> EXECUTANDO: {script_name} {mode_text}\n{'='*25}")
    try:
        # Constrói o comando a ser executado
        command = [sys.executable, script_name]
        # Adiciona o argumento --demo se estiver no modo de demonstração
        if is_demo_mode:
            command.append('--demo')

        subprocess.run(
            command,
            check=True, # Garante que um erro no script irá parar o pipeline
            encoding='utf-8'
        )
        print(f"--- SUCESSO: '{script_name}' concluído sem erros. ---")
        return True
    except Exception as e:
        print(f"!!! ERRO FATAL ao executar '{script_name}': {e} !!!")
        print("!!! O pipeline foi interrompido.")
        return False

def main():
    """
    Orquestra a execução de todo o pipeline.
    Execute com 'python main.py --demo' para um teste rápido com 20 páginas.
    Execute com 'python main.py' para o processo completo.
    """
    # Verifica se o modo demo foi ativado através dos argumentos da linha de comando
    is_demo_mode = '--demo' in sys.argv

    if is_demo_mode:
        print(">>> INICIANDO O PIPELINE EM MODO DEMO (LIMITE DE 20 PÁGINAS) <<<")
    else:
        print(">>> INICIANDO O PIPELINE COMPLETO <<<")
    
    start_time = time.time()

    # Executa cada script na ordem, passando o modo de execução
    for script in PIPELINE_SCRIPTS:
        if not run_script(script, is_demo_mode):
            break
    else: # Este 'else' pertence ao 'for'
        end_time = time.time()
        total_time = end_time - start_time
        print("\n\n>>> PIPELINE EXECUTADO COM SUCESSO! <<<")
        print(f"Tempo total de execução: {total_time:.2f} segundos.")

if __name__ == '__main__':
    main()
