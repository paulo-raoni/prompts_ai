import os
import json
import re
import time
import hashlib
import html
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# --- CONFIGURAÇÕES GERAIS ---
load_dotenv()
DATABASE_FILE = 'output/prompts_database_final.json'
OUTPUT_DIR_FULL = 'output/HTML_Arsenal_Completo'
INDEX_TEMPLATE_FILE = 'templates/index_template.html'
CONTENT_TEMPLATE_FILE = 'templates/content_template.html'
SECTION_TEMPLATE_FILE = 'templates/category_template.html' 
VIDEO_CONTENT_CACHE_FILE = 'output/video_content_cache.json'
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
CONCURRENCY_LIMIT = 5

# --- CONFIGURAÇÕES DE IA E PRODUTO ---
PRODUCT_NAME = "Arsenal Dev AI"
BRAND_NAME = "Brazilian Dev"
gemini_model = None

# --- PROMPTS DE IA ---

# PROMPT PARA GERAR DO ZERO (V10 - IA GERA LINKS)
VIDEO_WRITER_PROMPT_TEMPLATE = """
Você é um excelente professor e redator técnico.

**SUA TAREFA:**
Criar um texto curto e simples que explique o método do prompt no contexto abaixo.

**PASSOS DE EXECUÇÃO OBRIGATÓRIOS:**
1.  **CRIE A EXPLICAÇÃO:** Vá direto ao ponto. Não escreva frases introdutórias genéricas. Escreva um texto claro e simples sobre o método, mantendo a separação de parágrafos.
2.  **GENERALIZE FERRAMENTAS E PROMESSAS:** Generalize menções a 'ChatGPT', 'OpenAI', etc., para "a sua ferramenta de IA de preferência". Se o texto original menciona que uma empresa terceira oferece algo (ex: "a OpenAI oferece crédito"), generalize a frase para "alguns provedores de IA podem oferecer crédito". NUNCA atribua a promessa à nossa marca.
3.  **CRIE LINKS HTML:** Transforme URLs e a frase "sua chave de API da ferramenta de IA escolhida" em links HTML clicáveis (`<a href="..." target="_blank">...</a>`).
4.  **LIMPEZA:** Remova frases sobre "vídeo", "template abaixo" ou "clique aqui".
5.  **SUBSTITUA A MARCA:** Troque "Black Magic" ou "AI Avalanche" por "Arsenal Dev AI".
6.  **RETORNE O RESULTADO:** Apresente apenas o texto final, já com as tags <a>.

**CONTEXTO DA PÁGINA:**
{page_context}

**AGORA, EXECUTE OS 6 PASSOS E RETORNE O TEXTO FINAL:**
"""

# PROMPT PARA ADAPTAR TUTORIAIS (V9 - COM REGRA DE NEGÓCIO)
ENHANCE_METHOD_PROMPT = """
Você é um Redator Técnico e Editor especialista em adaptar tutoriais para a nossa plataforma.

**SUA TAREFA:**
Processar o texto do tutorial abaixo através de uma série de passos de adaptação.

**EXECUTE OS SEGUINTES PASSOS DE ADAPTAÇÃO NA ORDEM INDICADA:**
1.  **TRADUZA E PARAGRAFE:** Traduza para um Português do Brasil claro. Mantenha a estrutura de parágrafos do original. Se o texto começar com uma frase introdutória genérica que repete o título, remova-a.
2.  **SUBSTITUA MARCAS:** Substitua "Black Magic" ou "AI Avalanche" por "Arsenal Dev AI".
3.  **GENERALIZE FERRAMENTAS E PROMESSAS (REGRA CRÍTICA):**
    * Generalize nomes como "ChatGPT" e "OpenAI" para "a sua ferramenta de IA de preferência".
    * Generalize "chave de API do ChatGPT" para "a sua chave de API da ferramenta de IA escolhida".
    * **IMPORTANTE:** Se o texto original fizer uma promessa sobre uma empresa terceira (ex: "a OpenAI oferece crédito gratuito"), reescreva a frase para ser genérica e não atribuir a promessa à nossa marca. Exemplo: "alguns provedores de IA podem oferecer crédito gratuito para uso inicial".
4.  **CRIE LINKS HTML:** Transforme URLs e a frase "sua chave de API da ferramenta de IA escolhida" em links HTML clicáveis (`<a href="..." target="_blank" class="text-blue-400 hover:underline">...</a>`). O link para a chave de API deve ser para a pesquisa no Google que já definimos.
5.  **REMOVA REFERÊNCIAS INÚTEIS:** Elimine frases sobre "vídeo", "template abaixo" ou "clique aqui".
6.  **PRESERVE O RESTO:** Mantenha todos os outros passos práticos e URLs explícitas.
7.  **RETORNE O RESULTADO:** Apresente apenas o texto final já formatado com as tags <a>.

**TEXTO ORIGINAL PARA ANÁLISE:**
{existing_explanation}

**CONTEXTO ADICIONAL DA PÁGINA (TÍTULO E PROMPTS):**
{page_context}

**AGORA, PROCESSE O TEXTO SEGUINDO OS 7 PASSOS E RETORNE APENAS O RESULTADO FINAL:**
"""

# --- FUNÇÕES AUXILIARES ---

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

# --- LÓGICA DE GERAÇÃO (ESTRUTURA PRINCIPAL) ---

def restructure_and_group_data(data):
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


# --- FUNÇÕES DE PROCESSAMENTO ASSÍNCRONO DE IA ---

async def generate_video_content_task(semaphore, cache_key, prompt_template, context_data):
    """Tarefa assíncrona que formata o prompt correto (gerar ou aprimorar) e chama a API."""
    async with semaphore:
        prompt_title = "A aprimorar texto" if 'existing_explanation' in context_data else "A gerar texto do zero"
        print(f"   -> [API] {prompt_title} para a página: {context_data['page_context'][:60]}...")
        
        try:
            prompt = prompt_template.format(**context_data)
            response = await gemini_model.generate_content_async(prompt)
            return (cache_key, response.text)
        except Exception as e:
            print(f"      -> !!! ERRO ao processar a chave {cache_key[:8]}: {e}")
            return (cache_key, None)

async def pre_generate_all_video_content(grouped_data, video_cache):
    """Identifica o conteúdo de vídeo necessário, decide se deve gerar ou aprimorar, e executa as tarefas em paralelo."""
    if not gemini_model:
        print("AVISO: O modelo Gemini não está configurado. A geração de conteúdo de vídeo será pulada.")
        return

    print("\n--- Iniciando Pré-geração de Conteúdo de Vídeo em Paralelo (Lógica Contextual) ---")
    tasks = []
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    for section_name, sub_categories in grouped_data.items():
        for sub_category_name, details in sub_categories.items():
            for prompt_data in details["prompts"]:
                content_structure = prompt_data.get("content_structure", [])
                
                if any("vídeo" in block.get("content", "").lower() for block in content_structure):
                    
                    page_context = f"Título: {prompt_data['title']}\nSubcategoria: {sub_category_name}\nConteúdo:\n" + "\n".join([f"- {b['type']}: {b['content']}" for b in content_structure])
                    cache_key = hashlib.md5(page_context.encode()).hexdigest()

                    if cache_key not in video_cache:
                        
                        existing_paragraphs = [
                            block['content'] for block in content_structure 
                            if block.get('type') == 'paragraph' and 'vídeo' not in block.get('content', '').lower()
                        ]
                        existing_explanation = "\n\n".join(existing_paragraphs).strip()

                        if not existing_explanation:
                            prompt_to_use = VIDEO_WRITER_PROMPT_TEMPLATE
                            context_for_prompt = {"page_context": page_context}
                        else:
                            prompt_to_use = ENHANCE_METHOD_PROMPT
                            context_for_prompt = {
                                "page_context": page_context,
                                "existing_explanation": existing_explanation
                            }

                        task = generate_video_content_task(semaphore, cache_key, prompt_to_use, context_for_prompt)
                        tasks.append(task)

    if not tasks:
        print("-> Nenhum conteúdo novo (gerar ou aprimorar) para processar. Tudo já está no cache.")
        return

    print(f"-> A enviar {len(tasks)} novas requisições para a API do Gemini (limite de {CONCURRENCY_LIMIT} em paralelo)...")
    results = await asyncio.gather(*tasks)

    updated_count = 0
    for key, text in results:
        if text:
            video_cache[key] = text
            updated_count += 1
    
    print(f"--- Pré-geração concluída. {updated_count} novos itens foram adicionados ao cache. ---")


# --- FUNÇÕES DE RENDERIZAÇÃO DE HTML (NOVA ARQUITETURA) ---

def consolidate_method_explanation(original_structure, page_context, video_cache):
    """Recebe a estrutura original e devolve uma nova, limpa, com a explicação do método gerada pela IA e sem duplicados."""
    is_video_case = any("vídeo" in block.get("content", "").lower() for block in original_structure)
    if not is_video_case:
        return original_structure

    cache_key = hashlib.md5(page_context.encode()).hexdigest()
    generated_text = video_cache.get(cache_key)

    if not generated_text:
        return [block for block in original_structure if "vídeo" not in block.get("content", "").lower()]

    ai_explanation_block = {"type": "ai_explanation", "content": generated_text}
    
    clean_structure = []
    method_section_started = False
    
    for block in original_structure:
        block_content_lower = block.get("content", "").lower()
        block_type = block.get("type")

        if block_type == "subheading" and "método" in block_content_lower:
            method_section_started = True
            clean_structure.append(block)
            clean_structure.append(ai_explanation_block)
            continue
        
        if method_section_started and block_type == "subheading":
            method_section_started = False
            
        if method_section_started and block_type == "paragraph":
            continue

        if "vídeo" in block_content_lower:
            continue
            
        clean_structure.append(block)

    return clean_structure

def render_content_structure(structure, titles_to_ignore):
    """Renderiza uma estrutura de conteúdo que JÁ VEM com HTML de links da IA."""
    content_html = ""
    prompt_count = sum(1 for block in structure if block.get("type") == "prompt")

    for block in structure:
        block_type = block.get("type")
        block_content = block.get("content", "")

        if block_content.strip() in titles_to_ignore or not block_content:
            continue

        if block_type in ["ai_explanation", "paragraph"]:
            # O conteúdo já vem com links da IA, então apenas trocamos quebras de linha por <br>
            # Não usamos html.escape() aqui para permitir que os links funcionem.
            final_content = block_content.replace("\n", "<br>")
            
            if block_type == "ai_explanation":
                content_html += f'<div class="bg-gray-900/50 p-6 my-6"><div class="text-gray-300 space-y-4">{final_content}</div></div>'
            else:
                content_html += f'<p class="text-gray-300 text-lg mb-4">{final_content}</p>'
        
        elif block_type == "subheading":
            # Títulos são sempre texto puro, então devem ser escapados.
            escaped_content = html.escape(block_content)
            if "comandos" in block_content.lower() or "prompts" in block_content.lower():
                heading_text = "O Comando" if prompt_count == 1 else "Os Comandos"
                content_html += f'<h3 class="text-2xl font-bold mt-12 mb-4 border-l-4 border-blue-500 pl-4">{heading_text}</h3>'
            else:
                content_html += f'<h3 class="text-2xl font-bold mt-12 mb-4 border-l-4 border-blue-500 pl-4">{escaped_content}</h3>'
        
        elif block_type == "prompt":
            # O conteúdo de um prompt DEVE ser escapado.
            escaped_content = html.escape(block_content)
            content_html += f'''
                <div class="bg-gray-800 rounded-xl border border-gray-700 my-6">
                    <div class="px-6 py-4 border-b border-gray-700 text-gray-300 font-semibold flex justify-between items-center">
                        <span>Prompt de Comando</span>
                        <button class="copy-button bg-gray-700 hover:bg-gray-600 text-white font-bold py-1 px-3 rounded-lg text-sm transition-all">Copiar</button>
                    </div>
                    <div class="p-6"><pre class="whitespace-pre-wrap font-mono text-gray-200"><code>{escaped_content}</code></pre></div>
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
                
                page_context_for_video = f"Título: {prompt['title']}\n"
                page_context_for_video += f"Subcategoria: {sub_category_name}\n"
                page_context_for_video += "Conteúdo:\n" + "\n".join([f"- {b['type']}: {b['content']}" for b in prompt["content_structure"]])

                original_content_structure = prompt["content_structure"]
                clean_content_structure = consolidate_method_explanation(original_content_structure, page_context_for_video, video_cache)

                titles_to_ignore = {prompt['title'], sub_category_name}
                main_content_html = render_content_structure(clean_content_structure, titles_to_ignore)
                
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


# --- FUNÇÃO DE ARRANQUE ---

async def main():
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
    
    # 1. ETAPA DE PRÉ-GERAÇÃO PARALELA
    await pre_generate_all_video_content(grouped_data, video_cache)
    
    # 2. ETAPAS DE GERAÇÃO RÁPIDA DE HTML
    generate_index_page(grouped_data, index_template, search_index)
    generate_section_pages(grouped_data, section_template, search_index)
    generate_content_pages(grouped_data, content_template, video_cache)
    
    # 3. SALVAR O CACHE ATUALIZADO
    save_video_cache(video_cache)
    
    print("\n\n--- Processo de Geração de Produto Finalizado com Sucesso! ---")
    print(f"Os arquivos HTML foram gerados no diretório: '{OUTPUT_DIR_FULL}'")

if __name__ == "__main__":
    # Executar a função main assíncrona
    asyncio.run(main())