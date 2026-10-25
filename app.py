import streamlit as st
import pandas as pd
import json
import os

# Configuração da Página
st.set_page_config(
    page_title="Editalis.io - Matriz de Incidência",
    page_icon="⚡",
    layout="wide"
)

# Estilização CSS customizada
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #4f46e5; color: white; }
    .stButton>button:hover { background-color: #4338ca; }
    .stAlert { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Barra Lateral (Sidebar)
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
    st.title("Editalis.ai Pro")
    st.caption("Estratégia de estudos inteligente.")
    
    st.divider()
    
    st.markdown("### 🔑 Configuração da IA")
    api_key_input = st.text_input("Google Gemini API Key", type="password", help="Insira sua chave do Google AI Studio.")
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.success("API Key configurada com sucesso!", icon="✅")
    else:
        st.info("💡 Obtenha sua chave gratuita no Google AI Studio.", icon="ℹ️")
        
    st.divider()
    
    # Seção de Apoio / Pix (Mercado Pago)
    st.markdown("### ☕ Apoie o Projeto")
    st.markdown("Gostou da ferramenta? Contribua com qualquer valor para manter o servidor no ar!")
    
    # Botão estilizado para o Link de Pagamento do Mercado Pago (Substitua SEU_LINK_AQUI pelo link real gerado no MP)
    st.markdown("""
        <a href="https://mpago.la/2fd7ssC" target="_blank">
            <div style="display: flex; align-items: center; justify-content: center; background-color: #009ee3; color: white; padding: 10px 15px; border-radius: 8px; font-weight: bold; text-align: decoration: none; margin-bottom: 10px;">
                💙 Pagar um Café via Pix
            </div>
        </a>
    """, unsafe_allow_html=True)
    
    # Opcional: QR Code estático (basta salvar a imagem como qrcode_pix.png na mesma pasta)
    try:
        st.image("qrcode_pix.png", caption="Escaneie o QR Code Pix", use_container_width=True)
    except:
        pass
        
    st.divider()
    st.caption("Desenvolvido com foco em produtividade.")

# Corpo Principal
st.title("⚡ Editalis.ai - Estruturador de Editais & Matriz de Incidência")
st.markdown("Cole o conteúdo programático do edital, defina o cargo e a banca para gerar uma estratégia de estudo direcionada.")

# Exemplo padrão para teste rápido
sample_content = """
DIREITO ADMINISTRATIVO: 1. Estado, governo e administração pública: conceito, elementos, poderes e organização. 2. Agentes públicos: espécies, cargo, emprego e função pública, regras constitucionais (Art. 37 a 41). 3. Poderes administrativos: hierárquico, disciplinar, regulamentar e de polícia. 4. Licitações e Contratos Administrativos: Lei nº 14.133/2021. 5. Improbidade Administrativa: Lei nº 8.429/1992.
DIREITO CONSTITUCIONAL: 1. Direitos e garantias fundamentais: direitos e deveres individuais e coletivos, nacionalidade, direitos políticos. 2. Organização político-administrativa da União, Estados, Municípios e DF. 3. Poder Legislativo, Executivo e Judiciário. 4. Defesa do Estado e das instituições democráticas.
"""

col1, col2 = st.columns([2, 1])

with col1:
    banca_opcao = st.selectbox("Banca Examinadora", [
        "Cebraspe (CESPE)", "FGV", "FCC", "Vunesp", "IBFC", 
        "AOCP / Instituto AOCP", "Consulplan", "Outra (Digitar manualmente)"
    ])
    
    if banca_opcao == "Outra (Digitar manualmente)":
        banca = st.text_input("Digite o nome da Banca Examinadora:", "Ex: Idecan / Quadrix")
    else:
        banca = banca_opcao

with col2:
    cargo = st.text_input("Cargo Pretendido", "Ex: Analista Judiciário / Perito / Inspetor")

if st.button("✨ Inserir Conteúdo de Exemplo"):
    st.session_state["edital_input"] = sample_content

edital_text = st.text_area(
    "Cole o Conteúdo Programático do Edital aqui:",
    value=st.session_state.get("edital_input", ""),
    height=180,
    placeholder="Cole aqui apenas os tópicos e matérias extraídos do edital..."
)

# Botão de Execução
if st.button("🚀 Gerar Matriz Estratégica com IA", type="primary"):
    current_key = os.environ.get("GEMINI_API_KEY")
    
    if not current_key:
        st.warning("⚠️ Opa! Você esqueceu de inserir a sua **Google Gemini API Key** na barra lateral esquerda. Insira a chave para continuar.", icon="🔑")
    elif not edital_text.strip():
        st.error("Por favor, insira o conteúdo programático do edital.")
    else:
        try:
            from google import genai
            
            client = genai.Client(api_key=current_key)
            
            with st.spinner("Analisando o edital e cruzando com o histórico da banca..."):
                prompt = f"""
                Você é um especialista sênior em análise de concursos públicos e estrategista de aprovação de alta performance.
                Analise o seguinte conteúdo programático para o cargo de '{cargo}' sob o perfil histórico e estilo de cobrança da banca '{banca}'.
                
                Refine a análise considerando o peso relativo do tema na prova da referida banca.
                
                Retorne a resposta EXCLUSIVAMENTE em formato JSON (sem blocos de código markdown adicionais, apenas o JSON puro) contendo uma lista de objetos com as seguintes chaves:
                - materia (nome da matéria)
                - topico (tópico específico do edital)
                - incidencia (use exatamente uma destas strings com emoji: "🔴 Alta Incidência", "🟡 Média Incidência", "🟢 Baixa Incidência")
                - estudo_sugerido (ex: Teoria + Questões, Apenas Revisão, Foco em Jurisprudência Seca)
                - dica_estrategica (uma dica curta e certeira sobre o padrão de cobrança desse tópico específico por essa banca)
                
                Conteúdo programático:
                {edital_text}
                """
                
                response = client.models.generate_content(
                    model='gemini-3-flash-preview',
                    contents=prompt
                )
                
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()
                
                data = json.loads(raw_text)
                df = pd.DataFrame(data)
                
                st.success("Análise estratégica concluída com sucesso!")
                
                st.markdown("### 📊 Matriz de Incidência e Prioridades")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar Matriz em CSV (Pronto para importar no Notion/Excel)",
                    data=csv,
                    file_name='matriz_incidencia_edital.csv',
                    mime='text/csv',
                )
                
        except Exception as e:
            st.error(f"Erro ao processar com a IA: {e}")
            st.info("Verifique se a sua API Key é válida e se há saldo/limite disponível na sua conta do Google AI Studio.")