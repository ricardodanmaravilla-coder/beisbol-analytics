import os
import pandas as pd
import numpy as np

def cargar_datos_mlb():
    url_github_raw = 'https://raw.githubusercontent.com/ricardodanmaravilla-coder/beisbol-analytics/main/data/historico_mlb.csv'
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
            df = pd.read_csv(url_github_raw)
        except Exception as e:
            raise FileNotFoundError(f"Error cargando histórico MLB: {e}")

    df['Fecha'] = pd.to_datetime(df['Fecha'])
    fecha_referencia = df['Fecha'].max()
    df['Dias_Antiguedad'] = (fecha_referencia - df['Fecha']).dt.days
    df['Peso'] = 0.5 ** (df['Dias_Antiguedad'] / 365.0) # Mayor peso a juegos recientes
    
    return df

def media_ponderada(valores, pesos):
    df_temp = pd.DataFrame({'val': valores, 'peso': pesos}).dropna()
    if len(df_temp) == 0 or df_temp['peso'].sum() == 0: return 0
    return np.average(df_temp['val'], weights=df_temp['peso'])

def calcular_ratings_mlb(df):
    pesos = df['Peso']
    media_c_loc = media_ponderada(df['Carreras_Local'], pesos)
    media_c_vis = media_ponderada(df['Carreras_Visita'], pesos)
    media_h_loc = media_ponderada(df['Hits_Local'], pesos)
    media_h_vis = media_ponderada(df['Hits_Visita'], pesos)
    
    return media_c_loc, media_c_vis, media_h_loc, media_h_vis

def obtener_fuerza_equipo(df, equipo, promedios_liga):
    df_local = df[df['Local'] == equipo]
    df_visita = df[df['Visitante'] == equipo]
    
    if len(df_local) == 0 or len(df_visita) == 0:
        return None

    m_c_l, m_c_v, m_h_l, m_h_v = promedios_liga

    # Fuerza Ofensiva y Defensiva en Carreras
    att_carreras_loc = media_ponderada(df_local['Carreras_Local'], df_local['Peso']) / m_c_l
    def_carreras_loc = media_ponderada(df_local['Carreras_Visita'], df_local['Peso']) / m_c_v
    att_carreras_vis = media_ponderada(df_visita['Carreras_Visita'], df_visita['Peso']) / m_c_v
    def_carreras_vis = media_ponderada(df_visita['Carreras_Local'], df_visita['Peso']) / m_c_l

    # Fuerza Ofensiva y Defensiva en Hits
    att_hits_loc = media_ponderada(df_local['Hits_Local'], df_local['Peso']) / m_h_l
    def_hits_loc = media_ponderada(df_local['Hits_Visita'], df_local['Peso']) / m_h_v
    att_hits_vis = media_ponderada(df_visita['Hits_Visita'], df_visita['Peso']) / m_h_v
    def_hits_vis = media_ponderada(df_visita['Hits_Local'], df_visita['Peso']) / m_h_l

    return {
        "Att_Carreras_L": att_carreras_loc, "Def_Carreras_L": def_carreras_loc,
        "Att_Carreras_V": att_carreras_vis, "Def_Carreras_V": def_carreras_vis,
        "Att_Hits_L": att_hits_loc, "Def_Hits_L": def_hits_loc,
        "Att_Hits_V": att_hits_vis, "Def_Hits_V": def_hits_vis
    }

def calcular_expectativa_mlb(local, visita, df_historico):
    promedios = calcular_ratings_mlb(df_historico)
    stats_l = obtener_fuerza_equipo(df_historico, local, promedios)
    stats_v = obtener_fuerza_equipo(df_historico, visita, promedios)
    
    if stats_l is None or stats_v is None:
        raise ValueError(f"Faltan datos históricos reales para {local} o {visita}.")
    
    # Lambda = Ataque Local * Defensa Visita * Promedio Liga
    lambda_carreras_l = stats_l["Att_Carreras_L"] * stats_v["Def_Carreras_V"] * promedios[0]
    lambda_carreras_v = stats_v["Att_Carreras_V"] * stats_l["Def_Carreras_L"] * promedios[1]
    
    lambda_hits_l = stats_l["Att_Hits_L"] * stats_v["Def_Hits_V"] * promedios[2]
    lambda_hits_v = stats_v["Att_Hits_V"] * stats_l["Def_Hits_L"] * promedios[3]

    return {
        "lambda_carreras_local": max(0.5, lambda_carreras_l),
        "lambda_carreras_visita": max(0.5, lambda_carreras_v),
        "lambda_hits_local": max(1.0, lambda_hits_l),
        "lambda_hits_visita": max(1.0, lambda_hits_v)
    }
