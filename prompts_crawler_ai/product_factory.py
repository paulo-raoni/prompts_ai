import os
import json
import re
import sys
import time
import html

# --- CONFIGURAÇÕES GERAIS ---
DATABASE_FILE = 'prompts_database_final_PT-BR.json'
OUTPUT_DIR_FULL = 'HTML_Arsenal_Completo'
OUTPUT_DIR_SAMPLE = 'HTML_Amostra_Gratis'
PRODUCT_NAME = "Arsenal Dev AI"
BRAND_NAME = "Brazilian Dev"
ASSETS_DIR = 'assets'
WEBSITE_URL = "https://arsenaldev.ai"

# --- CONTEÚDO ---
DICAS_DE_MESTRE = [
    "Dica de Mestre: Ao usar um prompt, seja o mais específico possível. Em vez de 'crie um texto', diga 'crie um texto de 3 parágrafos em tom persuasivo sobre...'.",
    "Dica de Mestre: A IA é ótima para gerar a primeira versão. Sempre revise e peça a ela mesma para 'agir como um editor sênior e refinar este texto'.",
    "Dica de Mestre: Use a técnica de 'poucos exemplos' (few-shot). Dê à IA 2 ou 3 exemplos do estilo que você quer antes de fazer seu pedido final."
]
PROMOTIONAL_PROMPTS = [
    {"category": "Marketing de Conteúdo", "prompt": "Crie 5 ideias de títulos para um vídeo no YouTube sobre [tópico]. Os títulos devem ser curtos, magnéticos e otimizados para cliques."},
    {"category": "Copywriting (Escrita Persuasiva)", "prompt": "Aja como um copywriter sênior. Escreva um parágrafo persuasivo para um anúncio no Instagram vendendo um [tipo de produto, ex: curso online]. Use a fórmula AIDA."},
    {"category": "Desenvolvimento de Software", "prompt": "Escreva uma função em Python que recebe uma lista de números e retorna apenas os números pares. Adicione comentários explicando o código."}
]
SOCIAL_LINKS = {
    'Instagram': 'https://www.instagram.com/braziliandev_oficial/',
    'TikTok': 'https://www.tiktok.com/@braziliandev_oficial',
    'YouTube': 'https://www.youtube.com/braziliandev'
}

# --- TEMPLATE HTML E CSS ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Fira+Code&display=swap');
        html {{
            scroll-behavior: smooth;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #111827;
            color: #F9FAFB;
            margin: 0;
            padding: 40px;
            line-height: 1.7;
        }}
        .container {{
            max-width: 900px;
            margin: auto;
        }}
        .header {{
            text-align: center;
            border-bottom: 1px solid #374151;
            padding-bottom: 30px;
            margin-bottom: 50px;
        }}
        .header img {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            border: 3px solid #3B82F6;
        }}
        .header h1 {{
            font-size: 42px;
            font-weight: 900;
            margin: 20px 0 5px 0;
            color: #fff;
        }}
        .header h2 {{
            font-size: 22px;
            font-style: italic;
            color: #9CA3AF;
            font-weight: normal;
        }}
        .toc {{
            background-color: #1F2937;
            padding: 20px 30px;
            border-radius: 8px;
            margin-bottom: 50px;
        }}
        .toc h3 {{
            font-size: 24px;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 0;
            column-count: 2;
        }}
        .toc a {{
            text-decoration: none;
            color: #60A5FA;
            font-size: 16px;
        }}
        .toc a:hover {{ text-decoration: underline; }}
        .toc li {{ margin-bottom: 10px; }}
        .prompt-group h3 {{
            font-size: 28px;
            font-weight: 700;
            border-left: 4px solid #3B82F6;
            padding-left: 15px;
            margin-top: 60px;
        }}
        .prompt-card {{
            background-color: #1F2937;
            border: 1px solid #374151;
            border-radius: 8px;
            margin: 25px 0;
            position: relative;
            overflow: hidden;
        }}
        .prompt-card-header {{
             padding: 15px 20px;
             border-bottom: 1px solid #374151;
             display: flex;
             justify-content: space-between;
             align-items: center;
        }}
        .prompt-card-header h4 {{
            font-size: 16px;
            margin: 0;
            color: #E5E7EB;
        }}
        .prompt-card-body {{
            padding: 20px;
        }}
        .prompt-card pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Fira Code', monospace;
            background-color: #111827;
            padding: 15px;
            border-radius: 5px;
            font-size: 14px;
            line-height: 1.6;
            color: #d1d5db;
        }}
        .copy-button {{
            background-color: #374151;
            color: #E5E7EB;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            font-family: 'Inter', sans-serif;
            transition: background-color 0.2s, color 0.2s;
        }}
        .copy-button:hover {{ background-color: #4B5563; }}
        footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #374151;
            font-size: 14px;
            color: #9CA3AF;
        }}
        .cta-section {{
            text-align: center;
            padding: 50px 20px;
            margin-top: 60px;
            background-color: #1F2937;
            border-radius: 8px;
        }}
        .cta-button {{
            display: inline-block;
            background-color: #3B82F6;
            color: #fff;
            padding: 15px 30px;
            font-size: 18px;
            font-weight: bold;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
    <script>
        document.querySelectorAll('.copy-button').forEach(button => {{
            button.addEventListener('click', () => {{
                const pre = button.closest('.prompt-card').querySelector('pre');
                navigator.clipboard.writeText(pre.innerText).then(() => {{
                    button.innerText = 'Copiado!';
                    button.style.backgroundColor = '#10B981';
                    button.style.color = '#fff';
                    setTimeout(() => {{
                        button.innerText = 'Copiar';
                        button.style.backgroundColor = '#374151';
                        button.style.color = '#E5E7EB';
                    }}, 2000);
                }}, (err) => {{
                    console.error('Erro ao copiar: ', err);
                    button.innerText = 'Erro';
                }});
            }});
        }});
    </script>
</body>
</html>
"""

def generate_html_file(html_content, output_filename):
    """Salva o conteúdo HTML em um arquivo .html."""
    try:
        print(f"Gerando arquivo: '{output_filename}'...")
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f" -> SUCESSO: '{output_filename}' gerado.")
    except Exception as e:
        print(f"!!! ERRO ao salvar arquivo HTML: {e}")

def generate_full_packages(data):
    """Gera as páginas HTML completas para cada categoria de produto."""
    if not os.path.exists(OUTPUT_DIR_FULL): os.makedirs(OUTPUT_DIR_FULL)
    
    prompts_by_category = {}
    for entry in data:
        category = entry.get('category', 'Geral')
        if category not in prompts_by_category: prompts_by_category[category] = []
        prompts_by_category[category].append(entry)

    print(f"\n--- Iniciando Geração de {len(prompts_by_category)} Produtos HTML Completos ---")
    for category, entries in prompts_by_category.items():
        content_html = ""
        sanitized_category_name = re.sub(r'[^\w\s-]', '', category).strip().replace(" ", "_")
        filename = os.path.join(OUTPUT_DIR_FULL, f"Arsenal_Dev_{sanitized_category_name}.html")
        
        logo_path = os.path.join(ASSETS_DIR, 'nova_logo.jpg')
        logo_html = f'<img src="file:///{os.path.abspath(logo_path)}">' if os.path.exists(logo_path) else ''
        content_html += f'<div class="header">{logo_html}<h1>{PRODUCT_NAME}</h1><h2>Guia de Prompts: {category}</h2></div>'
        
        content_html += '<div class="toc">'
        content_html += '<h3>Índice</h3><ul>'
        for i, entry in enumerate(entries):
            anchor_id = f"entry-{i}"
            content_html += f'<li><a href="#{anchor_id}">{html.escape(entry["title"])}</a></li>'
        content_html += '</ul></div>'

        for i, entry in enumerate(entries):
            anchor_id = f"entry-{i}"
            content_html += f'<div class="prompt-group" id="{anchor_id}"><h3>{html.escape(entry["title"])}</h3>'
            
            # CORREÇÃO DEFINITIVA: Lendo da chave "translated_prompts"
            prompts = entry.get("translated_prompts", [])
            if not prompts:
                content_html += "<p><i>(Nenhum prompt encontrado para esta seção. Verifique o arquivo JSON de entrada.)</i></p>"
            else:
                for j, prompt_text in enumerate(prompts, 1):
                    safe_prompt_text = html.escape(prompt_text)
                    content_html += f'<div class="prompt-card"><div class="prompt-card-header"><h4>Prompt {j}</h4><button class="copy-button">Copiar</button></div><div class="prompt-card-body"><pre>{safe_prompt_text}</pre></div></div>'
            content_html += '</div>'
        
        content_html += f'<footer><p>© {time.strftime("%Y")} {BRAND_NAME}. Todos os direitos reservados.</p></footer>'
        final_html = HTML_TEMPLATE.format(title=f"{PRODUCT_NAME} - {category}", content=content_html)
        
        generate_html_file(final_html, filename)

def generate_free_sample_html():
    """Gera a página HTML completa para a amostra grátis."""
    if not os.path.exists(OUTPUT_DIR_SAMPLE): os.makedirs(OUTPUT_DIR_SAMPLE)
    
    filename = os.path.join(OUTPUT_DIR_SAMPLE, "Amostra_Gratis_Arsenal_Dev_AI.html")
    content_html = ""

    logo_path = os.path.join(ASSETS_DIR, 'nova_logo.jpg')
    logo_html = f'<img src="file:///{os.path.abspath(logo_path)}">' if os.path.exists(logo_path) else ''
    content_html += f'<div class="header">{logo_html}<h1>{PRODUCT_NAME}</h1><h2>Amostra Grátis de Prompts de Elite</h2></div>'
    content_html += "<p style='text-align:center; color: #9CA3AF; max-width: 600px; margin: auto; margin-bottom: 40px;'>Uma pequena demonstração do poder que você terá em mãos com o Arsenal Dev AI completo.</p>"
    
    for item in PROMOTIONAL_PROMPTS:
        safe_prompt_text = html.escape(item["prompt"])
        content_html += f'<div class="prompt-group"><h3>Categoria: {item["category"]}</h3>'
        content_html += f'<div class="prompt-card"><div class="prompt-card-header"><h4>Exemplo de Prompt</h4><button class="copy-button">Copiar</button></div><div class="prompt-card-body"><pre>{safe_prompt_text}</pre></div></div>'
    
    content_html += '<div class="cta-section">'
    content_html += '<h3>Gostou? Desbloqueie o Arsenal Completo.</h3>'
    content_html += '<p>Esta amostra é apenas o começo. Centenas de prompts avançados te esperam.</p>'
    content_html += f'<a href="{WEBSITE_URL}" class="cta-button">ADQUIRA O ARSENAL DEV AI AGORA!</a>'
    content_html += '</div>'
    
    content_html += f'<footer><p>© {time.strftime("%Y")} {BRAND_NAME}. Todos os direitos reservados.</p></footer>'
    final_html = HTML_TEMPLATE.format(title="Amostra Grátis - Arsenal Dev AI", content=content_html)
    
    generate_html_file(final_html, filename)

def main():
    if not os.path.exists(DATABASE_FILE):
        print(f"ERRO: Arquivo de banco de dados '{DATABASE_FILE}' não encontrado.")
        return
    
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    generate_full_packages(all_data)
    generate_free_sample_html()
    
    print("\n--- Geração de Produtos HTML Concluída ---")

if __name__ == "__main__":
    main()