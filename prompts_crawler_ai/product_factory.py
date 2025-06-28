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
        # Usamos html.escape para segurança, para evitar injeção de HTML.
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
        
        # Gera um nome de arquivo seguro e único
        s_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
        url_hash = hashlib.md5(entry.get("source_url", title).encode()).hexdigest()[:6]
        filename = f"{s_title}_{url_hash}.html"
        filepath = os.path.join(OUTPUT_DIR_FULL, filename)

        main_content_html = render_content_structure(entry.get("content_structure", []))
        
        # Preenche o template de conteúdo
        processed_html = template_html.replace('{page_title}', f"{title} - {PRODUCT_NAME}")
        processed_html = processed_html.replace('{main_title}', title)
        processed_html = processed_html.replace('{main_content}', main_content_html)
        processed_html = processed_html.replace('{year}', time.strftime("%Y"))
        processed_html = processed_html.replace('{brand_name}', BRAND_NAME)
        
        generate_html_file(processed_html, filepath)
    
    print("--- Geração das páginas de conteúdo concluída. ---")

def generate_index_page(data, template_html):
    """Gera a página principal 'index.html' com o novo layout de seções e categorias."""
    print("\n--- Gerando Página de Índice Principal (Novo Layout Estruturado) ---")
    
    # --- LÓGICA DE AGRUPAMENTO ATUALIZADA ---
    sections = {}
    for entry in data:
        section_name = entry.get('section', 'Outros')
        category_name = entry.get('category', 'Geral')
        emoji = entry.get('emoji', '✨')
        
        if section_name not in sections:
            sections[section_name] = {}
        
        if category_name not in sections[section_name]:
            sections[section_name][category_name] = {
                "emoji": emoji,
                "prompts": []
            }
        
        title = entry.get('main_title', 'Guia Sem Título')
        s_title = re.sub(r'[^\w\s-]', '', title).strip().replace(" ", "_")
        url_hash = hashlib.md5(entry.get("source_url", title).encode()).hexdigest()[:6]
        filename = f"{s_title}_{url_hash}.html"
        
        sections[section_name][category_name]["prompts"].append({
            "title": title, 
            "url": filename,
            "content": " ".join([block.get("content", "") for block in entry.get("content_structure", [])])
        })

    # --- LÓGICA DE RENDERIZAÇÃO DE HTML ATUALIZADA ---
    guide_list_html = ""
    search_index = []

    # Ordena as seções para uma apresentação consistente
    for section_name, categories in sorted(sections.items()):
        guide_list_html += f'<div class="category-section mb-12">'
        guide_list_html += f'<h2 class="text-3xl font-bold mb-6 border-l-4 border-blue-500 pl-4">{section_name}</h2>'
        
        # Cria um grid para os cards de categoria
        guide_list_html += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
        
        # Ordena as categorias dentro da seção
        for category_name, details in sorted(categories.items()):
            emoji = details["emoji"]
            # Por enquanto, o card da categoria é visual. O link poderia levar a uma futura página de categoria.
            guide_list_html += f'''
            <div class="guide-card flex items-center bg-gray-800 p-6 rounded-xl border border-gray-700 transition-all duration-200">
                <span class="text-3xl mr-4">{emoji}</span>
                <span class="font-semibold">{category_name}</span>
            </div>
            '''
            
            # Adiciona os prompts individuais ao índice de busca
            for prompt in details["prompts"]:
                search_index.append({
                    "title": prompt["title"], 
                    "category": category_name, 
                    "section": section_name,
                    "url": prompt["url"], 
                    "content": prompt["content"].lower()
                })

        guide_list_html += '</div></div>'

    # Injeta os dados do índice de busca no JavaScript do template
    js_data_line = f"const searchIndex = {json.dumps(search_index, ensure_ascii=False)};"

    final_html = template_html.replace('{product_name}', PRODUCT_NAME)
    final_html = final_html.replace('{guide_list}', guide_list_html)
    final_html = final_html.replace('{year}', time.strftime("%Y"))
    final_html = final_html.replace('{brand_name}', BRAND_NAME)
    final_html = final_html.replace('// SEARCH_INDEX_PLACEHOLDER', js_data_line)

    generate_html_file(final_html, os.path.join(OUTPUT_DIR_FULL, "index.html"))
    print("--- Geração da Página de Índice Principal concluída. ---")

def main():
    """Função principal que orquestra a geração dos arquivos HTML."""
    index_template = load_template(INDEX_TEMPLATE_FILE)
    content_template = load_template(CONTENT_TEMPLATE_FILE)
    if not index_template or not content_template: return

    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERRO ao ler a base de dados '{DATABASE_FILE}': {e}")
        return

    generate_index_page(all_data, index_template)
    generate_content_pages(all_data, content_template)
    
    print("\n\n--- Processo de Geração de Produto Finalizado com Sucesso! ---")
    print(f"Os arquivos HTML foram gerados no diretório: '{OUTPUT_DIR_FULL}'")

if __name__ == "__main__":
    main()