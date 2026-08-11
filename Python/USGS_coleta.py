import requests
import pandas as pd
import time

def get_quakes_chunk(start_str, end_str, minmag=0):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    all_records = []
    offset = 1

    while True:
        params = {
            "format": "geojson",
            "starttime": start_str,
            "endtime": end_str,
            "minmagnitude": minmag,
            "limit": 20000,
            "offset": offset,
            "orderby": "time"
        }
        data = None
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
                else:
                    print(f"  [Aviso] HTTP {response.status_code} em {start_str} offset {offset}, tentando novamente...")
                    time.sleep(2)
            except Exception as e:
                print(f"  [Erro] {e}, tentando novamente...")
                time.sleep(2)

        if not data:
            print(f"  [Falha] Não foi possível obter dados para {start_str} até {end_str} (offset {offset})")
            break

        features = data.get("features", [])
        if not features:
            break

        for f in features:
            props = f["properties"]
            coords = f["geometry"]["coordinates"]
            all_records.append({
                "time": pd.to_datetime(props["time"], unit="ms"),
                "place": props["place"],
                "magnitude": props["mag"],
                "longitude": coords[0],
                "latitude": coords[1],
                "depth_km": coords[2]
            })

        if len(features) < 20000:
            break

        offset += 20000

    return pd.DataFrame(all_records)

def collect_all_quakes(start, end, minmag=0):
    dates = pd.date_range(start=start, end=end, freq="MS")
    frames = []
    
    for i in range(len(dates)):
        chunk_start = dates[i].strftime("%Y-%m-%d")
        if i + 1 < len(dates):
            chunk_end = dates[i + 1].strftime("%Y-%m-%d")
        else:
            chunk_end = end
            
        print(f"Coletando terremotos de {chunk_start} até {chunk_end}...")
        df_chunk = get_quakes_chunk(chunk_start, chunk_end, minmag=minmag)
        if not df_chunk.empty:
            frames.append(df_chunk)
        time.sleep(0.5)

    if frames:
        df_concat = pd.concat(frames, ignore_index=True)
        return df_concat.drop_duplicates().reset_index(drop=True)
    return pd.DataFrame()

if __name__ == "__main__":
    import os
    # Coletar dados de 2020-01-01 até 2026-08-18
    df_final = collect_all_quakes("2020-01-01", "2026-08-18", minmag=0)

    # Garantir pasta Data
    out_dir = "../Data" if os.path.basename(os.getcwd()) == "Python" else "Data"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "terremotos_2020_2026.csv")

    # Salvar em CSV
    df_final.to_csv(out_path, index=False)
    print(f"\nColeta finalizada com sucesso! Gravado em '{out_path}'")
    print("Total de registros coletados:", df_final.shape[0])

