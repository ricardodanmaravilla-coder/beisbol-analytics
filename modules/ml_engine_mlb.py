import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

class PredictorML_MLB:
    def __init__(self):
        self.model_ganador = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model_carreras = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model_hits = RandomForestRegressor(n_estimators=100, random_state=42)
        self.encoder_equipos = LabelEncoder()
        self.is_trained = False

    def entrenar(self, df_historico):
        try:
            df = df_historico.copy()
            df['Local'] = df['Local'].astype(str).str.strip()
            df['Visitante'] = df['Visitante'].astype(str).str.strip()
            
            todos_equipos = pd.concat([df['Local'], df['Visitante']]).unique()
            self.encoder_equipos.fit(todos_equipos)
            
            df['Local_Encoded'] = self.encoder_equipos.transform(df['Local'])
            df['Visita_Encoded'] = self.encoder_equipos.transform(df['Visitante'])
            
            # Ganador: 1 si gana Local, 0 si gana Visita
            df['Target_Ganador'] = (df['Carreras_Local'] > df['Carreras_Visita']).astype(int)
            df['Total_Carreras'] = df['Carreras_Local'] + df['Carreras_Visita']
            df['Total_Hits'] = df['Hits_Local'] + df['Hits_Visita']
            
            X = df[['Local_Encoded', 'Visita_Encoded']].fillna(0)
            
            self.model_ganador.fit(X, df['Target_Ganador'])
            self.model_carreras.fit(X, df['Total_Carreras'])
            self.model_hits.fit(X, df['Total_Hits'])
            
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Error ML MLB: {e}")
            return False

    def predecir_juego(self, equipo_local, equipo_visita):
        if not self.is_trained:
            return {}
            
        try:
            loc_enc = self.encoder_equipos.transform([equipo_local])[0]
            vis_enc = self.encoder_equipos.transform([equipo_visita])[0]
            
            X_pred = pd.DataFrame([[loc_enc, vis_enc]], columns=['Local_Encoded', 'Visita_Encoded'])
            
            probs = self.model_ganador.predict_proba(X_pred)[0]
            carreras_ml = float(self.model_carreras.predict(X_pred)[0])
            hits_ml = float(self.model_hits.predict(X_pred)[0])
            
            return {
                "Prob_Visita": round(probs[0] * 100, 1),
                "Prob_Local": round(probs[1] * 100, 1),
                "Carreras_Totales": round(carreras_ml, 2),
                "Hits_Totales": round(hits_ml, 2)
            }
        except Exception:
            return {}
