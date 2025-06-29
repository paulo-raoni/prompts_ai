import json
import os
import subprocess
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

# --- CONFIGURAÇÕES ---
ADMIN_PANEL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ADMIN_PANEL_DIR)

# Inicializa a aplicação Flask
app = Flask(__name__, template_folder='templates')
app.secret_key = 'uma-chave-secreta-muito-segura'

# --- CONFIGURAÇÃO DE CAMINHOS NO FLASK (A FORMA CORRIGIDA) ---
# Armazenamos os caminhos na configuração da própria aplicação para evitar erros de escopo.
app.config['DATABASE_FILE'] = os.path.join(PROJECT_ROOT, 'output', 'prompts_database_final.json')
app.config['GENERATOR_SCRIPT'] = os.path.join(PROJECT_ROOT, 'src', 'generation', 'product_factory.py')
app.config['GENERATED_SITE_DIR'] = os.path.join(PROJECT_ROOT, 'output', 'HTML_Arsenal_Completo')


# --- FUNÇÕES AUXILIARES ---
def load_prompts():
    """Carrega os prompts da base de dados JSON."""
    db_file = app.config['DATABASE_FILE']
    if not os.path.exists(db_file):
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        return []
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []

def save_prompts(prompts):
    """Guarda os prompts na base de dados JSON."""
    db_file = app.config['DATABASE_FILE']
    try:
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Erro ao guardar a base de dados: {e}")

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def index():
    prompts = load_prompts()
    prompts_with_id = [dict(p, id=i) for i, p in enumerate(prompts)]
    return render_template('admin_index.html', prompts=prompts_with_id)

@app.route('/add', methods=['GET', 'POST'])
def add_prompt():
    if request.method == 'POST':
        prompts = load_prompts()
        try:
            content_structure = json.loads(request.form['content_structure'])
        except json.JSONDecodeError:
            flash('Erro: A estrutura de conteúdo não é um JSON válido.', 'error')
            return redirect(url_for('add_prompt'))
        new_prompt = {
            "section": request.form['section'], "category": "Geral", "emoji": request.form['emoji'],
            "main_title": request.form['main_title'], "source_url": request.form['source_url'],
            "content_structure": content_structure
        }
        prompts.append(new_prompt)
        save_prompts(prompts)
        flash('Prompt adicionado com sucesso! Agora pode regenerar o site.', 'success')
        return redirect(url_for('index'))
    return render_template('admin_form.html', action="Adicionar", prompt={})

@app.route('/edit/<int:prompt_id>', methods=['GET', 'POST'])
def edit_prompt(prompt_id):
    prompts = load_prompts()
    if prompt_id >= len(prompts):
        flash('Erro: ID do prompt inválido.', 'error')
        return redirect(url_for('index'))
    prompt_to_edit = prompts[prompt_id]
    if request.method == 'POST':
        try:
            content_structure = json.loads(request.form['content_structure'])
        except json.JSONDecodeError:
            flash('Erro: A estrutura de conteúdo não é um JSON válido.', 'error')
            prompt_to_edit.update(request.form.to_dict())
            prompt_to_edit['content_structure_str'] = request.form['content_structure']
            return render_template('admin_form.html', action="Editar", prompt=prompt_to_edit, prompt_id=prompt_id)
        prompts[prompt_id].update({
            "main_title": request.form['main_title'], "section": request.form['section'],
            "emoji": request.form['emoji'], "source_url": request.form['source_url'],
            "content_structure": content_structure
        })
        save_prompts(prompts)
        flash('Prompt atualizado com sucesso! Agora pode regenerar o site.', 'success')
        return redirect(url_for('index'))
    prompt_to_edit['content_structure_str'] = json.dumps(prompt_to_edit.get('content_structure', []), indent=2, ensure_ascii=False)
    return render_template('admin_form.html', action="Editar", prompt=prompt_to_edit, prompt_id=prompt_id)

@app.route('/delete/<int:prompt_id>', methods=['POST'])
def delete_prompt(prompt_id):
    prompts = load_prompts()
    if prompt_id < len(prompts):
        prompts.pop(prompt_id)
        save_prompts(prompts)
        flash('Prompt apagado com sucesso! Agora pode regenerar o site.', 'success')
    else:
        flash('Erro: ID do prompt inválido.', 'error')
    return redirect(url_for('index'))

@app.route('/regenerate', methods=['POST'])
def regenerate_site():
    generator_script = app.config['GENERATOR_SCRIPT']
    if not os.path.exists(generator_script):
        flash(f"Erro: Script de geração não encontrado em '{generator_script}'", "error")
        return redirect(url_for('index'))
    try:
        result = subprocess.run(
            [sys.executable, generator_script], check=True, capture_output=True, text=True, encoding='utf-8'
        )
        flash("Site regenerado com sucesso!", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Erro ao regenerar o site. Detalhes: {e.stderr}", "error")
    except Exception as e:
        flash(f"Ocorreu um erro inesperado: {e}", "error")
    return redirect(url_for('index'))


@app.route('/site/')
@app.route('/site/<path:path>')
def serve_site(path='index.html'):
    """Serve os ficheiros do site gerado a partir da pasta output."""
    generated_site_dir = app.config['GENERATED_SITE_DIR'] # Acede ao caminho a partir da config
    if not os.path.exists(generated_site_dir):
        flash("O diretório do site ainda não existe. Por favor, clique em 'Regenerar Site' primeiro.", "error")
        return redirect(url_for('index'))
    return send_from_directory(generated_site_dir, path)


if __name__ == '__main__':
    app.run(debug=True, port=5001)