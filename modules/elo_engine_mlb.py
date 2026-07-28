import pandas as pd

class SistemaEloMLB:
    def __init__(self, k_factor=20, base_rating=1500):
        # K menor que en fútbol porque en béisbol hay más partidos por temporada (162)
        self.k_factor = k_factor
        self.base_rating = base_rating

    def calcular_historico(self, df_historico):
        if df_historico is None or df_historico.empty:
            return pd.DataFrame(columns=['Equipo', 'ELO_Rating'])

        df = df_historico.copy()
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df = df.sort_values('Fecha').reset_index(drop=True)

        ratings = {}
        
        def get_rating(eq):
            if eq not in ratings:
                ratings[eq] = self.base_rating
            return ratings[eq]

        for idx, row in df.iterrows():
            local = str(row['Local']).strip()
            visita = str(row['Visitante']).strip()
            
            c_l = row.get('Carreras_Local', 0)
            c_v = row.get('Carreras_Visita', 0)
            
            if pd.isna(c_l) or pd.isna(c_v):
                continue

            elo_l = get_rating(local)
            elo_v = get_rating(visita)

            # Ventaja de casa ligera en MLB (~ 24 puntos de ELO)
            elo_l_adj = elo_l + 24

            exp_l = 1 / (1 + 10 ** ((elo_v - elo_l_adj) / 400))
            exp_v = 1 / (1 + 10 ** ((elo_l_adj - elo_v) / 400))

            # Resultado (Béisbol no tiene empates reales a final de juego)
            if c_l > c_v:
                s_l, s_v = 1.0, 0.0
            else:
                s_l, s_v = 0.0, 1.0

            ratings[local] = elo_l + self.k_factor * (s_l - exp_l)
            ratings[visita] = elo_v + self.k_factor * (s_v - exp_v)

        data_ranking = [{'Equipo': eq, 'ELO_Rating': round(float(r), 1)} for eq, r in ratings.items()]
        return pd.DataFrame(data_ranking).sort_values(by='ELO_Rating', ascending=False).reset_index(drop=True)
