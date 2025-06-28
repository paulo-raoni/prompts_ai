import os
import json
import re
import time
import hashlib
import html
from dotenv import load_dotenv
import google.generativeai as genai

# --- CONFIGURAÇÕES GERAIS ---
load_dotenv()
DATABASE_FILE = 'prompts_database_final.json'
OUTPUT_DIR_FULL = 'HTML_Arsenal_Completo'
INDEX_TEMPLATE_FILE = 'index_template.html'
CONTENT_TEMPLATE_FILE = 'content_template.html'
SECTION_TEMPLATE_FILE = 'category_template.html' 
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
VIDEO_CONTENT_CACHE_FILE = 'video_content_cache.json'

# --- CONFIGURAÇÕES DE IA E PRODUTO ---
PRODUCT_NAME = "Arsenal Dev AI"
BRAND_NAME = "Brazilian Dev"
gemini_model = None

# --- PROMPT DE ESPECIALISTA ESCRITOR (ATUALIZADO) ---
VIDEO_WRITER_PROMPT_TEMPLATE = """
Você é um Escritor Técnico especialista e Estratega de Conteúdo, com vasta experiência em transformar tópicos complexos em artigos de blog claros, envolventes e fáceis de seguir.

**A SUA TAREFA:**

Eu irei fornecer-lhe o contexto de uma página sobre um determinado método ou prompt de IA. Este contexto inclui o título principal, os subtítulos e os exemplos de prompt.
A página original menciona um "vídeo" para explicar o passo a passo, mas nós não temos acesso a esse vídeo. A sua missão é preencher esta lacuna, criando o conteúdo que estaria nesse vídeo.

**REGRAS DE ESCRITA (CRÍTICO):**

1.  **Analise o Contexto:** Use o título e os exemplos de prompt para inferir o objetivo e os passos lógicos do método.
2.  **Crie uma Secção de "Passo a Passo":** Escreva um texto claro e detalhado que explique o método. Se fizer sentido, use listas numeradas ou com marcadores para quebrar os passos.
3.  **Seja Prático:** Foque-se em dar instruções práticas que o utilizador possa seguir.
4.  **Tom Humano:** Escreva como um especialista a ensinar um colega. Use frases como "O primeiro passo é...", "A chave aqui é...", "Lembre-se de que...".
5.  **NÃO Mencione o Vídeo:** A sua resposta deve ser o conteúdo em si. Nunca escreva frases como "No vídeo, vemos que..." ou "Como mostrado no tutorial...". O texto que você cria **É** o tutorial.
6.  **Saída Limpa:** A sua resposta deve ser apenas o texto do passo a passo, sem introduções como "Claro, aqui está o texto:" ou qualquer outra coisa.
7.  **Idioma (MUITO IMPORTANTE):** O texto final deve ser escrito em **Português do Brasil**. Preste atenção para usar um tom natural brasileiro, evitando expressões, gírias ou construções frasais de Português Europeu.
8.  **Substituição de Marca:** Se o contexto mencionar "Black Magic" ou "AI Avalanche", substitua estes nomes por "Arsenal Dev AI" ou "Brazilian Dev", de forma apropriada.

**CONTEXTO DA PÁGINA:**
{page_context}

**A PARTIR DO CONTEXTO ACIMA, GERE AGORA O TEXTO DO PASSO A PASSO:**
"""

# --- Funções Auxiliares (load_template, generate_html_file, etc.) ---
# (O conteúdo destas funções permanece o mesmo da versão anterior)
def load_template(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f: return f.read()
    except FileNotFoundError:
        print(f"ERRO FATAL: Ficheiro de template '{filename}' não encontrado.")
        return None

def generate_html_file(html_content, output_filename):
    try:
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        with open(output_filename, 'w', encoding='utf-8') as f: f.write(html_content)
    except Exception as e:
        print(f"!!! ERRO ao salvar o ficheiro '{output_filename}': {e}")

def get_safe_filename(name):
    return re.sub(r'[^\w\s-]', '', name).strip().replace(" ", "_")

def setup_gemini():
    global gemini_model
    if not GOOGLE_API_KEY:
        print("AVISO: GOOGLE_API_KEY não encontrada. A geração de conteúdo de vídeo não funcionará.")
        return False
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        print("API do Gemini configurada para geração de conteúdo.")
        return True
    except Exception as e:
        print(f"Erro ao configurar a API do Gemini: {e}")
        return False

def load_video_cache():
    if os.path.exists(VIDEO_CONTENT_CACHE_FILE):
        try:
            with open(VIDEO_CONTENT_CACHE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except json.JSONDecodeError: return {}
    return {}

def save_video_cache(cache):
    with open(VIDEO_CONTENT_CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(cache, f, indent=4, ensure_ascii=False)


# --- Lógica de Geração (com as novas funções) ---
# (O conteúdo das funções de reestruturação e geração de páginas permanece o mesmo)
def restructure_and_group_data(data):
    # ... (código inalterado da versão anterior)
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
    # ... (código inalterado da versão anterior)
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

# --- FUNÇÃO ATUALIZADA ---
def render_content_structure(structure, titles_to_ignore, page_context_for_video, video_cache):
    """Renderiza a estrutura, ajustando plural e gerando conteúdo para vídeos."""
    content_html = ""
    prompt_count = sum(1 for block in structure if block.get("type") == "prompt")

    for block in structure:
        block_type = block.get("type", "paragraph")
        block_content = block.get("content", "")
        
        if block_content.strip() in titles_to_ignore:
            continue
        
        if "vídeo" in block_content.lower() and gemini_model:
            print(f"   -> Encontrada referência a vídeo. A gerar conteúdo inferencial...")
            cache_key = hashlib.md5(page_context_for_video.encode()).hexdigest()
            if cache_key in video_cache:
                print("      -> A usar conteúdo do cache.")
                generated_text = video_cache[cache_key]
            else:
                print("      -> A contactar a API do Gemini para gerar o texto...")
                prompt = VIDEO_WRITER_PROMPT_TEMPLATE.format(page_context=page_context_for_video)
                response = gemini_model.generate_content(prompt)
                generated_text = response.text
                video_cache[cache_key] = generated_text # Salva no cache
            
            # Adiciona o conteúdo gerado como um bloco de destaque
            content_html += f'''
            <div class="bg-gray-900/50 backdrop-blur-sm border border-blue-500/50 p-6 my-6 rounded-xl">
                <h4 class="text-xl font-bold text-blue-300 mb-2">Passo a Passo do Método</h4>
                <div class="text-gray-300 space-y-4">{generated_text.replace("\n", "<br>")}</div>
            </div>
            '''
            continue # Pula a renderização do parágrafo original "siga os passos no vídeo"

        safe_block_content = html.escape(block_content) if block_type != 'paragraph' else block.get("content", "")
        if not safe_block_content: continue

        if block_type == "subheading":
            if "comandos" in block_content.lower() or "prompts" in block_content.lower():
                 heading_text = "O Comando" if prompt_count == 1 else "Os Comandos"
                 content_html += f'<h3 class="text-2xl font-bold mt-12 mb-4 border-l-4 border-blue-500 pl-4">{heading_text}</h3>'
            else:
                 content_html += f'<h3 class="text-2xl font-bold mt-12 mb-4 border-l-4 border-blue-500 pl-4">{safe_block_content}</h3>'
        elif block_type == "paragraph":
            content_html += f'<p class="text-gray-300 text-lg mb-4">{safe_block_content}</p>'
        elif block_type == "prompt":
            content_html += f'''
                <div class="bg-gray-800 rounded-xl border border-gray-700 my-6">
                    <div class="px-6 py-4 border-b border-gray-700 text-gray-300 font-semibold flex justify-between items-center">
                        <span>Prompt de Comando</span>
                        <button class="copy-button bg-gray-700 hover:bg-gray-600 text-white font-bold py-1 px-3 rounded-lg text-sm transition-all">Copiar</button>
                    </div>
                    <div class="p-6"><pre class="whitespace-pre-wrap font-mono text-gray-200"><code>{html.escape(block_content)}</code></pre></div>
                </div>'''
    return content_html

def generate_content_pages(grouped_data, template_html, video_cache):
    print("\n--- Gerando Páginas de Conteúdo (Prompts Individuais) ---")
    count = 0
    for section_name, sub_categories in grouped_data.items():
        section_filename = f"secao_{get_safe_filename(section_name)}.html"
        for sub_category_name, details in sub_categories.items():
            for prompt in details["prompts"]:
                count += 1
                content_structure = prompt["content_structure"]
                titles_to_ignore = {prompt['title'], sub_category_name}

                # Cria o contexto completo da página para enviar à IA do vídeo
                page_context_for_video = f"Título: {prompt['title']}\n"
                page_context_for_video += f"Subcategoria: {sub_category_name}\n"
                page_context_for_video += "Conteúdo:\n" + "\n".join([f"- {b['type']}: {b['content']}" for b in content_structure])

                main_content_html = render_content_structure(content_structure, titles_to_ignore, page_context_for_video, video_cache)
                
                main_title_clean = prompt['title']
                
                processed_html = template_html.replace('{page_title}', f"{main_title_clean} - {PRODUCT_NAME}")
                processed_html = processed_html.replace('{section_name}', section_name)
                processed_html = processed_html.replace('{section_url}', section_filename)
                processed_html = processed_html.replace('{sub_category_title}', sub_category_name)
                processed_html = processed_html.replace('{main_title}', main_title_clean)
                processed_html = processed_html.replace('{main_content}', main_content_html)
                processed_html = processed_html.replace('{year}', time.strftime("%Y"))
                processed_html = processed_html.replace('{brand_name}', BRAND_NAME)
                
                generate_html_file(processed_html, os.path.join(OUTPUT_DIR_FULL, prompt["url"]))
    print(f"--- {count} páginas de conteúdo geradas. ---")

def generate_section_pages(grouped_data, template_html, search_index):
    # ... (código inalterado da versão anterior)
    print("\n--- Gerando Páginas de Índice de Seção (Cards Agrupados) ---")
    count = 0
    for section_name, sub_categories in grouped_data.items():
        count += 1
        sub_category_html_list = ""
        for sub_category_name, details in sorted(sub_categories.items()):
            sub_category_html_list += f'''
            <div class="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-8">
                <h3 class="text-2xl font-bold mb-4 flex items-center">
                    <span class="text-2xl mr-3">📁</span>
                    {sub_category_name}
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            '''
            for prompt in sorted(details["prompts"], key=lambda x: x['title']):
                sub_category_html_list += f'<a href="{prompt["url"]}" class="block bg-gray-900 p-4 rounded-lg border border-gray-600 hover:border-blue-500 hover:bg-gray-700 transition-all duration-200">{prompt["title"]}</a>'
            sub_category_html_list += '''
                </div>
            </div>
            '''
        section_search_index = [item for item in search_index if item["section"] == section_name]
        js_data_line = f"const searchIndex = {json.dumps(section_search_index, ensure_ascii=False)};"
        processed_html = template_html.replace('{category_title}', section_name)
        processed_html = processed_html.replace('{product_name}', PRODUCT_NAME)
        processed_html = processed_html.replace('{emoji}', next(iter(sub_categories.values()))['emoji'])
        processed_html = processed_html.replace('{prompt_list}', sub_category_html_list)
        processed_html = processed_html.replace('{year}', time.strftime("%Y"))
        processed_html = processed_html.replace('{brand_name}', BRAND_NAME)
        processed_html = processed_html.replace('// SEARCH_INDEX_PLACEHOLDER', js_data_line)
        section_filename = f"secao_{get_safe_filename(section_name)}.html"
        generate_html_file(processed_html, os.path.join(OUTPUT_DIR_FULL, section_filename))
    print(f"--- {count} páginas de seção geradas. ---")

def generate_index_page(grouped_data, template_html, search_index):
    # ... (código inalterado da versão anterior)
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
    if not setup_gemini():
        print("A API do Gemini é necessária para gerar conteúdo de vídeo. O script continuará sem esta funcionalidade.")

    index_template = load_template(INDEX_TEMPLATE_FILE)
    content_template = load_template(CONTENT_TEMPLATE_FILE)
    section_template = load_template(SECTION_TEMPLATE_FILE)
    if not all([index_template, content_template, section_template]): return

    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f: all_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERRO ao ler a base de dados '{DATABASE_FILE}': {e}")
        return
        
    video_cache = load_video_cache()

    grouped_data = restructure_and_group_data(all_data)
    search_index = create_search_index(grouped_data)
    
    generate_index_page(grouped_data, index_template, search_index)
    generate_section_pages(grouped_data, section_template, search_index)
    generate_content_pages(grouped_data, content_template, video_cache)
    
    save_video_cache(video_cache) # Salva o cache no final
    
    print("\n\n--- Processo de Geração de Produto Finalizado com Sucesso! ---")
    print(f"Os arquivos HTML foram gerados no diretório: '{OUTPUT_DIR_FULL}'")

if __name__ == "__main__":
    main()