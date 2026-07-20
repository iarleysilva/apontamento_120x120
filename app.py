import streamlit as st
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Validação de Apontamentos HT",
    page_icon="📋",
    layout="wide"
)

# 1. Carregamento dos dados via link de exportação do Sheets
@st.cache_data(ttl=30)
def carregar_dados():
    sheet_id = "1BYnAn1HYGkrJgCC-L0TCKVepLt3do6zqCPJvYhzcq_Y"
    gid = "117910462"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    df = pd.read_csv(url)
    
    # Tratamentos de Tipos e Formatos
    if 'Percursos' in df.columns:
        df['Percursos'] = df['Percursos'].fillna(0).astype(str).str.replace(r'\.0$', '', regex=True)
    if 'QTS previsto' in df.columns:
        df['QTS previsto'] = pd.to_numeric(df['QTS previsto'], errors='coerce').fillna(0).astype(int)
    if 'QTS regsitrado' in df.columns:
        df['QTS regsitrado'] = pd.to_numeric(df['QTS regsitrado'], errors='coerce').fillna(0).astype(int)
    if 'total tratado' in df.columns:
        df['total tratado'] = pd.to_numeric(df['total tratado'], errors='coerce').fillna(0)
    if 'mês' in df.columns:
        df['mês'] = pd.to_numeric(df['mês'], errors='coerce')
        
    return df

try:
    df_raw = carregar_dados()
    df_clean = df_raw[df_raw['Percursos'] != '0'].dropna(subset=['Percursos']).copy()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()

# 2. Filtros na Barra Lateral
st.sidebar.header("⚙️ Configurações e Filtros")

# Filtro de Mês
meses_nomes = {1.0: "Janeiro", 2.0: "Fevereiro", 3.0: "Março", 4.0: "Abril", 
               5.0: "Maio", 6.0: "Junho", 7.0: "Julho", 8.0: "Agosto", 
               9.0: "Setembro", 10.0: "Outubro", 11.0: "Novembro", 12.0: "Dezembro"}

meses_operacionais = sorted([m for m in df_clean['mês'].dropna().unique() if m in meses_nomes.keys() and m != 5.0])
opcoes_filtro_mes = ["Todos"] + [meses_nomes[m] for m in meses_operacionais]
mes_selecionado = st.sidebar.selectbox("Selecione o Mês", opcoes_filtro_mes)

# Segmentação de dados para Tabela e Dash
df_operacional_base = df_clean[df_clean['mês'] != 5.0].copy()

if mes_selecionado == "Todos":
    df_tabela_filtrado = df_operacional_base.copy()
    df_dash_filtrado = df_clean.copy()
else:
    num_mes = [k for k, v in meses_nomes.items() if v == mes_selecionado][0]
    df_tabela_filtrado = df_operacional_base[df_operacional_base['mês'] == num_mes]
    df_dash_filtrado = df_clean[df_clean['mês'] == num_mes]

# --- LÓGICA DO FILTRO PADRÃO DA OPERAÇÃO ---
def classificar_percurso(row):
    pais = str(row['País']).upper()
    status = str(row['Status']).strip().upper()
    registrado = row['QTS regsitrado']
    
    if pais == 'PARAGUAI':
        return 'Paraguai (Azul)'
    elif registrado > 0:
        return 'OK / Já Registrado (Sem Cor)'
    elif registrado == 0 and ('CONCLUIDO' in status):
        return 'Crítico: Concluído sem Registro (Vermelho)'
    elif registrado == 0 and ('PRONTO' in status):
        return 'Intermediário: Pronto sem Registro (Vermelho)'
    elif registrado == 0:
        return 'Pendente: Aguardando Lançamento (Amarelo)'
    return 'Outros'

if not df_tabela_filtrado.empty:
    df_tabela_filtrado['Filtro_Operacional'] = df_tabela_filtrado.apply(classificar_percurso, axis=1)

    # Ordenação do Status (Pendentes no topo, Concluídos no fundo)
    def definir_peso_status(status_str):
        status_upper = str(status_str).upper()
        if 'CONCLUIDO' in status_upper:
            return 3
        elif 'PRONTO' in status_upper:
            return 2
        else:
            return 1

    df_tabela_filtrado['Ordem_Status'] = df_tabela_filtrado['Status'].apply(definir_peso_status)
    df_tabela_filtrado = df_tabela_filtrado.sort_values(by=['Ordem_Status', 'fatura'], ascending=[True, True])

st.sidebar.markdown("---")
st.sidebar.markdown("**Visualização de Dados (Filtro Padrão)**")

# CORREÇÃO AQUI: As chaves batem 100% agora entre as opções e os valores padrão
opcoes_visao = [
    'Crítico: Concluído sem Registro (Vermelho)', 
    'Intermediário: Pronto sem Registro (Vermelho)',
    'Pendente: Aguardando Lançamento (Amarelo)', 
    'Paraguai (Azul)', 
    'OK / Já Registrado (Sem Cor)'
]

visao_selecionada = st.sidebar.multiselect(
    "Exibir na tabela:", 
    options=opcoes_visao, 
    default=[
        'Crítico: Concluído sem Registro (Vermelho)', 
        'Intermediário: Pronto sem Registro (Vermelho)',
        'Pendente: Aguardando Lançamento (Amarelo)'
    ]
)

if not df_tabela_filtrado.empty:
    df_tabela_final = df_tabela_filtrado[df_tabela_filtrado['Filtro_Operacional'].isin(visao_selecionada)]
else:
    df_tabela_final = pd.DataFrame()

# 3. Definição das Abas
tab_acompanhamento, tab_dash = st.tabs(["📋 Acompanhamento Detalhado", "📊 Dashboard de Resultados"])

# --- ABA 1: ACOMPANHAMENTO DETALHADO (OPERACIONAL) ---
with tab_acompanhamento:
    st.title("📋 Foco Operacional: Percursos Pendentes")
    st.markdown("🛠️ **Ordem de Prioridade Operacional:** Pendentes no Topo 🔼, Prontos no Meio 🟦 e Concluídos na Base 🔽.")
    
    colunas_exibicao = ['Percursos', 'QTS previsto', 'QTS regsitrado', 'Status', 'fatura', 'País', 'Filtro_Operacional']
    colunas_existentes = [c for c in colunas_exibicao if c in df_tabela_final.columns]
    
    if not df_tabela_final.empty:
        df_tabela_exibir = df_tabela_final[colunas_existentes].drop(columns=['Filtro_Operacional'], errors='ignore').reset_index(drop=True)
        
        def colorir_apenas_status(df_data):
            df_styler = pd.DataFrame('', index=df_data.index, columns=df_data.columns)
            for idx, row in df_tabela_final.reset_index(drop=True).iterrows():
                tipo = row['Filtro_Operacional']
                if 'Crítico' in tipo:
                    df_styler.at[idx, 'Status'] = 'background-color: #ffcccc; color: #800000; font-weight: bold; border: 1px solid red;'
                elif 'Intermediário' in tipo:
                    df_styler.at[idx, 'Status'] = 'background-color: #ffebcc; color: #b35c00; font-weight: bold;'
                elif 'Pendente' in tipo:
                    df_styler.at[idx, 'Status'] = 'background-color: #fff2cc; color: #856404; font-weight: bold;'
                elif 'Paraguai' in tipo:
                    df_styler.at[idx, 'Status'] = 'background-color: #e6f2ff; color: #004085; font-weight: bold;'
            return df_styler

        formatos = {'QTS previsto': '{:.0f}', 'QTS regsitrado': '{:.0f}'}
        df_styled = df_tabela_exibir.style.apply(colorir_apenas_status, axis=None).format(formatos)
        st.dataframe(df_styled, use_container_width=True, height=550, hide_index=True)
    else:
        st.success("Tudo limpo! Nenhum percurso pendente ou crítico com os filtros atuais.")

# --- ABA 2: DASHBOARD DE RESULTADOS ---
with tab_dash:
    st.title("📊 Indicadores Gerenciais & Raio-X de Transição Logística")
    st.markdown("Auditoria de processos logísticos com comparativo real entre o Modelo Antigo e a implantação do Modelo Novo.")
    
    # 🎯 BLOCO 1: AUDITORIA DE APONTAMENTOS (Valores consolidados pelo usuário)
    st.subheader("🎯 Auditoria de Apontamentos (Esperado vs Real)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="Volume Esperado (Previsto)", value="165 Peças")
    with c2:
        st.metric(label="Volume Efetuado (Apontado)", value="113 Peças", delta="68.5% Aderência")
    with c3:
        st.metric(label="⚠️ Gap de Lançamento (Pecado do Time)", value="52 Peças", delta="-52 pendentes", delta_color="inverse")
        
    st.markdown("---")
    
    # 🚀 BLOCO 2: ANÁLISE DE IMPACTO LOGÍSTICO E CAPACIDADE (Total Expedido Geral)
    st.subheader("🚀 Análise de Impacto Logístico e Capacidade")
    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric(label="📦 Total Expedido no Período", value="755 Plts")
        st.caption("Saldo total movimentado (desconsiderando o Paraguai).")
    with c5:
        st.metric(label="⚠️ Modelo Antigo Teórico (Base 12)", value="62.9 Estufas")
        st.caption("Estufas totais exigidas se 100% do volume fosse expedido sem a inteligência dos estrados.")
    with c6:
        st.metric(label="🪵 Total de Estrados Tratados", value="6.197 Estrados", delta="37.8 Estufas Equiv. (Base 164)", delta_color="normal")
        st.caption("Capacidade física que passou pelo processo térmico de otimização de cubagem.")

    st.markdown("---")
    
    # 🔍 BLOCO 3: RAIO-X REAL DA COMPOSIÇÃO DE FORÇAS
    st.subheader("🔍 Demonstração de Transição: Modelo Antigo vs Modelo Novo Atual")
    st.markdown("Este bloco expõe por que o modelo novo provisório soma **87 estufas totais**. O estoque passivo anterior ainda pesa muito, mas o ganho futuro já está mapeado.")
    
    c7, c8, c9 = st.columns(3)
    with c7:
        st.metric(label="📦 Volume Passivo Anterior (755 - 165)", value="590 Plts", delta="49.0 Estufas (Base 12)", delta_color="inverse")
        st.caption("Custo inevitável em estufas absorvido pelo estoque produzido no modelo antigo.")
    with c8:
        st.metric(label="🔥 Custo Otimizado Novo (Ações Atuais)", value="37.8 Estufas", delta="Base 164 Aplicada")
        st.caption("Volume gerado pelo processamento otimizado dos 6.197 novos estrados.")
    with c9:
        st.metric(label="📊 Modelo Novo Total Provisório (Passivo + Otimizado)", value="87.0 Estufas", delta="Estoque antigo ainda pesa")
        st.caption("O impacto conjunto atual. À medida que o passivo de 49 estufas zerar, o ganho de eficiência ficará isolado e evidente.")