import streamlit as st
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Validação de Apontamentos HT",
    page_icon="📋",
    layout="wide"
)

SHEET_ID = "1BYnAn1HYGkrJgCC-L0TCKVepLt3do6zqCPJvYhzcq_Y"

# 1. CARREGAMENTO DOS DADOS (DUAS ABAS COMBINADAS)
@st.cache_data(ttl=30)
def carregar_dados_combinados():
    gid_banco = "1463836430"      # Aba Banco_validação (Consolidado)
    gid_percursos = "117910462"   # Aba de Lançamentos de Percursos
    
    url_banco = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid_banco}"
    url_percursos = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid_percursos}"
    
    df_b = pd.read_csv(url_banco)
    df_p = pd.read_csv(url_percursos)
    
    df_b.columns = df_b.columns.str.strip()
    df_p.columns = df_p.columns.str.strip()
    
    # Padronização de nomes de coluna para 'mês' se existir com variação
    for col in df_p.columns:
        if col.lower() in ['mês', 'mes']:
            df_p.rename(columns={col: 'mês'}, inplace=True)
            
    for col in df_b.columns:
        if col.lower() in ['mês', 'mes']:
            df_b.rename(columns={col: 'Mês'}, inplace=True)
    
    # Tratamentos - Percursos
    if 'Percursos' in df_p.columns:
        df_p['Percursos'] = df_p['Percursos'].fillna(0).astype(str).str.replace(r'\.0$', '', regex=True)
    if 'QTS previsto' in df_p.columns:
        df_p['QTS previsto'] = pd.to_numeric(df_p['QTS previsto'], errors='coerce').fillna(0).astype(int)
    if 'QTS registrado' in df_p.columns:
        df_p['QTS registrado'] = pd.to_numeric(df_p['QTS registrado'], errors='coerce').fillna(0).astype(int)
    if 'mês' in df_p.columns:
        df_p['mês'] = pd.to_numeric(df_p['mês'], errors='coerce')
    if 'data' in df_p.columns:
        df_p['data'] = df_p['data'].fillna('-')
        
    # Tratamento das Novas Colunas
    if 'cod_produto_ora' in df_p.columns:
        df_p['cod_produto_ora'] = df_p['cod_produto_ora'].fillna('-').astype(str).str.replace(r'\.0$', '', regex=True)
    if 'formato_nominal' in df_p.columns:
        df_p['formato_nominal'] = df_p['formato_nominal'].fillna('-').astype(str)

    # Tratamentos - Banco Validação
    if 'Total Expedido (Plts)' in df_b.columns:
        df_b['Total Expedido (Plts)'] = pd.to_numeric(df_b['Total Expedido (Plts)'], errors='coerce').fillna(0)
    if 'Total Tratado (Estrados)' in df_b.columns:
        df_b['Total Tratado (Estrados)'] = pd.to_numeric(df_b['Total Tratado (Estrados)'], errors='coerce').fillna(0)
    if 'Meta Prevista' in df_b.columns:
        df_b['Meta Prevista'] = pd.to_numeric(df_b['Meta Prevista'], errors='coerce').fillna(0)
    if 'Mês' in df_b.columns:
        df_b['Mês'] = pd.to_numeric(df_b['Mês'], errors='coerce')

    return df_b, df_p

try:
    df_banco, df_raw_percursos = carregar_dados_combinados()
    df_percursos = df_raw_percursos[df_raw_percursos['Percursos'] != '0'].dropna(subset=['Percursos']).copy()
except Exception as e:
    st.error(f"Erro ao conectar com as abas do Google Sheets: {e}")
    st.stop()

# 2. FILTROS NA BARRA LATERAL
st.sidebar.header("⚙️ Configurações e Filtros")

meses_nomes = {1.0: "Janeiro", 2.0: "Fevereiro", 3.0: "Março", 4.0: "Abril", 
               5.0: "Maio", 6.0: "Junho", 7.0: "Julho", 8.0: "Agosto", 
               9.0: "Setembro", 10.0: "Outubro", 11.0: "Novembro", 12.0: "Dezembro"}

meses_operacionais = sorted([m for m in df_banco['Mês'].dropna().unique() if m in meses_nomes.keys() and m != 5.0])
opcoes_filtro_mes = ["Todos"] + [meses_nomes[m] for m in meses_operacionais]
mes_selecionado = st.sidebar.selectbox("Selecione o Mês", opcoes_filtro_mes)

# Segmentação de Dados por Mês
if mes_selecionado == "Todos":
    df_banco_filtrado = df_banco[df_banco['Mês'] != 5.0].copy()
    if 'mês' in df_percursos.columns:
        df_percursos_filtrado = df_percursos[df_percursos['mês'] != 5.0].copy()
    else:
        df_percursos_filtrado = df_percursos.copy()
else:
    num_mes = [k for k, v in meses_nomes.items() if v == mes_selecionado][0]
    df_banco_filtrado = df_banco[df_banco['Mês'] == num_mes]
    if 'mês' in df_percursos.columns:
        df_percursos_filtrado = df_percursos[df_percursos['mês'] == num_mes]
    else:
        df_percursos_filtrado = df_percursos.copy()

# --- LÓGICA DE NEGÓCIO E CLASSIFICAÇÃO DOS PERCURSOS ---
def classificar_percurso(row):
    pais = str(row['País']).upper() if 'País' in row else ''
    status = str(row['Status']).strip().upper() if 'Status' in row else ''
    registrado = row['QTS registrado'] if 'QTS registrado' in row else 0
    
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

if not df_percursos_filtrado.empty:
    df_percursos_filtrado['Filtro_Operacional'] = df_percursos_filtrado.apply(classificar_percurso, axis=1)

    def definir_peso_status(status_str):
        status_upper = str(status_str).upper()
        if 'CONCLUIDO' in status_upper:
            return 3
        elif 'PRONTO' in status_upper:
            return 2
        else:
            return 1

    df_percursos_filtrado['Ordem_Status'] = df_percursos_filtrado['Status'].apply(definir_peso_status)
    df_percursos_filtrado = df_percursos_filtrado.sort_values(
        by=['Ordem_Status', 'data', 'fatura'], 
        ascending=[True, True, True]
    )

# Filtro Multiselect de Visualização na Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**Visualização de Dados (Filtro Padrão)**")

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
        'Intermediário: Pronto sem Registro (Vermelho)',
        'Pendente: Aguardando Lançamento (Amarelo)'
    ]
)

if not df_percursos_filtrado.empty:
    df_tabela_final = df_percursos_filtrado[df_percursos_filtrado['Filtro_Operacional'].isin(visao_selecionada)]
else:
    df_tabela_final = pd.DataFrame()

# 3. DEFINIÇÃO DAS ABAS
tab_acompanhamento, tab_dash = st.tabs(["📋 Acompanhamento Detalhado", "📊 Dashboard de Resultados"])

# --- ABA 1: ACOMPANHAMENTO DETALHADO (INCLUINDO AS NOVAS COLUNAS) ---
with tab_acompanhamento:
    st.title("📋 Foco Operacional: Percursos Pendentes")
    st.markdown("🛠️ **Ordem de Prioridade Operacional:** Pendentes no Topo 🔼, Prontos no Meio 🟦 e Concluídos na Base 🔽.")
    
    # Ordem das colunas com os novos campos incluídos
    colunas_exibicao = [
        'data', 
        'Percursos', 
        'cod_produto_ora', 
        'formato_nominal', 
        'QTS previsto', 
        'QTS registrado', 
        'Status', 
        'fatura', 
        'País', 
        'Filtro_Operacional'
    ]
    colunas_existentes = [c for c in colunas_exibicao if c in df_tabela_final.columns]
    
    if not df_tabela_final.empty:
        df_tabela_exibir = df_tabela_final[colunas_existentes].drop(columns=['Filtro_Operacional'], errors='ignore').reset_index(drop=True)
        
        # Renomeando cabeçalhos para exibição
        renomear_cabecalhos = {
            'data': 'Data', 
            'fatura': 'Fatura',
            'cod_produto_ora': 'Código Oracle',
            'formato_nominal': 'Formato Nominal'
        }
        df_tabela_exibir = df_tabela_exibir.rename(columns=renomear_cabecalhos)

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

        formatos = {'QTS previsto': '{:.0f}', 'QTS registrado': '{:.0f}'}
        df_styled = df_tabela_exibir.style.apply(colorir_apenas_status, axis=None).format(formatos)
        st.dataframe(df_styled, use_container_width=True, height=550, hide_index=True)
    else:
        st.success("Tudo limpo! Nenhum percurso pendente ou crítico com os filtros atuais.")

# --- ABA 2: DASHBOARD DE RESULTADOS ---
with tab_dash:
    st.title("📊 Indicadores Gerenciais & Raio-X de Transição Logística")
    st.markdown("Auditoria de processos logísticos com comparativo real entre o Modelo Antigo e a implantação do Modelo Novo.")
    
    total_expedido_periodo = float(df_banco_filtrado['Total Expedido (Plts)'].sum()) if 'Total Expedido (Plts)' in df_banco_filtrado.columns else 0.0
    total_tratado_estrados = float(df_banco_filtrado['Total Tratado (Estrados)'].sum()) if 'Total Tratado (Estrados)' in df_banco_filtrado.columns else 0.0
    
    df_p_valido = df_percursos_filtrado[
        df_percursos_filtrado['País'].astype(str).str.upper().str.strip() != 'PARAGUAI'
    ].copy() if not df_percursos_filtrado.empty else pd.DataFrame()
    
    total_previsto = int(df_p_valido['QTS previsto'].sum()) if 'QTS previsto' in df_p_valido.columns else 0
    total_apontado = int(df_p_valido['QTS registrado'].sum()) if 'QTS registrado' in df_p_valido.columns else 0
    
    gap_apontamento = total_previsto - total_apontado
    eficiencia_apontamento = (total_apontado / total_previsto * 100) if total_previsto > 0 else 100.0
    
    estufas_necessarias_sem_otimizacao = total_expedido_periodo / 12.0 if total_expedido_periodo > 0 else 0.0
    volume_passivo_anterior = max(0.0, total_expedido_periodo - total_previsto)
    estufas_consumidas_passivo = volume_passivo_anterior / 12.0 if total_expedido_periodo > 0 else 0.0
    estufas_totais_tratadas_efetivas = total_tratado_estrados / 164.0 if total_tratado_estrados > 0 else 0.0

    # 🎯 BLOCO 1
    st.subheader("🎯 Auditoria de Apontamentos (Esperado vs Real)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="Volume Esperado (Previsto)", value=f"{total_previsto:,} Peças".replace(',', '.'))
    with c2:
        st.metric(
            label="Volume Efetuado (Apontado)", 
            value=f"{total_apontado:,} Peças".replace(',', '.'), 
            delta=f"{eficiencia_apontamento:.1f}% Aderência"
        )
    with c3:
        st.metric(
            label="⚠️ Gap de Lançamento (Pecado do Time)", 
            value=f"{gap_apontamento:,} Peças".replace(',', '.'), 
            delta=f"-{gap_apontamento} pendentes", 
            delta_color="inverse" if gap_apontamento > 0 else "normal"
        )
        
    st.markdown("---")
    
    # 🚀 BLOCO 2
    st.subheader("🚀 Análise de Impacto Logístico e Capacidade")
    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric(label="📦 Total Expedido no Período", value=f"{total_expedido_periodo:,.0f} Plts".replace(',', '.'))
        st.caption("Saldo total expedido movimentado na planilha.")
    with c5:
        st.metric(label="⚠️ Modelo Antigo Teórico (Base 12)", value=f"{estufas_necessarias_sem_otimizacao:.1f} Estufas")
        st.caption("Estufas exigidas se 100% do volume fosse expedido sem inteligência de estrados.")
    with c6:
        st.metric(
            label="🪵 Total de Estrados Tratados", 
            value=f"{total_tratado_estrados:,.0f} Estrados".replace(',', '.'), 
            delta=f"{estufas_totais_tratadas_efetivas:.1f} Estufas Equiv. (Base 164)", 
            delta_color="normal"
        )
        st.caption("Capacidade física que passou pelo processo térmico.")

    st.markdown("---")
    
    # 🔍 BLOCO 3
    st.subheader("🔍 Demonstração de Transição: Modelo Antigo vs Modelo Novo Atual")
    c7, c8, c9 = st.columns(3)
    with c7:
        st.metric(
            label=f"📦 Volume Passivo Anterior ({total_expedido_periodo:.0f} - {total_previsto})", 
            value=f"{volume_passivo_anterior:,.0f} Plts".replace(',', '.'), 
            delta=f"{estufas_consumidas_passivo:.1f} Estufas (Base 12)", 
            delta_color="inverse"
        )
    with c8:
        st.metric(
            label="🔥 Custo Otimizado Novo (Ações Atuais)", 
            value=f"{estufas_totais_tratadas_efetivas:.1f} Estufas", 
            delta="Base 164 Aplicada"
        )
    with c9:
        total_provisorio = estufas_consumidas_passivo + estufas_totais_tratadas_efetivas
        st.metric(
            label="📊 Modelo Novo Total Provisório (Passivo + Otimizado)", 
            value=f"{total_provisorio:.1f} Estufas", 
            delta="Estoque antigo ainda pesa"
        )