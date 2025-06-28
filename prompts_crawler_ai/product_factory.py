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
DATABASE_FILE = 'prompts_database_final.json'
OUTPUT_DIR_FULL = 'HTML_Arsenal_Completo'
INDEX_TEMPLATE_FILE = 'index_template.html'
CONTENT_TEMPLATE_FILE = 'content_template.html'
SECTION_TEMPLATE_FILE = 'category_template.html' 
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
VIDEO_CONTENT_CACHE_FILE = 'video_content_cache.json'
CONCURRENCY_LIMIT = 5

# --- CONFIGURAÇÕES DE IA E PRODUTO ---
PRODUCT_NAME = "Arsenal Dev AI"
BRAND_NAME = "Brazilian Dev"
gemini_model = None

# PROMPT PARA GERAR EXPLICAÇÃO DO ZERO
VIDEO_WRITER_PROMPT_TEMPLATE = """
Você é um Estratega de Conteúdo e Redator Técnico Sênior. Sua especialidade é destilar a lógica e o potencial de um prompt de IA em uma explicação clara, concisa e estratégica.

**SUA TAREFA:**
Analisando o contexto de uma página (título e exemplos de prompt), sua missão é escrever um texto curto e fluido que explique O MÉTODO ou A ESTRATÉGIA por trás do(s) prompt(s) apresentados. O objetivo é ajudar o usuário a entender *como* e *por que* o prompt funciona, para que ele possa adaptá-lo para qualquer LLM de sua preferência.

**REGRAS CRÍTICAS DE ESCRITA:**

1.  **Foco na Estratégia, Não nos Passos:** Em vez de um "passo a passo", explique o conceito. Por exemplo, em vez de "1. Abra o ChatGPT, 2. Copie o prompt...", escreva sobre a "técnica de usar a IA para gerar ideias de forma massiva e depois aplicá-las em um design..." num parágrafo.

2.  **Texto Fluido em Parágrafos:** A saída deve ser um texto corrido, dividido em 2 ou 3 parágrafos. **NUNCA** use listas numeradas (1, 2, 3...) ou com marcadores (*, -). O texto deve ser conciso e direto.

3.  **Seja Genérico e Abstrato:** NÃO mencione nomes de ferramentas ou softwares específicos (como Canva, TikTok, ChatGPT, Gemini, etc.), a menos que façam parte do texto do prompt original. A explicação deve ser aplicável a qualquer ferramenta de IA ou rede social. Use termos genéricos como "a ferramenta de IA", "a plataforma de vídeo", "sua rede social".

4.  **Tom de Especialista:** Mantenha um tom didático e de especialista, explicando o "pulo do gato" ou a principal vantagem do método.

5.  **Saída Limpa:** Gere APENAS o texto da explicação, sem introduções como "Claro, aqui está o texto:".

6.  **Idioma (MUITO IMPORTANTE):** O texto final deve ser escrito em Português do Brasil.

7.  **Substituição de Marca (OBRIGATÓRIO):** Se o contexto mencionar "Black Magic" ou "AI Avalanche", substitua estes nomes por "Arsenal Dev AI" ou "Brazilian Dev", de forma apropriada. Esta regra é inegociável.

**CONTEXTO DA PÁGINA:**
{page_context}

**EXPLIQUE AGORA O MÉTODO POR TRÁS DO(S) PROMPT(S) USANDO TODAS AS REGRAS ACIMA:**
"""

# NOVO PROMPT PARA APENAS MELHORAR UM TEXTO EXISTENTE
ENHANCE_METHOD_PROMPT = """
Você é um Editor e Estratega de Conteúdo Sênior, com um olhar apurado para clareza e profundidade.

**SUA TAREFA:**
Você receberá um texto que já explica um método para usar um prompt de IA. Sua missão é analisar este texto e o contexto da página. Baseado nisso, siga estritamente a seguinte lógica:

1.  **Se o texto existente já for bom, claro e completo,** simplesmente retorne o texto original, sem adicionar ou remover absolutamente nada.
2.  **Se o texto puder ser significativamente melhorado (por ser muito curto, vago ou confuso),** reescreva-o de forma mais clara e estratégica, mantendo a ideia central.

**REGRAS CRÍTICAS PARA QUANDO REESCREVER:**
- O texto final deve ser fluido, em 2 ou 3 parágrafos. NUNCA use listas.
- Seja genérico e não mencione nomes de ferramentas (Canva, etc.).
- Aplique a substituição de marca obrigatória: "Black Magic" ou "AI Avalanche" devem se tornar "Arsenal Dev AI" ou "Brazilian Dev".
- Retorne apenas o texto final (o original ou o reescrito), sem nenhuma introdução.

**TEXTO ORIGINAL PARA ANÁLISE:**
{existing_explanation}

**CONTEXTO ADICIONAL DA PÁGINA (TÍTULO E PROMPTS):**
{page_context}

**AGORA, RETORNE O TEXTO FINAL (ORIGINAL OU APRIMORADO):**
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

async def generate_video_content_task(semaphore, cache_key, prompt_template, context_data):
    """
    Tarefa assíncrona que formata o prompt correto (gerar ou aprimorar) e chama a API.
    """
    async with semaphore:
        prompt_title = "A aprimorar texto" if 'existing_explanation' in context_data else "A gerar texto do zero"
        print(f"   -> [API] {prompt_title} para a página: {context_data['page_context'][:60]}...")
        
        try:
            # O .format(**context_data) irá preencher {page_context} e, se existir, {existing_explanation}
            prompt = prompt_template.format(**context_data)
            response = await gemini_model.generate_content_async(prompt)
            return (cache_key, response.text)
        except Exception as e:
            print(f"      -> !!! ERRO ao processar a chave {cache_key[:8]}: {e}")
            return (cache_key, None)

async def pre_generate_all_video_content(grouped_data, video_cache):
    """
    Identifica o conteúdo de vídeo necessário, decide se deve gerar ou aprimorar,
    e executa as tarefas em paralelo.
    """
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
                
                # Procura por uma menção a "vídeo" para decidir se a página precisa de atenção
                if any("vídeo" in block.get("content", "").lower() for block in content_structure):
                    
                    page_context = f"Título: {prompt_data['title']}\nSubcategoria: {sub_category_name}\nConteúdo:\n" + "\n".join([f"- {b['type']}: {b['content']}" for b in content_structure])
                    cache_key = hashlib.md5(page_context.encode()).hexdigest()

                    # Continua apenas se o resultado ainda não estiver no cache
                    if cache_key not in video_cache:
                        
                        # AQUI ESTÁ A LÓGICA DE DECISÃO:
                        # 1. Extrai parágrafos que JÁ EXISTEM e que NÃO são o placeholder do vídeo.
                        existing_paragraphs = [
                            block['content'] for block in content_structure 
                            if block.get('type') == 'paragraph' and 'vídeo' not in block.get('content', '').lower()
                        ]
                        
                        # 2. Junta os parágrafos existentes num único texto.
                        existing_explanation = "\n\n".join(existing_paragraphs).strip()

                        # 3. Decide qual prompt usar.
                        if not existing_explanation:
                            # CENÁRIO B: Não há texto, apenas vídeo. Gerar do zero.
                            prompt_to_use = VIDEO_WRITER_PROMPT_TEMPLATE
                            context_for_prompt = {"page_context": page_context}
                        else:
                            # CENÁRIO C: Já existe um texto. Aprimorar.
                            prompt_to_use = ENHANCE_METHOD_PROMPT
                            context_for_prompt = {
                                "page_context": page_context,
                                "existing_explanation": existing_explanation
                            }

                        # 4. Cria a tarefa com o prompt e o contexto corretos.
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

# --- FUNÇÃO ATUALIZADA ---
def render_content_structure(structure, titles_to_ignore, page_context_for_video, video_cache):
    """Renderiza a estrutura, buscando o conteúdo de vídeo do cache pré-populado."""
    content_html = ""
    prompt_count = sum(1 for block in structure if block.get("type") == "prompt")

    for block in structure:
        block_type = block.get("type", "paragraph")
        block_content = block.get("content", "")
        
        if block_content.strip() in titles_to_ignore:
            continue
        
        if "vídeo" in block_content.lower():
            cache_key = hashlib.md5(page_context_for_video.encode()).hexdigest()
            if cache_key in video_cache:
                generated_text = video_cache[cache_key]
                # Corrigido para evitar o SyntaxError com backslash
                formatted_text_for_html = generated_text.replace("\n", "<br>")
                
                content_html += f'''
                <div class="bg-gray-900/50 backdrop-blur-sm border border-blue-500/50 p-6 my-6 rounded-xl">
                    <h4 class="text-xl font-bold text-blue-300 mb-2">Passo a Passo do Método</h4>
                    <div class="text-gray-300 space-y-4">{formatted_text_for_html}</div>
                </div>
                '''
            else:
                print(f"      -> AVISO: Conteúdo para vídeo com chave '{cache_key[:8]}' não foi encontrado no cache. Pulando.")
            continue

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