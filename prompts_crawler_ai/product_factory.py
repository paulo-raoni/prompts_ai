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
SECTION_TEMPLATE_FILE = 'category_template.html' 

# --- CONTEÚDO DO PRODUTO ---
PRODUCT_NAME = "Arsenal Dev AI"
BRAND_NAME = "Brazilian Dev"

def load_template(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERRO FATAL: Ficheiro de template '{filename}' não encontrado.")
        return None

def generate_html_file(html_content, output_filename):
    try:
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        print(f"!!! ERRO ao salvar o ficheiro '{output_filename}': {e}")

def get_safe_filename(name):
    return re.sub(r'[^\w\s-]', '', name).strip().replace(" ", "_")

def restructure_and_group_data(data):
    """Lê os dados brutos e os reestrutura na hierarquia correta."""
    print("-> Reestruturando dados e identificando subcategorias...")
    sections = {}
    for entry in data:
        content_structure = entry.get("content_structure", [])
        sub_category = "Geral"
        if content_structure and content_structure[0].get("type") == "subheading":
            sub_category = content_structure[0].get("content", "Geral")

        section_name = entry.get('section', 'Outros')
        emoji = entry.get('emoji', '✨')
        
        if section_name not in sections:
            sections[section_name] = {}

        if sub_category not in sections[section_name]:
            sections[section_name][sub_category] = {
                "emoji": emoji,
                "prompts": []
            }
        
        main_title_clean = entry.get('main_title', 'Guia Sem Título').split(' - ')[0]
        
        s_title = get_safe_filename(main_title_clean)
        url_hash = hashlib.md5(entry.get("source_url", main_title_clean).encode()).hexdigest()[:6]
        
        sections[section_name][sub_category]["prompts"].append({
            "title": main_title_clean,
            "url": f"{s_title}_{url_hash}.html",
            "content_structure": content_structure
        })
    print("-> Reestruturação concluída.")
    return sections

def create_search_index(grouped_data):
    search_index = []
    for section_name, sub_categories in grouped_data.items():
        for sub_category_name, details in sub_categories.items():
            for prompt in details["prompts"]:
                content = " ".join([block.get("content", "") for block in prompt.get("content_structure", [])])
                search_index.append({
                    "title": prompt["title"], 
                    "category": sub_category_name,
                    "section": section_name,
                    "url": prompt["url"], 
                    "content": content.lower()
                })
    return search_index

def generate_content_pages(grouped_data, template_html):
    """Gera as páginas de conteúdo final para cada prompt."""
    print("\n--- Gerando Páginas de Conteúdo (Prompts Individuais) ---")
    count = 0
    for section_name, sub_categories in grouped_data.items():
        section_filename = f"secao_{get_safe_filename(section_name)}.html"
        for sub_category_name, details in sub_categories.items():
            for prompt in details["prompts"]:
                count += 1
                
                titles_to_ignore = {prompt['title'], sub_category_name}
                main_content_html = render_content_structure(prompt["content_structure"], titles_to_ignore)
                
                processed_html = template_html.replace('{page_title}', f"{prompt['title']} - {PRODUCT_NAME}")
                processed_html = processed_html.replace('{section_name}', section_name)
                processed_html = processed_html.replace('{section_url}', section_filename)
                processed_html = processed_html.replace('{sub_category_title}', sub_category_name)
                processed_html = processed_html.replace('{main_title}', prompt['title'])
                processed_html = processed_html.replace('{main_content}', main_content_html)
                processed_html = processed_html.replace('{year}', time.strftime("%Y"))
                processed_html = processed_html.replace('{brand_name}', BRAND_NAME)
                
                generate_html_file(processed_html, os.path.join(OUTPUT_DIR_FULL, prompt["url"]))
    print(f"--- {count} páginas de conteúdo geradas. ---")

def render_content_structure(structure, titles_to_ignore):
    content_html = ""
    for block in structure:
        block_type = block.get("type", "paragraph")
        block_content = block.get("content", "")
        
        if block_content.strip() in titles_to_ignore:
            continue

        safe_block_content = html.escape(block_content) if block_type != 'paragraph' else block.get("content", "")

        if not safe_block_content: continue

        if block_type == "subheading":
            anchor_id = re.sub(r'[^\w-]', '', safe_block_content.lower().replace(' ', '-'))[:50]
            content_html += f'<h3 id="{anchor_id}" class="text-2xl font-bold mt-12 mb-4 border-l-4 border-blue-500 pl-4">{safe_block_content}</h3>'
        elif block_type == "paragraph":
            content_html += f'<p class="text-gray-300 text-lg mb-4">{safe_block_content}</p>'
        elif block_type == "prompt":
            content_html += f'''
                <div class="bg-gray-800 rounded-xl border border-gray-700 my-6">
                    <div class="px-6 py-4 border-b border-gray-700 text-gray-300 font-semibold flex justify-between items-center">
                        <span>Prompt de Comando</span>
                        <button class="copy-button bg-gray-700 hover:bg-gray-600 text-white font-bold py-1 px-3 rounded-lg text-sm transition-all">Copiar</button>
                    </div>
                    <div class="p-6">
                        <pre class="whitespace-pre-wrap font-mono text-gray-200"><code>{html.escape(block_content)}</code></pre>
                    </div>
                </div>'''
    return content_html

# --- FUNÇÃO ATUALIZADA COM O NOVO LAYOUT ---
def generate_section_pages(grouped_data, template_html, search_index):
    """Gera uma página de índice para cada SEÇÃO, com o layout de cards agrupados."""
    print("\n--- Gerando Páginas de Índice de Seção (Cards Agrupados) ---")
    count = 0
    for section_name, sub_categories in grouped_data.items():
        count += 1
        
        # Inicia a lista que vai conter os cards de subcategoria
        sub_category_html_list = ""
        
        # Itera sobre cada subcategoria para criar um card
        for sub_category_name, details in sorted(sub_categories.items()):
            
            # Início do card da subcategoria
            sub_category_html_list += f'''
            <div class="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-8">
                <h3 class="text-2xl font-bold mb-4 flex items-center">
                    <span class="text-2xl mr-3">📁</span> {sub_category_name}
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            '''

            # Adiciona os links dos prompts dentro do grid do card
            for prompt in sorted(details["prompts"], key=lambda x: x['title']):
                sub_category_html_list += f'<a href="{prompt["url"]}" class="block bg-gray-900 p-4 rounded-lg border border-gray-600 hover:border-blue-500 hover:bg-gray-700 transition-all duration-200">{prompt["title"]}</a>'
            
            # Fechamento do grid e do card
            sub_category_html_list += '''
                </div>
            </div>
            '''

        section_search_index = [item for item in search_index if item["section"] == section_name]
        js_data_line = f"const searchIndex = {json.dumps(section_search_index, ensure_ascii=False)};"

        # Preenche o template principal da seção
        processed_html = template_html.replace('{category_title}', section_name)
        processed_html = processed_html.replace('{product_name}', PRODUCT_NAME)
        # O emoji principal continua no título da página
        processed_html = processed_html.replace('{emoji}', next(iter(sub_categories.values()))['emoji'])
        processed_html = processed_html.replace('{prompt_list}', sub_category_html_list)
        processed_html = processed_html.replace('{year}', time.strftime("%Y"))
        processed_html = processed_html.replace('{brand_name}', BRAND_NAME)
        processed_html = processed_html.replace('// SEARCH_INDEX_PLACEHOLDER', js_data_line)

        section_filename = f"secao_{get_safe_filename(section_name)}.html"
        generate_html_file(processed_html, os.path.join(OUTPUT_DIR_FULL, section_filename))
    print(f"--- {count} páginas de seção geradas. ---")


def generate_index_page(grouped_data, template_html, search_index):
    """Gera a página principal 'index.html' com um card para cada seção."""
    print("\n--- Gerando Página de Índice Principal (Layout Detalhado) ---")
    index_html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">'
    for section_name, sub_categories in sorted(grouped_data.items()):
        emoji = next(iter(sub_categories.values()))['emoji']
        section_filename = f"secao_{get_safe_filename(section_name)}.html"
        index_html += f'''
        <div class="guide-card flex flex-col bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 class="text-xl font-bold mb-4 flex items-center">
                <span class="text-2xl mr-3">{emoji}</span>{section_name}
            </h3>
            <ul class="list-disc list-inside space-y-2 mb-4 flex-grow text-gray-300">'''
        prompts_to_display = []
        for details in sub_categories.values():
            prompts_to_display.extend(details['prompts'])
        for prompt in prompts_to_display[:5]:
            index_html += f'<li><a href="{prompt["url"]}" class="text-blue-400 hover:text-blue-300 hover:underline">{html.escape(prompt["title"])}</a></li>'
        index_html += '</ul>'
        index_html += f'<a href="{section_filename}" class="block text-center mt-auto bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg w-full transition-colors">Ver todos »</a></div>'
    index_html += '</div>'
    js_data_line = f"const searchIndex = {json.dumps(search_index, ensure_ascii=False)};"
    final_html = template_html.replace('{product_name}', PRODUCT_NAME)
    final_html = final_html.replace('{guide_list}', index_html)
    final_html = final_html.replace('{year}', time.strftime("%Y"))
    final_html = final_html.replace('{brand_name}', BRAND_NAME)
    final_html = final_html.replace('// SEARCH_INDEX_PLACEHOLDER', js_data_line)
    generate_html_file(final_html, os.path.join(OUTPUT_DIR_FULL, "index.html"))
    print("--- Geração da Página de Índice Principal concluída. ---")

def main():
    index_template = load_template(INDEX_TEMPLATE_FILE)
    content_template = load_template(CONTENT_TEMPLATE_FILE)
    section_template = load_template(SECTION_TEMPLATE_FILE)
    if not all([index_template, content_template, section_template]): 
        return
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERRO ao ler a base de dados '{DATABASE_FILE}': {e}")
        return
    grouped_data = restructure_and_group_data(all_data)
    search_index = create_search_index(grouped_data)
    generate_index_page(grouped_data, index_template, search_index)
    generate_section_pages(grouped_data, section_template, search_index)
    generate_content_pages(grouped_data, content_template)
    print("\n\n--- Processo de Geração de Produto Finalizado com Sucesso! ---")
    print(f"Os arquivos HTML foram gerados no diretório: '{OUTPUT_DIR_FULL}'")

if __name__ == "__main__":
    main()