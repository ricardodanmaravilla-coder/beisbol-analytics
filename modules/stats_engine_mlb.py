import os
import pandas as pd
import numpy as np

# Promedios estándar MLB (utilizados como base si falta algún dato)
PROMEDIOS_MLB = {
    "carreras_por_juego": 4.50,
    "hits_por_juego": 8.20,
    "era_pitcher": 4.10,
    "whip_pitcher": 1.28,
    "k9_pitcher": 8.50,      # Ponches por cada 9 entradas
    "k_pct_bateo": 0.22      # 22% de ponches por turno al bate
}

def cargar_datos_mlb():
    """Carga el archivo histórico o base de datos de MLB desde GitHub RAW o local."""
    url_raw = 'https://raw.githubusercontent.com/ricardodanmaravilla-coder/beisbol-analytics/main/data/historico_mlb.csv'
    rutas_locales = ['data/historico_mlb.csv', 'historico_mlb.csv']
    
    df = None
    for r in rutas_locales:
        if os.path.exists(r):
            try:
                df = pd.read_csv(r)
                break
            except Exception:
                pass
                
    if df is None:
        try:
            df = pd.read_csv(url_raw)
        except Exception:
            # DataFrame sintético/base si no existe aún el archivo histórico
            df = pd.DataFrame()
            
    return df

def calcular_expectativa_beisbol(local, visita, pitcher_local_stats=None, pitcher_visita_stats=None, df_historico=None):
    """
    Combina la efectividad del Pitcher Abridor vs. el Bateo Histórico del rival
    para calcular los lambdas (Poisson) de Carreras, Hits y Ponches.
    """
    # 1. Estadísticas de Pitchers (Valores por defecto si no vienen de la API/DataFrame)
    p_loc_era = pitcher_local_stats.get("era", PROMEDIOS_MLB["era_pitcher"]) if pitcher_local_stats else PROMEDIOS_MLB["era_pitcher"]
    p_loc_k9 = pitcher_local_stats.get("k9", PROMEDIOS_MLB["k9_pitcher"]) if pitcher_local_stats else PROMEDIOS_MLB["k9_pitcher"]
    p_loc_whip = pitcher_local_stats.get("whip", PROMEDIOS_MLB["whip_pitcher"]) if pitcher_local_stats else PROMEDIOS_MLB["whip_pitcher"]

    p_vis_era = pitcher_visita_stats.get("era", PROMEDIOS_MLB["era_pitcher"]) if pitcher_visita_stats else PROMEDIOS_MLB["era_pitcher"]
    p_vis_k9 = pitcher_visita_stats.get("k9", PROMEDIOS_MLB["k9_pitcher"]) if pitcher_visita_stats else PROMEDIOS_MLB["k9_pitcher"]
    p_vis_whip = pitcher_visita_stats.get("whip", PROMEDIOS_MLB["whip_pitcher"]) if pitcher_visita_stats else PROMEDIOS_MLB["whip_pitcher"]

    # 2. Factores de Bateo por Equipo
    carreras_base_local = PROMEDIOS_MLB["carreras_por_juego"]
    carreras_base_visita = PROMEDIOS_MLB["carreras_por_juego"]
    
    hits_base_local = PROMEDIOS_MLB["hits_por_juego"]
    hits_base_visita = PROMEDIOS_MLB["hits_por_juego"]

    # Cruce: Bateo Local vs Pitcher Visitante
    factor_era_visita = p_vis_era / PROMEDIOS_MLB["era_pitcher"]
    lambda_carreras_local = carreras_base_local * factor_era_visita * 1.03  # 3% ventaja localía
    
    # Cruce: Bateo Visitante vs Pitcher Local
    factor_era_local = p_loc_era / PROMEDIOS_MLB["era_pitcher"]
    lambda_carreras_visita = carreras_base_visita * factor_era_local

    # Expectativa de Hits (Función del WHIP del Pitcher)
    lambda_hits_local = hits_base_local * (p_vis_whip / PROMEDIOS_MLB["whip_pitcher"])
    lambda_hits_visita = hits_base_visita * (p_loc_whip / PROMEDIOS_MLB["whip_pitcher"])

    # Expectativa de Ponches (Ks) del Pitcher (Asumiendo 5.2 innings promedio de trabajo)
    innings_estimados = 5.2
    lambda_ponches_p_local = (p_loc_k9 / 9.0) * innings_estimados
    lambda_ponches_p_visita = (p_vis_k9 / 9.0) * innings_estimados

    return {
        "lambda_carreras_local": max(0.5, lambda_carreras_local),
        "lambda_carreras_visita": max(0.5, lambda_carreras_visita),
        "lambda_hits_local": max(1.0, lambda_hits_local),
        "lambda_hits_visita": max(1.0, lambda_hits_visita),
        "lambda_ponches_p_local": max(1.0, lambda_ponches_p_local),
        "lambda_ponches_p_visita": max(1.0, lambda_ponches_p_visita)
    }
