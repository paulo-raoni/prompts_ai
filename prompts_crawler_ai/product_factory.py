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

def group_data_by_section(data):
    sections = {}
    for entry in data:
        section_name = entry.get('section', 'Outros')
        emoji = entry.get('emoji', '✨')
        
        if section_name not in sections:
            sections[section_name] = {"emoji": emoji, "prompts": []}
        
        if sections[section_name]["emoji"] == '✨' and emoji != '✨':
            sections[section_name]["emoji"] = emoji

        title = entry.get('main_title', 'Guia Sem Título')
        s_title = get_safe_filename(title)
        url_hash = hashlib.md5(entry.get("source_url", title).encode()).hexdigest()[:6]
        
        sections[section_name]["prompts"].append({
            "title": title,
            "category": entry.get('category', 'Geral'),
            "url": f"{s_title}_{url_hash}.html",
            "content_structure": entry.get("content_structure", [])
        })
    return sections

def create_search_index(grouped_data):
    """Cria um índice de busca a partir dos dados agrupados."""
    search_index = []
    for section_name, details in grouped_data.items():
        for prompt in details["prompts"]:
            content = " ".join([block.get("content", "") for block in prompt.get("content_structure", [])])
            search_index.append({
                "title": prompt["title"], 
                "category": prompt["category"],
                "section": section_name,
                "url": prompt["url"], 
                "content": content.lower()
            })
    return search_index

def generate_content_pages(grouped_data, template_html):
    print("\n--- Gerando Páginas de Conteúdo (Prompts Individuais) ---")
    count = 0
    for section in grouped_data.values():
        for prompt in section["prompts"]:
            count += 1
            main_content_html = render_content_structure(prompt["content_structure"])
            processed_html = template_html.replace('{page_title}', f"{prompt['title']} - {PRODUCT_NAME}")
            processed_html = processed_html.replace('{main_title}', prompt['title'])
            processed_html = processed_html.replace('{main_content}', main_content_html)
            processed_html = processed_html.replace('{year}', time.strftime("%Y"))
            processed_html = processed_html.replace('{brand_name}', BRAND_NAME)
            generate_html_file(processed_html, os.path.join(OUTPUT_DIR_FULL, prompt["url"]))
    print(f"--- {count} páginas de conteúdo geradas. ---")

def render_content_structure(structure):
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

def generate_section_pages(grouped_data, template_html, search_index):
    """Gera uma página de índice para cada SEÇÃO, com pesquisa e layout melhorado."""
    print("\n--- Gerando Páginas de Índice de Seção ---")
    count = 0
    for section_name, details in grouped_data.items():
        count += 1
        prompt_list_html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
        
        # Filtra o índice de busca apenas para os itens desta seção
        section_search_index = [item for item in search_index if item["section"] == section_name]
        js_data_line = f"const searchIndex = {json.dumps(section_search_index, ensure_ascii=False)};"

        for prompt in sorted(details["prompts"], key=lambda x: x['title']):
            # Adiciona um ícone SVG para um toque visual
            prompt_list_html += f'''
            <a href="{prompt["url"]}" class="group block bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-blue-500 hover:bg-gray-700 transition-all duration-200 transform hover:-translate-y-1">
                <div class="flex items-center">
                    <svg class="w-6 h-6 text-gray-500 group-hover:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    <span class="ml-3 font-semibold">{prompt["title"]}</span>
                </div>
            </a>
            '''
        prompt_list_html += '</div>'
        
        processed_html = template_html.replace('{category_title}', section_name)
        processed_html = processed_html.replace('{product_name}', PRODUCT_NAME)
        processed_html = processed_html.replace('{emoji}', details["emoji"])
        processed_html = processed_html.replace('{prompt_list}', prompt_list_html)
        processed_html = processed_html.replace('{year}', time.strftime("%Y"))
        processed_html = processed_html.replace('{brand_name}', BRAND_NAME)
        # Injeta os dados da pesquisa
        processed_html = processed_html.replace('// SEARCH_INDEX_PLACEHOLDER', js_data_line)

        section_filename = f"secao_{get_safe_filename(section_name)}.html"
        generate_html_file(processed_html, os.path.join(OUTPUT_DIR_FULL, section_filename))
    print(f"--- {count} páginas de seção geradas. ---")

def generate_index_page(grouped_data, template_html, search_index):
    """Gera a página principal 'index.html' com um card para cada seção."""
    print("\n--- Gerando Página de Índice Principal (Layout Detalhado) ---")
    
    index_html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">'

    for section_name, details in sorted(grouped_data.items()):
        emoji = details["emoji"]
        section_filename = f"secao_{get_safe_filename(section_name)}.html"
        
        index_html += f'''
        <div class="guide-card flex flex-col bg-gray-800 p-6 rounded-xl border border-gray-700">
            <h3 class="text-xl font-bold mb-4 flex items-center">
                <span class="text-2xl mr-3">{emoji}</span>
                {section_name}
            </h3>
            <ol class="list-decimal list-inside space-y-2 mb-4 flex-grow text-gray-300">
        '''
        
        prompts_to_display = details["prompts"][:5]
        for prompt in prompts_to_display:
            index_html += f'<li><a href="{prompt["url"]}" class="text-blue-400 hover:text-blue-300 hover:underline">{html.escape(prompt["title"])}</a></li>'
            
        index_html += '</ol>'
        
        index_html += f'<a href="{section_filename}" class="block text-center mt-auto bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg w-full transition-colors">Ver todos »</a>'
        index_html += '</div>'

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

    grouped_data = group_data_by_section(all_data)
    # Criamos o índice de busca uma vez para ser reutilizado
    search_index = create_search_index(grouped_data)

    generate_index_page(grouped_data, index_template, search_index)
    generate_section_pages(grouped_data, section_template, search_index)
    generate_content_pages(grouped_data, content_template)
    
    print("\n\n--- Processo de Geração de Produto Finalizado com Sucesso! ---")
    print(f"Os arquivos HTML foram gerados no diretório: '{OUTPUT_DIR_FULL}'")

if __name__ == "__main__":
    main()