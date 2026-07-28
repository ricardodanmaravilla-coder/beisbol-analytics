import numpy as np
import pandas as pd
from modules.stats_engine_mlb import calcular_expectativa_mlb

def simular_partido_mlb(local, visita, df_historico, elo_local=None, elo_visita=None, num_simulaciones=1000000, linea_carreras=8.5, linea_hits=15.5):
    
    # ELO Real de contingencia si no se pasa desde App
    if elo_local is None or elo_visita is None:
        try:
            from modules.elo_engine_mlb import SistemaEloMLB
            tabla_elo = SistemaEloMLB().calcular_historico(df_historico)
            elo_local = float(tabla_elo.loc[tabla_elo['Equipo'] == local, 'ELO_Rating'].values[0])
            elo_visita = float(tabla_elo.loc[tabla_elo['Equipo'] == visita, 'ELO_Rating'].values[0])
        except:
            elo_local, elo_visita = 1500.0, 1500.0

    # Extraer lambdas 100% reales calculadas del CSV
    exp = calcular_expectativa_mlb(local, visita, df_historico)
    c_l_exp = exp["lambda_carreras_local"]
    c_v_exp = exp["lambda_carreras_visita"]
    h_l_exp = exp["lambda_hits_local"]
    h_v_exp = exp["lambda_hits_visita"]

    # Ajuste fino matemático por diferencia real de ELO
    factor_elo_carreras = (elo_local - elo_visita) / 400.0
    c_l_exp = max(0.1, c_l_exp + (factor_elo_carreras * 0.40)) # Mayor impacto del ELO en Béisbol
    c_v_exp = max(0.1, c_v_exp - (factor_elo_carreras * 0.40))

    # Simulaciones de Montecarlo
    carreras_loc_sim = np.random.poisson(c_l_exp, num_simulaciones)
    carreras_vis_sim = np.random.poisson(c_v_exp, num_simulaciones)
    carreras_tot_sim = carreras_loc_sim + carreras_vis_sim

    hits_loc_sim = np.random.poisson(h_l_exp, num_simulaciones)
    hits_vis_sim = np.random.poisson(h_v_exp, num_simulaciones)
    hits_tot_sim = hits_loc_sim + hits_vis_sim

    # Resolver empates (El béisbol continúa en extra innings)
    # Redistribuimos los empates 50/50 para forzar un ganador final
    wins_local = np.sum(carreras_loc_sim > carreras_vis_sim)
    wins_visita = np.sum(carreras_loc_sim < carreras_vis_sim)
    empates = np.sum(carreras_loc_sim == carreras_vis_sim)
    
    prob_local = round(((wins_local + empates/2) / num_simulaciones) * 100, 1)
    prob_visita = round(((wins_visita + empates/2) / num_simulaciones) * 100, 1)

    over_c = round((np.sum(carreras_tot_sim > linea_carreras) / num_simulaciones) * 100, 1)
    over_h = round((np.sum(hits_tot_sim > linea_hits) / num_simulaciones) * 100, 1)

    return {
        "Moneyline": {
            "Gana Local": prob_local,
            "Gana Visita": prob_visita
        },
        "Mercados": {
            f"Over {linea_carreras} Carreras": over_c,
            f"Under {linea_carreras} Carreras": round(100.0 - over_c, 1),
            f"Over {linea_hits} Hits": over_h,
            f"Under {linea_hits} Hits": round(100.0 - over_h, 1)
        },
        "Individuales": {
            "Carreras_Local": int(round(c_l_exp)),
            "Carreras_Visita": int(round(c_v_exp)),
            "Hits_Local": int(round(h_l_exp)),
            "Hits_Visita": int(round(h_v_exp))
        }
    }
