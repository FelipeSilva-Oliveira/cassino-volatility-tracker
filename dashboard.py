import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO E ESTILO (UI/UX)
# ==========================================
st.set_page_config(page_title="Nolimit City - Radar Pro", layout="wide")

st.markdown("""
<style>
.main { background-color: #0e1117; }

/* Card de Jogo Principal */
.game-card {
    background-color: #1E1E24;
    border: 1px solid #3A3A45;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}
.game-card:hover {
    border-color: #ff4b4b;
    box-shadow: 0 4px 20px rgba(255, 75, 75, 0.15);
    transform: translateY(-2px);
}

/* Textos do Card */
.hot-tag { color: #ff4b4b; font-weight: bold; font-size: 0.85rem; margin-bottom: 8px; display: block; }
.game-title { color: white; font-size: 1.25rem; font-weight: 600; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rtp-val { font-size: 1.8rem; font-weight: 800; color: #fff; margin-bottom: 12px; }
.rtp-val span { font-size: 1rem; color: #888; font-weight: normal; }

/* Linha de Info (Ciclo e Fundo) */
.info-row { display: flex; justify-content: space-between; font-size: 0.9rem; color: #aaa; margin-bottom: 16px; border-bottom: 1px solid #2A2A35; padding-bottom: 12px; }

/* Caixa de Estatísticas Interna */
.stats-box {
    background-color: #121216;
    border-radius: 8px;
    padding: 12px;
    border: 1px solid #2A2A35;
}
.stat-title { color: #fff; font-size: 0.9rem; margin-bottom: 10px; font-weight: 500; }
.stat-row { display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 6px; color: #bbb; }
.stat-row span { color: #00d2ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE DADOS (CACHE DE 60s)
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        conexao = mysql.connector.connect(
            host='localhost', user='root', password='123123', database='cassino_analytics'
        )
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ciclos_volatilidade ORDER BY data_virou_hot DESC")
        dados = cursor.fetchall()
        df = pd.DataFrame(dados)
        conexao.close()
        return df
    except Exception as e:
        st.error(f"Erro no banco de dados: {e}")
        return pd.DataFrame()

# ==========================================
# 3. NAVEGAÇÃO LATERAL (SIDEBAR)
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>NOLIMIT <span style='color: #ff4b4b;'>CITY</span></h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.subheader("Navegação")

pagina = st.sidebar.radio(
    "Escolha a visualização:",
    ["🔥 Resumo de Mercado (Cards)", "📊 Análise Estatística"]
)
st.sidebar.markdown("---")
st.sidebar.info("Atualizando via Fragmento a cada 60s com dados Ouro do MariaDB.")

# ==========================================
# 4. A MÁGICA: FRAGMENTO DE ATUALIZAÇÃO AUTOMÁTICA
# ==========================================
@st.fragment(run_every="60s")
def renderizar_painel():
    df = carregar_dados()

    if pagina == "🔥 Resumo de Mercado (Cards)":
        st.markdown("### Monitoramento Live: Últimos Ciclos de Recuperação")
        st.divider()
        
        if df.empty:
            st.info("Aguardando os primeiros ciclos serem registrados no banco...")
        else:
            df_recentes = df.head(12)
            cols = st.columns(4)
            
            for i, row in df_recentes.iterrows():
                nome = row['nome_jogo']
                hist_jogo = df[df['nome_jogo'] == nome]
                total_vezes = len(hist_jogo)
                
                f_1_5 = len(hist_jogo[(hist_jogo['minutos_para_recuperar'] >= 1) & (hist_jogo['minutos_para_recuperar'] <= 5)])
                f_5_10 = len(hist_jogo[(hist_jogo['minutos_para_recuperar'] > 5) & (hist_jogo['minutos_para_recuperar'] <= 10)])
                f_10_20 = len(hist_jogo[(hist_jogo['minutos_para_recuperar'] > 10) & (hist_jogo['minutos_para_recuperar'] <= 20)])
                f_20_plus = len(hist_jogo[hist_jogo['minutos_para_recuperar'] > 20])
                
                with cols[i % 4]:
                    t = row['minutos_para_recuperar']
                    tempo_txt = f"{t//60}h {t%60}m" if t > 60 else f"{t} min"
                    
                    # HTML COM ZERO ESPAÇOS NA MARGEM ESQUERDA PARA EVITAR BUG DO MARKDOWN
                    st.markdown(f"""
<div class="game-card">
<div class="hot-tag">🔥 HOT RTP</div>
<div class="game-title" title="{nome}">{nome}</div>
<div class="rtp-val">{float(row['rtp_quando_quente']):.0f}% <span>RTP Pico</span></div>
<div class="info-row">
<span>⏳ Ciclo: {tempo_txt}</span>
<span>🧊 Congelado: {float(row['rtp_quando_frio']):.0f}%</span>
</div>
<div class="stats-box">
<div class="stat-title">📈 Histórico ({total_vezes} no total)</div>
<div class="stat-row"><span>1 a 5 min:</span> <span>{f_1_5}</span></div>
<div class="stat-row"><span>5 a 10 min:</span> <span>{f_5_10}</span></div>
<div class="stat-row"><span>10 a 20 min:</span> <span>{f_10_20}</span></div>
<div class="stat-row"><span>+20 min:</span> <span>{f_20_plus}</span></div>
</div>
</div>
""", unsafe_allow_html=True)

 # ==========================================
    # 5. PÁGINA 2: ANÁLISE ESTATÍSTICA (GRÁFICOS)
    # ==========================================
    elif pagina == "📊 Análise Estatística":
        st.markdown("### Distribuição de Frequência e Dispersão")
        st.divider()

        if df.empty:
            st.warning("Sem dados suficientes para gráficos.")
        else:
            if 'jogo_selecionado' not in st.session_state:
                st.session_state.jogo_selecionado = "Todos os Jogos"

            def selecionar_pelo_card(nome_jogo):
                st.session_state.jogo_selecionado = nome_jogo

            jogos_disponiveis = ["Todos os Jogos"] + list(df['nome_jogo'].unique())
            st.selectbox("🔎 Buscar jogo específico:", jogos_disponiveis, key="jogo_selecionado")
            
            st.markdown("<p style='color: #888; font-size: 0.9rem; margin-top: 10px;'>Acesso Rápido (Jogos com mais ciclos registrados):</p>", unsafe_allow_html=True)
            
            # --- CORREÇÃO DOS BOTÕES (Removendo o HTML e adicionando a contagem limpa) ---
            contagem_jogos = df['nome_jogo'].value_counts()
            top_jogos = ["Todos os Jogos"] + list(contagem_jogos.index[:11])
            
            cols = st.columns(6) 
            for i, jogo in enumerate(top_jogos):
                is_ativo = (st.session_state.jogo_selecionado == jogo)
                
                # Formata o nome do botão para mostrar a quantidade de ciclos ex: "Bizarre (29)"
                if jogo == "Todos os Jogos":
                    label_botao = "Todos os Jogos"
                else:
                    label_botao = f"{jogo} ({contagem_jogos[jogo]})"
                
                with cols[i % 6]:
                    st.button(
                        label_botao,
                        type="primary" if is_ativo else "secondary",
                        on_click=selecionar_pelo_card,
                        args=(jogo,),
                        key=f"mini_card_{jogo}",
                        use_container_width=True
                    )
                    
            st.markdown("---")
            jogo_alvo = st.session_state.jogo_selecionado
            df_plot = df if jogo_alvo == "Todos os Jogos" else df[df['nome_jogo'] == jogo_alvo]

            c1, c2, c3 = st.columns(3)
            if not df_plot.empty:
                c1.metric("Tempo Médio de Recuperação", f"{df_plot['minutos_para_recuperar'].mean():.1f} min")
                c2.metric("Ciclos Mapeados (Amostra)", len(df_plot))
                c3.metric("Pico Máximo de RTP", f"{df_plot['rtp_quando_quente'].max():.0f}%")
            else:
                st.info("Ainda não há dados históricos registrados para este jogo.")

            st.markdown("<br>", unsafe_allow_html=True)
            
            if not df_plot.empty:
                # --- GRÁFICOS LADO A LADO ---
                # Cria duas colunas idênticas para dividir a tela ao meio
                col_esq, col_dir = st.columns(2)

                with col_esq:
                    st.markdown("<h4 style='color: white; font-size: 1.1rem;'>Frequência: Faixas de Tempo no 'Gelo'</h4>", unsafe_allow_html=True)
                    fig_hist = px.histogram(
                        df_plot, 
                        x="minutos_para_recuperar", 
                        nbins=20, 
                        color="nome_jogo" if jogo_alvo == "Todos os Jogos" else None,
                        color_discrete_sequence=px.colors.sequential.Plasma,
                        labels={"minutos_para_recuperar": "Minutos em estado Cold"},
                        template="plotly_dark"
                    )
                    # Controla a altura máxima (height) e as margens para o gráfico ficar mais compacto
                    fig_hist.update_layout(yaxis_title="Quantidade de Explosões", height=400, margin=dict(t=20, b=20, l=0, r=0))
                    st.plotly_chart(fig_hist, use_container_width=True)

                with col_dir:
                    st.markdown("<h4 style='color: white; font-size: 1.1rem;'>Linha do Tempo: Picos Registrados</h4>", unsafe_allow_html=True)
                    fig_linha = px.scatter(
                        df_plot, 
                        x="data_virou_hot", 
                        y="rtp_quando_quente", 
                        color="nome_jogo" if jogo_alvo == "Todos os Jogos" else None,
                        size="minutos_para_recuperar",
                        hover_data=["minutos_para_recuperar"],
                        labels={"data_virou_hot": "Data da Ocorrência", "rtp_quando_quente": "RTP de Explosão (%)"},
                        template="plotly_dark"
                    )
                    # Controla a altura máxima (height) para alinhar com o gráfico do lado esquerdo
                    fig_linha.update_layout(height=400, margin=dict(t=20, b=20, l=0, r=0))
                    st.plotly_chart(fig_linha, use_container_width=True)

# ==========================================
# 5. INICIALIZAÇÃO DA INTERFACE
# ==========================================
renderizar_painel()