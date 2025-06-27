import os
import subprocess
import sys

# --- CONFIGURAÇÃO DO PIPELINE ---
# Esta é a ordem de execução final e definitiva do nosso projeto.
PIPELINE_SCRIPTS = [
    'crawler.py',
    'consolidate_data.py',
    'translate_database.py',
    'pdf_factory.py'
]

def run_script(script_name):
    """
    Função aprimorada para executar um script Python, mostrando sua saída em tempo real.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    print(f"\n{'='*25}\n EXECUTANDO: {script_name}\n{'='*25}")
    try:
        # Modificado: removemos a captura de output.
        # A saída do script filho será mostrada diretamente no seu terminal.
        # Isso resolve os problemas de encoding e melhora o feedback.
        subprocess.run(
            [sys.executable, script_name], # sys.executable garante que estamos usando o mesmo interpretador Python
            check=True, # Garante que um erro no script irá lançar uma exceção
            encoding='utf-8' # Ajuda a padronizar a codificação entre os processos
        )
        print(f"--- SUCESSO: '{script_name}' concluído sem erros. ---")
        return True
    except FileNotFoundError:
        print(f"!!! ERRO FATAL: O script '{script_name}' não foi encontrado.")
        print("!!! Verifique se o nome do arquivo está correto e no mesmo diretório.")
        return False
    except subprocess.CalledProcessError as e:
        # Se o script retornar um código de erro (ou seja, quebrar), esta exceção é lançada.
        print(f"!!! ERRO FATAL ao executar '{script_name}' !!!")
        print("!!! O pipeline foi interrompido.")
        # stderr não é mais capturado diretamente, mas o erro do processo filho será exibido
        return False

def main():
    """
    Orquestra a execução de todo o pipeline de geração de PDFs.
    """
    print(">>> INICIANDO O PIPELINE DE GERAÇÃO 'ARSENAL DEV AI' <<<")
    
    # Executa cada script na ordem definida.
    # Se qualquer um deles falhar, o orquestrador para.
    for script in PIPELINE_SCRIPTS:
        if not run_script(script):
            print("\n>>> O PIPELINE FOI INTERROMPIDO DEVIDO A UM ERRO. <<<")
            break
    else: # Este 'else' pertence ao 'for'. Ele só executa se o loop terminar SEM um 'break'.
        print("\n\n>>> PIPELINE COMPLETO EXECUTADO COM SUCESSO! <<<")
        print("Verifique as pastas 'PDF_Arsenal_Completo' e 'PDF_Amostra_Gratis' pelos seus arquivos.")

if __name__ == '__main__':
    main()