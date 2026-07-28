import os
import streamlit as st
import pandas as pd
import requests
from modules.montecarlo_sim_mlb import simular_partido_mlb
from modules.stats_engine_mlb import cargar_datos_mlb

st.set_page_config(page_title="MLB Analytics & Value Betting", layout="wide")

API_KEY = os.environ.get("API_SPORTS_KEY") 
BASE_URL = "https://v3.baseball.api-sports.io"
HEADERS = {'x-apisports-key': API_KEY}
MLB_ID = 1

@st.cache_data(ttl=3600)
def obtener_proximos_juegos_mlb():
    """Obtiene los partidos programados de la MLB."""
    url = f"{BASE_URL}/games"
    params = {"league": str(MLB_ID), "season": "2026", "next": "10"}
    
    try:
        res = requests.get(url, headers=HEADERS, params=params)
        if res.status_code != 200:
            return {}
        datos = res.json().get("response", [])
    except Exception:
        datos = []

    juegos = {}
    for j in datos:
        local = j["teams"]["home"]["name"]
        visita = j["teams"]["away"]["name"]
        game_id = j["id"]
        fecha = j["date"][:10]
        
        llave = f"⚾ {fecha} | {local} vs {visita}"
        juegos[llave] = {
            "local": local,
            "visita": visita,
            "game_id": game_id
        }
    return juegos

st.title("⚾ MLB Monte Carlo Analytics (2026)")
st.write("Simulador cuantitativo de Carreras, Hits y Ponches de Pitchers")

partidos_mlb = obtener_proximos_juegos_mlb()

if not partidos_mlb:
    # Datos de demostración por si la API aún no tiene partidos cargados
    partidos_mlb = {
        "⚾ Demo | New York Yankees vs Boston Red Sox": {"local": "New York Yankees", "visita": "Boston Red Sox", "game_id": 101},
        "⚾ Demo | Los Angeles Dodgers vs San Francisco Giants": {"local": "Los Angeles Dodgers", "visita": "San Francisco Giants", "game_id": 102}
    }

seleccion = st.selectbox("Selecciona un juego de la MLB:", list(partidos_mlb.keys()))
datos_juego = partidos_mlb[seleccion]

st.markdown("---")
st.subheader("🧢 Configuración de Pitchers Abridores")
col_p1, col_p2 = st.columns(2)

with col_p1:
    p_local_nombre = st.text_input(f"Pitcher Abridor ({datos_juego['local']}):", value="Pitcher Local A")
    p_local_era = st.number_input(f"ERA de {p_local_nombre}:", value=3.80, step=0.10)
    p_local_k9 = st.number_input(f"K/9 de {p_local_nombre}:", value=9.2, step=0.10)

with col_p2:
    p_visita_nombre = st.text_input(f"Pitcher Abridor ({datos_juego['visita']}):", value="Pitcher Visita B")
    p_visita_era = st.number_input(f"ERA de {p_visita_nombre}:", value=4.20, step=0.10)
    p_visita_k9 = st.number_input(f"K/9 de {p_visita_nombre}:", value=8.1, step=0.10)

if st.button("Ejecutar Simulación Montecarlo MLB", type="primary"):
    with st.spinner("Procesando 10,000 simulaciones de entradas y pitcheos..."):
        p_loc_stats = {"era": p_local_era, "k9": p_local_k9, "whip": 1.20}
        p_vis_stats = {"era": p_visita_era, "k9": p_visita_k9, "whip": 1.30}
        
        df_hist = cargar_datos_mlb()
        
        resultados = simular_partido_mlb(
            datos_juego["local"], 
            datos_juego["visita"],
            pitcher_local_name=p_local_nombre,
            pitcher_visita_name=p_visita_nombre,
            pitcher_local_stats=p_loc_stats,
            pitcher_visita_stats=p_vis_stats,
            df_historico=df_hist
        )

        st.markdown("### 🏆 Probabilidades de Victoria (Moneyline)")
        m_col1, m_col2 = st.columns(2)
        m_col1.metric(f"Victoria {datos_juego['local']}", f"{resultados['Moneyline']['Gana Local']}%")
        m_col2.metric(f"Victoria {datos_juego['visita']}", f"{resultados['Moneyline']['Gana Visita']}%")

        st.markdown("---")
        st.markdown("### 📊 Mercados Principales Over / Under")
        o_col1, o_col2 = st.columns(2)
        
        over_85 = resultados['Carreras_Totales']['Over 8.5']
        o_col1.metric("Línea: Over 8.5 Carreras", f"{over_85}%", f"Under: {round(100 - over_85, 1)}%")

        over_155_hits = resultados['Hits_Totales']['Over 15.5']
        o_col2.metric("Línea: Over 15.5 Hits Totales", f"{over_155_hits}%", f"Under: {round(100 - over_155_hits, 1)}%")

        st.markdown("---")
        st.markdown("### 🎯 Ponches de Pitchers Abridores (Over/Under 5.5 K's)")
        k_col1, k_col2 = st.columns(2)
        
        k_loc_over = resultados['Ponches_Pitchers'][p_local_nombre]['Over 5.5 K']
        k_col1.metric(f"Ponches {p_local_nombre}", f"Over 5.5 K: {k_loc_over}%", f"Promedio: {resultados['Ponches_Pitchers'][p_local_nombre]['Promedio_K']} K's")

        k_vis_over = resultados['Ponches_Pitchers'][p_visita_nombre]['Over 5.5 K']
        k_col2.metric(f"Ponches {p_visita_nombre}", f"Over 5.5 K: {k_vis_over}%", f"Promedio: {resultados['Ponches_Pitchers'][p_visita_nombre]['Promedio_K']} K's")

        st.markdown("---")
        st.markdown("### 📈 Pronóstico Suavizado en Números Enteros")
        ent = resultados["Pronostico_Enteros"]
        
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            st.markdown("⚽ **Carreras Esperadas**")
            st.write(f"- {datos_juego['local']}: **{ent['Carreras_Local']}** carreras")
            st.write(f"- {datos_juego['visita']}: **{ent['Carreras_Visita']}** carreras")
        with p_col2:
            st.markdown("⚾ **Hits Esperados**")
            st.write(f"- {datos_juego['local']}: **{ent['Hits_Local']}** hits")
            st.write(f"- {datos_juego['visita']}: **{ent['Hits_Visita']}** hits")
        with p_col3:
            st.markdown("🔥 **Ponches Estimados**")
            st.write(f"- {p_local_nombre}: **{ent['Ponches_Pitcher_Local']}** K's")
            st.write(f"- {p_visita_nombre}: **{ent['Ponches_Pitcher_Visita']}** K's")
