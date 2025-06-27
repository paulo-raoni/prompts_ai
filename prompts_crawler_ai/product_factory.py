import os
import json
import re
import time
import hashlib
import html

# --- CONFIGURAÇÕES GERAIS ---
DATABASE_FILE = 'prompts_database_final.json'
OUTPUT_DIR_FULL = 'HTML_Arsenal_Completo'
INDEX_TEMPLATE_FILE = 'index_template.html'
CONTENT_TEMPLATE_FILE = 'content_template.html'

# --- CONTEÚDO DO PRODUTO ---
PRODUCT_NAME = "Arsenal Dev AI"
BRAND_NAME = "Brazilian Dev"

def load_template(filename):
    """Carrega um ficheiro de template."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERRO FATAL: Ficheiro de template '{filename}' não encontrado.")
        return None

def generate_html_file(html_content, output_filename):
    """Salva conteúdo HTML num ficheiro."""
    try:
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        print(f"!!! ERRO ao salvar o ficheiro '{output_filename}': {e}")

def render_content_structure(structure):
    """Renderiza a estrutura de conteúdo em HTML."""
    content_html = ""
    for block in structure:
        block_type = block.get("type", "paragraph")
        block_content = html.escape(block.get("content", ""))
        if not block_content: continue

        if block_type == "subheading":
            anchor_id = re.sub(r'[^\w-]', '', block_content.lower().replace(' ', '-'))[:50]
            content_html += f'<h3 id="{anchor_id}" class="text-2xl font-bold mt-12 mb-4 border-l-4 border-blue-500 pl-4">{block_content}</h3>'
        elif block_type == "paragraph":
            content_html += f'<p class="text-gray-300 text-lg mb-4">{block_content}</p>'
        elif block_type == "prompt":
            content_html += f'''
                <div class="bg-gray-800 rounded-xl border border-gray-700 my-6">
                    <div class="px-6 py-4 border-b border-gray-700 text-gray-300 font-semibold flex justify-between items-center">
                        <span>Prompt de Comando</span>
                        <button class="copy-button bg-gray-700 hover:bg-gray-600 text-white font-bold py-1 px-3 rounded-lg text-sm transition-all">Copiar</button>
                    </div>
                    <div class="p-6">
                        <pre class="whitespace-pre-wrap font-mono text-gray-200"><code>{block_content}</code></pre>
                    </div>
                </div>'''
    return content_html

def generate_content_pages(data, template_html):
    """Gera todas as páginas de conteúdo com o novo estilo escuro."""
    print(f"\n--- Gerando {len(data)} Páginas de Conteúdo (Tema Escuro) ---")
    
    for entry in data:
        title = entry.get('main_title', 'Guia Sem Título')
        
        s_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
        url_hash = hashlib.md5(entry.get("source_url", title).encode()).hexdigest()[:6]
        filename = f"{s_title}_{url_hash}.html"
        filepath = os.path.join(OUTPUT_DIR_FULL, filename)

        main_content_html = render_content_structure(entry.get("content_structure", []))
        
        processed_html = template_html.replace('{page_title}', f"{title} - {PRODUCT_NAME}")
        processed_html = processed_html.replace('{main_title}', title)
        processed_html = processed_html.replace('{main_content}', main_content_html)
        processed_html = processed_html.replace('{year}', time.strftime("%Y"))
        processed_html = processed_html.replace('{brand_name}', BRAND_NAME)
        
        generate_html_file(processed_html, filepath)
    
    print("--- Geração das páginas de conteúdo concluída. ---")

def generate_index_page(data, template_html):
    """Gera a página principal 'index.html' com o novo layout de cards."""
    print("\n--- Gerando Página de Índice Principal (Novo Layout) ---")
    
    guides_by_category = {}
    for entry in data:
        category = entry.get('category', 'Geral')
        if category not in guides_by_category:
            guides_by_category[category] = {"guides": [], "emoji": entry.get("emoji", "✨")}
        
        title = entry.get('main_title', 'Guia Sem Título')
        s_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
        url_hash = hashlib.md5(entry.get("source_url", title).encode()).hexdigest()[:6]
        filename = f"{s_title}_{url_hash}.html"
        guides_by_category[category]["guides"].append({"title": title, "url": filename})

    guide_list_html = ""
    for category, details in sorted(guides_by_category.items()):
        guide_list_html += f'<div class="category-section mb-12">'
        guide_list_html += f'<h2 class="text-3xl font-bold mb-6 flex items-center gap-4"><span class="text-4xl">{details["emoji"]}</span> {category}</h2>'
        guide_list_html += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
        for guide in details["guides"]:
            guide_list_html += f'<a href="{guide["url"]}" class="guide-card block bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-blue-500 hover:bg-gray-700 transition-all duration-200 transform hover:-translate-y-1"><span>{guide["title"]}</span></a>'
        guide_list_html += '</div></div>'
    
    search_index = []
    for category, details in guides_by_category.items():
        for guide in details["guides"]:
            content = " ".join([d.get("content", "") for d in data if d.get("main_title") == guide["title"]])
            search_index.append({"title": guide["title"], "category": category, "url": guide["url"], "content": content})

    js_data_line = f"const searchIndex = {json.dumps(search_index, ensure_ascii=False)};"

    final_html = template_html.replace('{product_name}', PRODUCT_NAME)
    final_html = final_html.replace('{guide_list}', guide_list_html)
    final_html = final_html.replace('{year}', time.strftime("%Y"))
    final_html = final_html.replace('{brand_name}', BRAND_NAME)
    final_html = final_html.replace('// SEARCH_INDEX_PLACEHOLDER', js_data_line)

    generate_html_file(final_html, os.path.join(OUTPUT_DIR_FULL, "index.html"))
    print("--- Geração da Página de Índice Principal concluída. ---")

def main():
    index_template = load_template(INDEX_TEMPLATE_FILE)
    content_template = load_template(CONTENT_TEMPLATE_FILE)
    if not index_template or not content_template: return

    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except Exception as e:
        print(f"ERRO ao ler a base de dados '{DATABASE_FILE}': {e}")
        return

    generate_index_page(all_data, index_template)
    generate_content_pages(all_data, content_template)
    
    print("\n--- Geração de Produtos HTML Concluída ---")

if __name__ == "__main__":
    main()
