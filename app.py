import json
import os

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Configurações gerais
# ---------------------------------------------------------------------------
LIMITE_USOS_CHAVE_COMPARTILHADA = 5   # análises por sessão usando a chave do app
LIMITE_CARACTERES_EDITAL = 15000      # tamanho máximo do texto colado
MODELO_GEMINI = "gemini-3-flash-preview"

st.set_page_config(
    page_title="Editalis.io - Matriz de Incidência",
    page_icon="⚡",
    layout="wide",
)

# Estilização CSS customizada
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #4f46e5; color: white; }
    .stButton>button:hover { background-color: #4338ca; }
    .stAlert { border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def get_shared_key():
    """Chave fixa do app, guardada em Streamlit Secrets (nunca no código)."""
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        # Sem arquivo secrets.toml (ex.: rodando local sem configurar)
        return None


def get_user_key():
    """Chave que o próprio usuário digitou (vale só para a sessão dele)."""
    return st.session_state.get("user_api_key", "").strip()


def mostrar_tabela(df):
    """Compatível com versões novas e antigas do Streamlit."""
    try:
        st.dataframe(df, width="stretch")
    except TypeError:
        st.dataframe(df, use_container_width=True)


def preencher_exemplo():
    st.session_state["edital_input"] = SAMPLE_CONTENT


SAMPLE_CONTENT = """
DIREITO ADMINISTRATIVO: 1. Estado, governo e administração pública: conceito, elementos, poderes e organização. 2. Agentes públicos: espécies, cargo, emprego e função pública, regras constitucionais (Art. 37 a 41). 3. Poderes administrativos: hierárquico, disciplinar, regulamentar e de polícia. 4. Licitações e Contratos Administrativos: Lei nº 14.133/2021. 5. Improbidade Administrativa: Lei nº 8.429/1992.
DIREITO CONSTITUCIONAL: 1. Direitos e garantias fundamentais: direitos e deveres individuais e coletivos, nacionalidade, direitos políticos. 2. Organização político-administrativa da União, Estados, Municípios e DF. 3. Poder Legislativo, Executivo e Judiciário. 4. Defesa do Estado e das instituições democráticas.
"""


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def analisar_edital(_api_key: str, cargo: str, banca: str, edital_text: str):
    """
    Chama o Gemini e devolve a lista de tópicos.
    - O parâmetro com "_" na frente NÃO entra na chave do cache (a API key
      não fica misturada ao cache).
    - Editais repetidos (mesmo cargo + banca + texto) vêm do cache e não gastam cota.
    - Se der erro, nada é cacheado.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_api_key)

    prompt = f"""
    Você é um especialista sênior em análise de concursos públicos e estrategista de aprovação de alta performance.
    Analise o seguinte conteúdo programático para o cargo de '{cargo}' sob o perfil histórico e estilo de cobrança da banca '{banca}'.

    Refine a análise considerando o peso relativo do tema na prova da referida banca, para cada tópico identificado.

    Retorne uma lista de objetos JSON com as seguintes chaves:
    - materia (nome da matéria)
    - topico (tópico específico do edital)
    - incidencia (use exatamente uma destas strings com emoji: "🔴 Alta Incidência", "🟡 Média Incidência", "🟢 Baixa Incidência")
    - estudo_sugerido (ex: Teoria + Questões, Apenas Revisão, Foco em Jurisprudência Seca)
    - dica_estrategica (uma dica curta e certeira sobre o padrão de cobrança desse tópico específico por essa banca)

    Conteúdo programático:
    {edital_text}
    """

    response = client.models.generate_content(
        model=MODELO_GEMINI,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    data = json.loads(response.text)

    # Se a IA devolver {"itens": [...]} em vez de [...], pega a primeira lista
    if isinstance(data, dict):
        listas = [v for v in data.values() if isinstance(v, list)]
        data = listas[0] if listas else []

    return data


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
    st.title("Editalis.io Pro")
    st.caption("Estratégia de estudos inteligente.")

    st.divider()

    st.markdown("### 🔑 Configuração da IA")
    st.text_input(
        "Usar minha própria chave Gemini (opcional)",
        type="password",
        key="user_api_key",
        help=(
            "O app já funciona com uma chave compartilhada, mas ela tem limite. "
            "Se a cota acabar, gere uma chave gratuita no Google AI Studio e cole aqui. "
            "Sua chave fica apenas na sua sessão e não é salva."
        ),
    )
    if get_user_key():
        st.success("Usando a sua chave pessoal (sem limite do app).", icon="✅")
    elif get_shared_key():
        usos = st.session_state.get("usos", 0)
        restantes = max(0, LIMITE_USOS_CHAVE_COMPARTILHADA - usos)
        st.info(
            f"Usando a chave compartilhada do app. Análises restantes nesta sessão: **{restantes}**. "
            "Quer usar sem limite? Cole sua própria chave acima.",
            icon="ℹ️",
        )
    else:
        st.warning(
            "O app não tem chave compartilhada configurada. Cole sua chave do Google AI Studio acima.",
            icon="🔑",
        )

    st.divider()

    # Seção de Apoio / Pix (Mercado Pago)
    st.markdown("### ☕ Apoie o Projeto")
    st.markdown(
        "Gostou da ferramenta? Contribua **voluntariamente** com qualquer valor para ajudar a manter o projeto no ar!"
    )

    st.markdown(
        """
        <a href="https://mpago.la/2fd7ssC" target="_blank">
            <div style="display: flex; align-items: center; justify-content: center; background-color: #009ee3; color: white; padding: 10px 15px; border-radius: 8px; font-weight: bold; text-align: center; text-decoration: none; margin-bottom: 10px;">
                💙 Pagar um Café (Pix / Cartão)
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )

    # QR Code: coloque o arquivo "qrcode_pix.png" na mesma pasta do app.py
    if os.path.exists("qrcode_pix.png"):
        st.image("qrcode_pix.png", caption="Ou aponte a câmera para o QR Code", width=180)

    st.caption("Ao clicar, você será direcionado ao ambiente seguro do Mercado Pago.")

    st.divider()
    st.caption("Desenvolvido com foco em produtividade.")


# ---------------------------------------------------------------------------
# Corpo principal
# ---------------------------------------------------------------------------
st.title("⚡ Editalis.io - Estruturador de Editais & Matriz de Incidência")
st.markdown(
    "Cole o conteúdo programático do edital, defina o cargo e a banca para gerar uma estratégia de estudo direcionada."
)
st.caption(
    "⚠️ A análise é gerada por inteligência artificial e pode conter imprecisões. "
    "Sempre confira as informações com o edital oficial e com outras fontes."
)

col1, col2 = st.columns([2, 1])

with col1:
    bancas_lista = [
        "Cebraspe (CESPE)", "FGV", "FCC", "Vunesp", "IBFC",
        "AOCP / Instituto AOCP", "Consulplan", "Quadrix", "Outra (Digitar manualmente)",
    ]

    banca_opcao = st.selectbox("Banca Examinadora", bancas_lista)

    if banca_opcao == "Outra (Digitar manualmente)":
        banca = st.text_input("Digite o nome da Banca Examinadora:", placeholder="Ex: Idecan").strip()
    else:
        banca = banca_opcao

with col2:
    cargo = st.text_input(
        "Cargo Pretendido",
        placeholder="Ex: Analista Judiciário / Perito / Inspetor",
    ).strip()

st.button("✨ Inserir Conteúdo de Exemplo", on_click=preencher_exemplo)

edital_text = st.text_area(
    "Cole o Conteúdo Programático do Edital aqui:",
    key="edital_input",
    height=180,
    placeholder="Cole aqui apenas os tópicos e matérias extraídos do edital...",
)
st.caption(f"{len(edital_text)} / {LIMITE_CARACTERES_EDITAL} caracteres")

# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
if st.button("🚀 Gerar Matriz Estratégica com IA", type="primary"):
    user_key = get_user_key()
    shared_key = get_shared_key()
    usando_chave_propria = bool(user_key)
    api_key = user_key or shared_key

    if not api_key:
        st.warning(
            "⚠️ Nenhuma chave de API disponível. Cole a sua **Google Gemini API Key** na barra lateral.",
            icon="🔑",
        )
    elif not edital_text.strip():
        st.error("Por favor, insira o conteúdo programático do edital.")
    elif len(edital_text) > LIMITE_CARACTERES_EDITAL:
        st.error(
            f"O texto tem {len(edital_text)} caracteres e o limite é {LIMITE_CARACTERES_EDITAL}. "
            "Cole apenas as matérias e tópicos, ou divida o edital em partes."
        )
    elif not cargo:
        st.error("Informe o cargo pretendido.")
    elif not banca:
        st.error("Informe o nome da banca examinadora.")
    elif (
        not usando_chave_propria
        and st.session_state.get("usos", 0) >= LIMITE_USOS_CHAVE_COMPARTILHADA
    ):
        st.warning(
            "Você atingiu o limite gratuito desta sessão. "
            "Para continuar sem limite, cole sua própria chave do Google AI Studio na barra lateral.",
            icon="🔑",
        )
    else:
        try:
            with st.spinner(
                f"Analisando o edital para o cargo de '{cargo}' com foco no padrão da banca '{banca}'..."
            ):
                data = analisar_edital(api_key, cargo, banca, edital_text)

            if not usando_chave_propria:
                st.session_state["usos"] = st.session_state.get("usos", 0) + 1

            if not data:
                st.error("A IA não retornou nenhum tópico. Tente novamente ou ajuste o texto do edital.")
            else:
                df = pd.DataFrame(data)

                st.success("Análise estratégica concluída com sucesso!")
                st.markdown("### 📊 Matriz de Incidência e Prioridades")
                mostrar_tabela(df)

                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 Baixar Matriz em CSV (Pronto para importar no Notion/Excel)",
                    data=csv,
                    file_name="matriz_incidencia_edital.csv",
                    mime="text/csv",
                )

        except json.JSONDecodeError:
            st.error("A IA devolveu um formato inválido. Clique em gerar novamente.")
        except Exception as e:
            msg = str(e)
            # Nunca mostre a chave na tela; mensagens da API normalmente não a contêm,
            # mas por segurança removemos qualquer ocorrência.
            if api_key:
                msg = msg.replace(api_key, "***")
            st.error(f"Erro ao processar com a IA: {msg}")
            st.info(
                "Verifique se a chave é válida e se ainda há cota disponível. "
                "Se estiver usando a chave compartilhada, tente colocar a sua própria na barra lateral."
            )
