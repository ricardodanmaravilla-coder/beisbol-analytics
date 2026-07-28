import os
import requests
import pandas as pd
import time

# --- CONFIGURACIÓN ---
API_KEY = os.environ.get("API_SPORTS_KEY")
BASE_URL = "https://v1.baseball.api-sports.io"  # URL correcta corregida a v1
HEADERS = {'x-apisports-key': API_KEY}
MLB_ID = 1  # ID de la MLB en API-Sports
TEMPORADAS = [2021, 2022, 2023, 2024, 2025, 2026] 

def crear_directorio_data():
    if not os.path.exists('data'):
        os.makedirs('data')

def descargar_temporada(season):
    print(f"\n📥 Solicitando temporada {season} de MLB a {BASE_URL}/games...")
    url = f"{BASE_URL}/games"
    params = {
        "league": MLB_ID,
        "season": season
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return []
            
        data = response.json()
        
        api_errors = data.get("errors", [])
        if api_errors:
            print(f"🚨 LA API RECHAZÓ LA PETICIÓN. Motivo: {api_errors}")
            return []
            
        resultados = data.get("response", [])
        print(f"⚾ La API devolvió {len(resultados)} registros para el año {season}.")
        
        partidos = []
        for p in resultados:
            # En béisbol, los partidos finalizados suelen venir como 'FT' o 'AOT'
            status = p.get("status", {}).get("short", "")
            if status not in ["FT", "AOT"]:
                continue
                
            try:
                scores = p.get("scores", {})
                home_scores = scores.get("home", {})
                away_scores = scores.get("away", {})
                
                c_local = home_scores.get("total")
                c_visita = away_scores.get("total")
                
                if c_local is None or c_visita is None:
                    continue

                fila = {
                    "Fecha": p.get("date", "")[:10],
                    "Temporada": season,
                    "Local": p.get("teams", {}).get("home", {}).get("name", "Unknown"),
                    "Visitante": p.get("teams", {}).get("away", {}).get("name", "Unknown"),
                    "Carreras_Local": int(c_local),
                    "Carreras_Visita": int(c_visita),
                    "Hits_Local": int(home_scores.get("hits") or 0),
                    "Hits_Visita": int(away_scores.get("hits") or 0),
                    "Errores_Local": int(home_scores.get("errors") or 0),
                    "Errores_Visita": int(away_scores.get("errors") or 0),
                    "Innings_Extra": 1 if status == "AOT" else 0
                }
                partidos.append(fila)
                
            except Exception as e:
                continue
                
        print(f"✅ Temporada {season} procesada con éxito: {len(partidos)} partidos válidos.")
        return partidos
        
    except Exception as e:
        print(f"❌ Error crítico conectando con la API en la temporada {season}: {e}")
        return []

def generar_historico():
    crear_directorio_data()
    todos_los_partidos = []
    
    for temp in TEMPORADAS:
        partidos_temp = descargar_temporada(temp)
        todos_los_partidos.extend(partidos_temp)
        time.sleep(2) 
        
    if not todos_los_partidos:
        print("\n⚠️ ATENCIÓN: No se recolectaron datos. El archivo CSV NO fue generado.")
        return
        
    df = pd.DataFrame(todos_los_partidos)
    df = df.dropna()
    
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values(by='Fecha').reset_index(drop=True)
    
    ruta_csv = 'data/historico_mlb.csv'
    df.to_csv(ruta_csv, index=False)
    print(f"\n🎉 ¡ÉXITO TOTAL! Archivo '{ruta_csv}' creado y guardado con {len(df)} registros.")

if __name__ == "__main__":
    if not API_KEY:
        print("🚨 ERROR FATAL: La llave API_SPORTS_KEY no está configurada.")
    else:
        print("🚀 Iniciando descarga del histórico de MLB con v1.baseball...")
        generar_historico()
