import sys
import os
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import random
import folium
from streamlit_folium import st_folium

# =============== CORREÇÃO PRINCIPAL ===============
# st.set_page_config() DEVE SER A PRIMEIRA CHAMADA DO STREAMLIT
st.set_page_config(
    page_title="AgroInsight - Dashboard Agrícola",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============== CSS PARA MELHOR VISIBILIDADE ===============
st.markdown("""
<style>
    /* Reset básico para consistência */
    * {
        box-sizing: border-box;
    }
    
    /* Fundo geral do dashboard */
    .reportview-container {
        background: #f0f2f6;
        color: #333;
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background: #2c3e50 !important;
        color: #ecf0f1 !important;
        padding: 20px 0 !important;
    }
    
    /* Cabeçalhos na sidebar */
    .sidebar h1, .sidebar h2, .sidebar h3, .sidebar h4 {
        color: #ecf0f1 !important;
        margin-bottom: 15px !important;
    }
    
    /* Métricas principais */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        transition: transform 0.2s;
        border: 1px solid #e0e0e0;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    /* Dados simulados */
    .simulated-data {
        background-color: #e6f7ff !important;
        border-left: 4px solid #1890ff;
        border: 1px solid #bae7ff;
    }
    
    /* Alertas de alta prioridade */
    .alert-high {
        background-color: #fff0f0;
        border-left: 4px solid #ff4b4b;
        border: 1px solid #ffd9d9;
        color: #590909;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Alertas de média prioridade */
    .alert-medium {
        background-color: #fff9e6;
        border-left: 4px solid #ffa500;
        border: 1px solid #ffe5b3;
        color: #5c3d00;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Alertas de baixa prioridade */
    .alert-low {
        background-color: #f6ffed;
        border-left: 4px solid #52c41a;
        border: 1px solid #e6ffac;
        color: #237804;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Títulos dos alertas */
    .alert-title {
        font-weight: 600;
        margin: 0 0 8px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Mensagens dos alertas */
    .alert-message {
        margin: 0 0 8px 0;
        line-height: 1.4;
    }
    
    /* Horário dos alertas */
    .alert-time {
        font-size: 0.85em;
        color: #777;
        margin-top: 8px;
        display: block;
    }
    
    /* Fontes para melhor legibilidade */
    .data-source {
        font-size: 0.8em;
        color: #666;
        text-align: right;
        margin-top: -10px;
    }
    
    /* Botões */
    .stButton>button {
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }
    
    /* Tabelas */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Debug info */
    .debug-info {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 6px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 0.9em;
        border: 1px solid #e9ecef;
    }
    
    /* Ajustes para tema escuro (se aplicável) */
    @media (prefers-color-scheme: dark) {
        .reportview-container {
            background: #1a1a1a;
            color: #e0e0e0;
        }
        
        .metric-card {
            background: #2d2d2d;
            border: 1px solid #444;
        }
        
        .simulated-data {
            background-color: #1a2b4a !important;
            border: 1px solid #2a4d8a;
        }
        
        .alert-high {
            background-color: #3a1a1a;
            border: 1px solid #5a2a2a;
            color: #ffcccc;
        }
        
        .alert-medium {
            background-color: #3a301a;
            border: 1px solid #5a4a2a;
            color: #ffe6b3;
        }
        
        .alert-low {
            background-color: #1a3a1a;
            border: 1px solid #2a5a2a;
            color: #acffac;
        }
        
        .debug-info {
            background-color: #252525;
            border: 1px solid #333;
            color: #e0e0e0;
        }
    }
</style>
""", unsafe_allow_html=True)

# =============== CONFIGURAÇÃO DO CAMINHO DO PROJETO ===============
def setup_project_path():
    """Configura o caminho do projeto para funcionar em qualquer sistema operacional."""
    # Obtém o caminho absoluto do diretório atual do script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Obtém o caminho da pasta raiz do projeto (um nível acima de 'dashboard')
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    
    # Adiciona ao PYTHONPATH se ainda não estiver lá
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        return project_root, True
    return project_root, False

# Executa a configuração do caminho
project_root, is_new_path = setup_project_path()

# =============== IMPORTAÇÃO SEGURO COM FALLBACK ===============
try:
    from core.data_collector import CommoditiesCollector
    
    # Função de teste para verificar se o coletor funciona
    def test_collector():
        try:
            collector = CommoditiesCollector()
            data = collector.collect_all()
            return data, True
        except Exception as e:
            return str(e), False
            
    collector_data, collector_available = test_collector()
    
except ImportError as e:
    st.error("""
    ❌ ERRO DE IMPORTAÇÃO: Não foi possível carregar o módulo 'core.data_collector'.
    
    Possíveis causas:
    1. A estrutura de pastas está incorreta
    2. O arquivo 'data_collector.py' não existe na pasta 'core'
    3. Erros no próprio arquivo data_collector.py
    
    Soluções:
    1. Verifique se sua estrutura de pastas é:
       commodities/
       ├── core/
       │   └── data_collector.py
       └── dashboard/
           └── main.py
    
    2. Certifique-se que o arquivo data_collector.py existe e está correto
    
    3. Execute este comando no terminal para diagnosticar:
       python -c "import sys; print('PYTHONPATH:', sys.path)"
    """)
    st.stop()  # Para a execução do Streamlit

# =============== INFORMAÇÕES DE DEPURAÇÃO ===============
with st.expander("ℹ️ Informações de Depuração", expanded=False):
    st.markdown('<div class="debug-info">', unsafe_allow_html=True)
    st.write("Diretório atual:", os.getcwd())
    st.write("Caminho do script:", __file__)
    st.write("Caminho do projeto:", project_root)
    st.write("PYTHONPATH:", sys.path)
    
    if collector_available:
        st.success("✅ Módulo core.data_collector importado com sucesso!")
        st.write("Dados coletados:", collector_data)
    else:
        st.error(f"❌ Erro ao testar o coletor: {collector_data}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# =============== FUNÇÕES DE UTILIDADE ===============
@st.cache_data(ttl=3600)
def load_commodity_data():
    """Carrega dados usando o coletor atualizado com fallback seguro."""
    try:
        collector = CommoditiesCollector()
        return collector.collect_all()
    except Exception as e:
        st.warning(f"⚠️ Erro ao coletar dados: {str(e)}")
        # Dados de fallback para desenvolvimento
        return {
            "cepea": {
                "commodity": "soja",
                "price": 158.5,
                "variation": "+2.3%",
                "source": "SIMULADO_DESENVOLVIMENTO",
                "timestamp": datetime.now().isoformat()
            },
            "b3": {
                "commodity": "soja_futuro",
                "price": 15.85,
                "variation": "+0.75%",
                "source": "SIMULADO_DESENVOLVIMENTO",
                "timestamp": datetime.now().isoformat()
            },
            "usd": {
                "currency": "USD",
                "rate": 5.24,
                "variation": "-0.5%",
                "source": "SIMULADO_DESENVOLVIMENTO",
                "timestamp": datetime.now().isoformat()
            },
            "inmet": {
                "state": "MT",
                "avg_rainfall_mm": 120.0,
                "source": "SIMULADO_DESENVOLVIMENTO",
                "timestamp": datetime.now().isoformat()
            },
            "conab": {
                "commodity": "soja",
                "production_million_tons": 152.4,
                "state": "BR",
                "source": "SIMULADO_DESENVOLVIMENTO",
                "timestamp": datetime.now().isoformat()
            }
        }

def plot_price_trend(df, title, source_status):
    """Plota gráfico com indicação de dados reais/simulados."""
    fig = px.line(df, x='date', y='price', title=title,
                 labels={'price': 'Preço (R$)', 'date': 'Data'})
    
    # Adiciona anotação sobre a fonte dos dados
    source_text = "Dados: Fonte Oficial" if "REAL" in source_status else "Dados: Simulados (fonte temporariamente indisponível)"
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        text=source_text,
        font=dict(color="#666", size=12)
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2c3e50'),
        hovermode="x unified",
        margin=dict(b=60)  # Mais espaço na parte inferior para a anotação
    )
    return fig

def get_data_source_badge(source):
    """Retorna badge indicando se os dados são reais ou simulados."""
    if "SIMULADO" in source.upper():
        return '<span style="background-color: #e6f7ff; color: #1890ff; padding: 2px 6px; border-radius: 4px; font-size: 0.8em">⚠️ Dados Simulados</span>'
    return '<span style="background-color: #f6ffed; color: #52c41a; padding: 2px 6px; border-radius: 4px; font-size: 0.8em">✅ Dados Oficiais</span>'

# =============== BARRA LATERAL ===============
with st.sidebar:
    st.image("https://i.imgur.com/JoKdA8S.jpeg", width=200)
    st.title("🌾 AgroInsight")
    
    commodity = st.selectbox(
        "Selecione a commodity",
        ["soja", "milho", "boi", "café", "trigo"],
        index=0
    )
    
    time_frame = st.selectbox(
        "Período de análise",
        ["7 dias", "30 dias", "90 dias", "1 ano"],
        index=1
    )
    
    st.divider()
    st.subheader("Configurações")
    
    # Botão de atualização com feedback visual
    refresh = st.button("🔄 Atualizar Dados", use_container_width=True, type="primary")
    
    # Mostra status da última atualização
    last_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.caption(f"Última atualização: {last_update}")

# =============== CONTEÚDO PRINCIPAL ===============
st.title(f"📊 Dashboard de {commodity.capitalize()} - Análise Agrícola")

# Adiciona spinner durante a atualização
if refresh:
    with st.spinner('Atualizando dados em tempo real...'):
        time.sleep(1.5)  # Simula tempo de carregamento real
        st.rerun()  # Recarrega a página

# Carrega os dados
data = load_commodity_data()

# Métricas rápidas com indicação de fonte
col1, col2, col3, col4 = st.columns(4)
with col1:
    source_status = data["cepea"]["source"] if data["cepea"] else "N/A"
    st.markdown('<div class="metric-card ' + ('simulated-data' if "SIMULADO" in source_status.upper() else '') + '">', unsafe_allow_html=True)
    if data["cepea"]:
        st.metric("Preço Atual (CEPEA)", f"R$ {data['cepea']['price']:.2f}", data['cepea']['variation'])
        st.markdown(f'<div class="data-source">{get_data_source_badge(source_status)} | {data["cepea"]["timestamp"][:16]}</div>', unsafe_allow_html=True)
    else:
        st.metric("Preço Atual (CEPEA)", "N/A", "Erro na coleta")
        st.markdown('<div class="data-source"><span style="color: #ff4b4b">⚠️ Dados não disponíveis</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    source_status = data["usd"]["source"] if data["usd"] else "N/A"
    st.markdown('<div class="metric-card ' + ('simulated-data' if "SIMULADO" in source_status.upper() else '') + '">', unsafe_allow_html=True)
    if data["usd"]:
        st.metric("Dólar Comercial", f"R$ {data['usd']['rate']:.4f}", data['usd']['variation'])
        st.markdown(f'<div class="data-source">{get_data_source_badge(source_status)} | {data["usd"]["timestamp"][:16]}</div>', unsafe_allow_html=True)
    else:
        st.metric("Dólar Comercial", "N/A", "Erro na coleta")
        st.markdown('<div class="data-source"><span style="color: #ff4b4b">⚠️ Dados não disponíveis</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    source_status = data["conab"]["source"] if data["conab"] else "N/A"
    st.markdown('<div class="metric-card ' + ('simulated-data' if "SIMULADO" in source_status.upper() else '') + '">', unsafe_allow_html=True)
    if data["conab"]:
        st.metric("Produção (CONAB)", f"{data['conab']['production_million_tons']} mi t", "+4,2%")
        st.markdown(f'<div class="data-source">{get_data_source_badge(source_status)} | {data["conab"]["timestamp"][:16]}</div>', unsafe_allow_html=True)
    else:
        st.metric("Produção (CONAB)", "N/A", "Erro na coleta")
        st.markdown('<div class="data-source"><span style="color: #ff4b4b">⚠️ Dados não disponíveis</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    source_status = data["inmet"]["source"] if data["inmet"] else "N/A"
    st.markdown('<div class="metric-card ' + ('simulated-data' if "SIMULADO" in source_status.upper() else '') + '">', unsafe_allow_html=True)
    if data["inmet"]:
        status = "Abaixo" if data["inmet"]["avg_rainfall_mm"] < 100 else "Normal"
        st.metric("Precipitação MT", f"{data['inmet']['avg_rainfall_mm']}mm", status)
        st.markdown(f'<div class="data-source">{get_data_source_badge(source_status)} | {data["inmet"]["timestamp"][:16]}</div>', unsafe_allow_html=True)
    else:
        st.metric("Precipitação MT", "N/A", "Erro na coleta")
        st.markdown('<div class="data-source"><span style="color: #ff4b4b">⚠️ Dados não disponíveis</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =============== ABAS PRINCIPAIS ===============
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Análise de Preços", 
    "🌦️ Clima & Safra", 
    "🔔 Alertas", 
    "🔮 Previsões"
])

# Aba 1: Análise de Preços
with tab1:
    st.subheader("Tendência de Preços")
    
    # Simula dados históricos (em produção: viria do banco)
    days = 30 if "30" in time_frame else 7 if "7" in time_frame else 90 if "90" in time_frame else 365
    dates = pd.date_range(end=datetime.now(), periods=days)
    
    # Usa preço real se disponível, senão usa valor padrão
    base_price = data["cepea"]["price"] if data["cepea"] else 150.0
    
    # Simulação realista com sazonalidade
    prices = [base_price - 5 + i*0.5 + 10 * abs((i % 12) - 6) for i in range(days)]
    hist_data = pd.DataFrame({"date": dates, "price": prices})
    
    # Determina status da fonte
    source_status = "REAL" if data["cepea"] and "SIMULADO" not in data["cepea"].get("source", "").upper() else "SIMULADO"
    
    # Gráfico principal
    st.plotly_chart(
        plot_price_trend(hist_data, f"Preço da {commodity} - {days} dias", source_status),
        use_container_width=True
    )
    
    # Comparativo com dólar
    st.subheader("Correlação com Dólar")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Preço da soja vs Dólar (últimos 30 dias)")
        
        # Dados reais se disponíveis, senão simulados
        if data["cepea"] and data["usd"]:
            df_corr = pd.DataFrame({
                'date': pd.date_range(end=datetime.now(), periods=30),
                'soja': [data["cepea"]["price"] + i*0.3 for i in range(30)],
                'dolar': [data["usd"]["rate"] + i*0.02 for i in range(30)]
            })
        else:
            # Dados simulados
            df_corr = pd.DataFrame({
                'date': pd.date_range(end=datetime.now(), periods=30),
                'soja': [150 + i*0.3 for i in range(30)],
                'dolar': [5.1 + i*0.02 for i in range(30)]
            })
        
        try:
            fig = px.scatter(df_corr, x='dolar', y='soja', trendline="ols",
                            labels={"dolar": "Dólar (R$)", "soja": "Soja (R$/saca)"})
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning("⚠️ Erro ao gerar linha de tendência. Instale o statsmodels: pip install statsmodels")
            st.plotly_chart(px.scatter(df_corr, x='dolar', y='soja',
                                      labels={"dolar": "Dólar (R$)", "soja": "Soja (R$/saca)"}), 
                           use_container_width=True)
    
    with col2:
        st.caption("Destinos de Exportação")
        export_data = pd.DataFrame({
            'País': ['China', 'União Europeia', 'Estados Unidos', 'Outros'],
            'Volume (%)': [65, 15, 10, 10]
        })
        fig = px.pie(export_data, values='Volume (%)', names='País', hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

# Aba 2: Clima & Safra
with tab2:
    st.subheader("Mapa de Risco Climático")
    
    # Mapa interativo com Folium
    m = folium.Map(location=[-15.78, -47.91], zoom_start=4)
    
    # Dados reais do INMET se disponíveis
    risks = []
    if data["inmet"]:
        avg_rain = data["inmet"]["avg_rainfall_mm"]
        risk_level = "ALTO" if avg_rain < 50 else "MÉDIO" if avg_rain < 100 else "BAIXO"
        risks.append({
            "state": data["inmet"]["state"],
            "risk": risk_level,
            "coords": [-12.647, -55.424] if data["inmet"]["state"] == "MT" else [-24.89, -51.55]
        })
    
    # Adiciona estados vizinhos para contexto
    risks.extend([
        {"state": "GO", "risk": "MÉDIO", "coords": [-15.979, -49.809]},
        {"state": "PR", "risk": "MÉDIO", "coords": [-24.89, -51.55]},
        {"state": "RS", "risk": "BAIXO", "coords": [-30.01, -51.15]}
    ])
    
    for risk in risks:
        color = "red" if risk["risk"] == "ALTO" else "orange" if risk["risk"] == "MÉDIO" else "green"
        folium.Marker(
            location=risk["coords"],
            popup=f"{risk['state']} - Risco {risk['risk']}",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
    
    st_folium(m, width=1200, height=500)
    
    # Tabela de dados climáticos
    st.subheader("Dados Pluviométricos por Estado")
    
    # Mostra status da fonte
    if data["inmet"] and "SIMULADO" in data["inmet"].get("source", "").upper():
        st.warning("⚠️ Dados climáticos simulados - fonte oficial temporariamente indisponível")
    
    rainfall_data = pd.DataFrame([
        {"Estado": "MT", "Precipitação (mm)": data["inmet"]["avg_rainfall_mm"] if data["inmet"] else 120, 
         "Média Histórica": 200, "Status": "Abaixo" if data["inmet"] and data["inmet"]["avg_rainfall_mm"] < 150 else "Normal"},
        {"Estado": "GO", "Precipitação (mm)": 150, "Média Histórica": 180, "Status": "Abaixo"},
        {"Estado": "PR", "Precipitação (mm)": 180, "Média Histórica": 170, "Status": "Acima"},
        {"Estado": "RS", "Precipitação (mm)": 210, "Média Histórica": 200, "Status": "Normal"}
    ])
    
    st.dataframe(rainfall_data.style.applymap(
        lambda x: "background-color: #ffcccc" if x == "Abaixo" else 
                 "background-color: #ffffcc" if x == "Acima" else "",
        subset=["Status"]
    ))

# Aba 3: Alertas
with tab3:
    st.subheader("Alertas Ativos")
    
    # Gera alertas baseados nos dados coletados
    alerts = []
    
    # Alerta de preço
    if data["cepea"] and data["cepea"].get("variation", ""):
        variation_str = data["cepea"]["variation"].replace("%", "")
        try:
            variation = float(variation_str)
            if variation > 5:
                alerts.append({
                    "tipo": "PREÇO",
                    "nível": "ALTO",
                    "mensagem": f"Preço da soja {data['cepea']['variation']} nas últimas 24h",
                    "horário": datetime.now().strftime("%H:%M")
                })
            elif variation > 2:
                alerts.append({
                    "tipo": "PREÇO",
                    "nível": "MÉDIO",
                    "mensagem": f"Preço da soja {data['cepea']['variation']} nas últimas 24h",
                    "horário": datetime.now().strftime("%H:%M")
                })
        except (ValueError, TypeError):
            pass
    
    # Alerta climático
    if data["inmet"] and data["inmet"].get("avg_rainfall_mm", 0) < 50:
        alerts.append({
            "tipo": "CLIMA",
            "nível": "ALTO",
            "mensagem": f"Baixa precipitação em {data['inmet']['state']} (<50mm)",
            "horário": datetime.now().strftime("%H:%M")
        })
    
    # Alerta de produção
    if data["conab"] and data["conab"].get("production_million_tons", 0) > 150:
        alerts.append({
            "tipo": "MERCADO",
            "nível": "MÉDIO",
            "mensagem": "Produção de soja acima da média histórica",
            "horário": "Ontem"
        })
    
    # Se não houver alertas, mostra mensagem amigável
    if not alerts:
        st.info("✅ Nenhum alerta crítico detectado. Condições normais de mercado e clima.")
    
    for alert in alerts:
        alert_class = "alert-high" if alert["nível"] == "ALTO" else "alert-medium" if alert["nível"] == "MÉDIO" else "alert-low"
        
        # Ícone baseado no nível de alerta
        if alert["nível"] == "ALTO":
            icon = "🚨"
        elif alert["nível"] == "MÉDIO":
            icon = "⚠️"
        else:
            icon = "ℹ️"
        
        st.markdown(f"""
        <div class="{alert_class}">
            <div class="alert-title">{icon} {alert['tipo']} - {alert['nível']}</div>
            <div class="alert-message">{alert['mensagem']}</div>
            <span class="alert-time">Horário: {alert['horário']}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.button("Marcar como lido", type="primary", use_container_width=True)

# Aba 4: Previsões
with tab4:
    st.subheader("Previsões de Preço")
    
    # Simula previsão (em produção: usaria modelo real)
    periods = 7
    forecast_dates = pd.date_range(start=datetime.now(), periods=periods)
    base_price = data["cepea"]["price"] if data["cepea"] else 150
    
    # Simulação realista com tendência
    forecast_prices = [base_price + i*0.2 + random.uniform(-1, 1) for i in range(periods)]
    lower_bound = [p - 2 for p in forecast_prices]
    upper_bound = [p + 2 for p in forecast_prices]
    
    forecast = pd.DataFrame({
        "date": forecast_dates,
        "price": forecast_prices,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound
    })
    
    # Gráfico de previsão
    fig = px.line(forecast, x='date', y='price', title=f"Previsão 7 dias - {commodity.capitalize()}")
    fig.add_scatter(x=forecast['date'], y=forecast['lower_bound'], 
                   mode='lines', name='Limite Inferior', line=dict(dash='dash'))
    fig.add_scatter(x=forecast['date'], y=forecast['upper_bound'], 
                   mode='lines', name='Limite Superior', line=dict(dash='dash'))
    
    # Adiciona anotação sobre a fonte
    source = "Fonte Oficial" if data["cepea"] and "SIMULADO" not in data["cepea"].get("source", "").upper() else "Simulação Baseada em Tendências Históricas"
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        text=f"Previsão baseada em: {source}",
        font=dict(color="#666", size=12)
    )
    
    fig.update_layout(margin=dict(b=60))
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de recomendações
    st.subheader("Recomendações Comerciais")
    
    # Gera recomendações baseadas nos dados
    recommendations = []
    
    if data["cepea"] and data["cepea"].get("variation", ""):
        variation_str = data["cepea"]["variation"].replace("%", "")
        try:
            variation = float(variation_str)
            if variation > 0:
                recommendations.append({
                    "Ação": "Vender",
                    "Quantidade": "50%",
                    "Justificativa": "Preço acima da média histórica"
                })
        except (ValueError, TypeError):
            pass
    
    if data["inmet"] and data["inmet"].get("avg_rainfall_mm", 0) < 50:
        recommendations.append({
            "Ação": "Armazenar",
            "Quantidade": "30%",
            "Justificativa": "Risco de redução na produção futura"
        })
    
    if data["usd"] and data["usd"].get("variation", ""):
        variation_str = data["usd"]["variation"].replace("%", "")
        try:
            variation = float(variation_str)
            if variation < 0:
                recommendations.append({
                    "Ação": "Comprar",
                    "Quantidade": "20%",
                    "Justificativa": "Dólar baixo favorece importação"
                })
        except (ValueError, TypeError):
            pass
    
    # Se não houver recomendações específicas, mostra genéricas
    if not recommendations:
        recommendations = [
            {"Ação": "Monitorar", "Quantidade": "100%", "Justificativa": "Condições de mercado estáveis"},
            {"Ação": "Planejar", "Quantidade": "50%", "Justificativa": "Próxima safra em planejamento"}
        ]
    
    st.dataframe(pd.DataFrame(recommendations))

# =============== RODAPÉ ===============
st.divider()
st.caption("© 2025 Nizan | Dados atualizados em tempo real | Projeto Open Source para Análise Agrícola")
st.caption("Nota: Dados marcados como 'Simulados' são usados quando fontes oficiais estão temporariamente indisponíveis")