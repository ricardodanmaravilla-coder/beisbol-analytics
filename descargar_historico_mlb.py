import os
import requests
import pandas as pd
import time

# --- CONFIGURACIÓN ---
API_KEY = os.environ.get("API_SPORTS_KEY")
BASE_URL = "https://v1.baseball.api-sports.io"
HEADERS = {'x-apisports-key': API_KEY}
MLB_ID = 1 
TEMPORADAS = [2023, 2024, 2025] 

def crear_directorio_data():
    if not os.path.exists('data'):
        os.makedirs('data')

def descargar_temporada(season):
    print(f"\n📥 Solicitando temporada {season} de MLB a la API...")
    url = f"{BASE_URL}/games"
    params = {
        "league": MLB_ID,
        "season": season
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        
        # 1. Validar error HTTP directo
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return []
            
        data = response.json()
        
        # 2. Validar errores internos reportados por API-Sports (Ej. "no subscription")
        api_errors = data.get("errors", [])
        if api_errors:
            print(f"🚨 LA API RECHAZÓ LA PETICIÓN. Motivo: {api_errors}")
            return []
            
        resultados = data.get("response", [])
        print(f"⚾ La API devolvió {len(resultados)} juegos. Procesando y filtrando...")
        
        partidos = []
        for p in resultados:
            # Extraer status de forma segura
            status = p.get("status", {}).get("short", "")
            if status not in ["FT", "AOT"]:
                continue
                
            try:
                scores = p.get("scores", {})
                home_scores = scores.get("home", {})
                away_scores = scores.get("away", {})
                
                # Extraer datos usando .get() para que nunca colapse si falta un número
                c_local = home_scores.get("total", 0)
                c_visita = away_scores.get("total", 0)
                
                # Descartar si el total es None (partido cancelado o sin info)
                if c_local is None or c_visita is None:
                    continue

                fila = {
                    "Fecha": p.get("date", "")[:10],
                    "Temporada": season,
                    "Local": p.get("teams", {}).get("home", {}).get("name", "Unknown"),
                    "Visitante": p.get("teams", {}).get("away", {}).get("name", "Unknown"),
                    "Carreras_Local": c_local,
                    "Carreras_Visita": c_visita,
                    "Hits_Local": home_scores.get("hits", 0) or 0,
                    "Hits_Visita": away_scores.get("hits", 0) or 0,
                    "Errores_Local": home_scores.get("errors", 0) or 0,
                    "Errores_Visita": away_scores.get("errors", 0) or 0,
                    "Innings_Extra": 1 if status == "AOT" else 0
                }
                partidos.append(fila)
                
            except Exception as e:
                print(f"⚠️ Partido ignorado por formato inesperado. Detalle: {e}")
                continue
                
        print(f"✅ Temporada {season} filtrada con éxito: {len(partidos)} partidos reales obtenidos.")
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
        time.sleep(2) # Pausa estricta para evitar bloqueos por límite de velocidad
        
    if not todos_los_partidos:
        print("\n⚠️ ATENCIÓN: No se obtuvieron datos válidos de la API. El archivo CSV NO fue generado.")
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
        print("🚨 ERROR FATAL: La llave API_SPORTS_KEY no está configurada en los Secrets de GitHub.")
    else:
        print("🚀 Iniciando descarga del histórico de MLB...")
        generar_historico()
