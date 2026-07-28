import os
import requests
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURACIÓN ---
API_KEY = os.environ.get("API_SPORTS_KEY") # Asegúrate de tener tu API Key configurada
BASE_URL = "v1.baseball.api-sports.io"
HEADERS = {'x-apisports-key': API_KEY}
MLB_ID = 1 # ID de la MLB en API-Sports
TEMPORADAS = [2020, 2021, 2022, 2023, 2024, 2025] # Temporadas a descargar para el modelo ML y ELO

def crear_directorio_data():
    if not os.path.exists('data'):
        os.makedirs('data')

def descargar_temporada(season):
    print(f"📥 Descargando temporada {season} de MLB...")
    url = f"{BASE_URL}/games"
    params = {
        "league": MLB_ID,
        "season": season
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"❌ Error en la API: {response.status_code}")
            return []
            
        datos = response.json().get("response", [])
        partidos = []
        
        for p in datos:
            # Solo tomar partidos terminados
            if p["status"]["short"] != "FT" and p["status"]["short"] != "AOT":
                continue
                
            try:
                fila = {
                    "Fecha": p["date"][:10],
                    "Temporada": season,
                    "Local": p["teams"]["home"]["name"],
                    "Visitante": p["teams"]["away"]["name"],
                    "Carreras_Local": p["scores"]["home"]["total"],
                    "Carreras_Visita": p["scores"]["away"]["total"],
                    "Hits_Local": p["scores"]["home"]["hits"],
                    "Hits_Visita": p["scores"]["away"]["hits"],
                    "Errores_Local": p["scores"]["home"]["errors"],
                    "Errores_Visita": p["scores"]["away"]["errors"],
                    "Innings_Extra": 1 if p["status"]["short"] == "AOT" else 0
                }
                partidos.append(fila)
            except KeyError:
                # Ignorar partidos con datos incompletos en la API
                continue
                
        print(f"✅ Temporada {season} procesada: {len(partidos)} partidos.")
        return partidos
        
    except Exception as e:
        print(f"❌ Error al procesar la temporada {season}: {e}")
        return []

def generar_historico():
    crear_directorio_data()
    todos_los_partidos = []
    
    for temp in TEMPORADAS:
        partidos_temp = descargar_temporada(temp)
        todos_los_partidos.extend(partidos_temp)
        # Pausa para no saturar la API
        time.sleep(2)
        
    if not todos_los_partidos:
        print("⚠️ No se pudo descargar ningún dato.")
        return
        
    # Crear DataFrame y limpiar
    df = pd.DataFrame(todos_los_partidos)
    df = df.dropna()
    
    # Ordenar cronológicamente
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df = df.sort_values(by='Fecha').reset_index(drop=True)
    
    # Guardar CSV
    ruta_csv = 'data/historico_mlb.csv'
    df.to_csv(ruta_csv, index=False)
    print(f"🎉 ¡Éxito! Base de datos guardada en '{ruta_csv}' con {len(df)} registros.")

if __name__ == "__main__":
    if not API_KEY:
        print("🚨 ERROR: No se encontró la API_SPORTS_KEY en las variables de entorno.")
    else:
        print("🚀 Iniciando generador de base de datos MLB...")
        generar_historico()
