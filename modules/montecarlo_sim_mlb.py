import numpy as np
import pandas as pd
from modules.stats_engine_mlb import calcular_expectativa_beisbol

def simular_partido_mlb(local, visita, pitcher_local_name="Abridor Local", pitcher_visita_name="Abridor Visita", 
                         pitcher_local_stats=None, pitcher_visita_stats=None, 
                         df_historico=None, num_simulaciones=1000000, linea_carreras=8.5, linea_ponches=5.5):
    """
    Simulación Montecarlo de Béisbol (Carreras totales O/U 8.5, Hits, Ponches por Pitcher).
    """
    exp = calcular_expectativa_beisbol(local, visita, pitcher_local_stats, pitcher_visita_stats, df_historico)

    # 1. Simulaciones Poisson
    carreras_loc_sim = np.random.poisson(exp["lambda_carreras_local"], num_simulaciones)
    carreras_vis_sim = np.random.poisson(exp["lambda_carreras_visita"], num_simulaciones)
    carreras_totales_sim = carreras_loc_sim + carreras_vis_sim

    hits_loc_sim = np.random.poisson(exp["lambda_hits_local"], num_simulaciones)
    hits_vis_sim = np.random.poisson(exp["lambda_hits_visita"], num_simulaciones)
    hits_totales_sim = hits_loc_sim + hits_vis_sim

    ponches_p_loc_sim = np.random.poisson(exp["lambda_ponches_p_local"], num_simulaciones)
    ponches_p_vis_sim = np.random.poisson(exp["lambda_ponches_p_visita"], num_simulaciones)

    # 2. Moneyline (Ganador Directo)
    wins_local = np.sum(carreras_loc_sim > carreras_vis_sim)
    wins_visita = np.sum(carreras_loc_sim < carreras_vis_sim)
    empates = np.sum(carreras_loc_sim == carreras_vis_sim) # En béisbol no hay empates, repartir simulación
    
    prob_local = round(((wins_local + empates/2) / num_simulaciones) * 100, 1)
    prob_visita = round(((wins_visita + empates/2) / num_simulaciones) * 100, 1)

    # 3. Mercados Over / Under
    over_carreras = round((np.sum(carreras_totales_sim > linea_carreras) / num_simulaciones) * 100, 1)
    under_carreras = round(100.0 - over_carreras, 1)

    linea_hits_default = 15.5
    over_hits = round((np.sum(hits_totales_sim > linea_hits_default) / num_simulaciones) * 100, 1)
    under_hits = round(100.0 - over_hits, 1)

    over_k_loc = round((np.sum(ponches_p_loc_sim > linea_ponches) / num_simulaciones) * 100, 1)
    under_k_loc = round(100.0 - over_k_loc, 1)

    over_k_vis = round((np.sum(ponches_p_vis_sim > linea_ponches) / num_simulaciones) * 100, 1)
    under_k_vis = round(100.0 - over_k_vis, 1)

    return {
        "Moneyline": {
            "Gana Local": prob_local,
            "Gana Visita": prob_visita
        },
        "Carreras_Totales": {
            f"Over {linea_carreras}": over_carreras,
            f"Under {linea_carreras}": under_carreras
        },
        "Hits_Totales": {
            f"Over {linea_hits_default}": over_hits,
            f"Under {linea_hits_default}": under_hits
        },
        "Ponches_Pitchers": {
            pitcher_local_name: {
                f"Over {linea_ponches} K": over_k_loc,
                f"Under {linea_ponches} K": under_k_loc,
                "Promedio_K": round(exp["lambda_ponches_p_local"], 1)
            },
            pitcher_visita_name: {
                f"Over {linea_ponches} K": over_k_vis,
                f"Under {linea_ponches} K": under_k_vis,
                "Promedio_K": round(exp["lambda_ponches_p_visita"], 1)
            }
        },
        "Pronostico_Enteros": {
            "Carreras_Local": int(round(exp["lambda_carreras_local"])),
            "Carreras_Visita": int(round(exp["lambda_carreras_visita"])),
            "Hits_Local": int(round(exp["lambda_hits_local"])),
            "Hits_Visita": int(round(exp["lambda_hits_visita"])),
            "Ponches_Pitcher_Local": int(round(exp["lambda_ponches_p_local"])),
            "Ponches_Pitcher_Visita": int(round(exp["lambda_ponches_p_visita"]))
        }
    }
