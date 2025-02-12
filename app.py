import dash
from dash import dcc, html
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import requests
import random
from dash.dependencies import Input, Output, State, ALL
import os
from dotenv import load_dotenv

# Variablen aus der .env-Datei laden
# Cargar las variables del archivo .env

load_dotenv()

# Anmeldeinformationen aus Umgebungsvariablen abrufen
# Obtener credenciales desde variables de entorno

USERNAME = os.getenv("OPENSKY_USERNAME")
PASSWORD = os.getenv("OPENSKY_PASSWORD")

# Flüge mit Flugbahn von OpenSky API mit Datenvalidierung abrufen
# Obtener vuelos con trayectoria desde OpenSky API con validación de datos

def get_flights_with_tracks():
    url = "https://opensky-network.org/api/states/all"
    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=5)
        response.raise_for_status()
        data = response.json()
        flights = data.get("states", [])
        valid_flights = {}

        for flight in flights:
            if all([
                flight[0],  # ICAO24 (ID único)
                flight[1],  # Callsign
                flight[2],  # País de origen
                flight[5] is not None,  # Longitud
                flight[6] is not None,  # Latitud
                flight[7] is not None,  # Altitud
                flight[9] is not None  # Velocidad
            ]):
                valid_flights[flight[0]] = {
                    "icao24": flight[0],
                    "callsign": flight[1].strip() if flight[1] else "N/A",
                    "country": flight[2].strip() if flight[2] else "N/A",
                    "longitude": flight[5],
                    "latitude": flight[6],
                    "altitude": flight[7],
                    "velocity": flight[9]
                }

        if not valid_flights:
            return {}, len(flights)

        sample_size = min(max(10, len(valid_flights) // 10), len(valid_flights))
        sampled_flights = {k: valid_flights[k] for k in random.sample(list(valid_flights.keys()), sample_size)}

        return sampled_flights, len(flights)
    except requests.RequestException:
        return {}, 0

# Funktionen für metrische Berechnungen
# Funciones para cálculos de métricas

def estimate_fuel_and_co2(distance_km, num_flights=1, fuel_rate_kg_km=2.5, co2_rate_kg_kgfuel=3.16):
    total_fuel = num_flights * distance_km * fuel_rate_kg_km
    total_co2 = total_fuel * co2_rate_kg_kgfuel
    return total_fuel, total_co2

def estimate_solar_energy(num_flights=1, panel_area_m2=50, efficiency=0.2, solar_irradiance=1000):
    return num_flights * panel_area_m2 * efficiency * solar_irradiance  

def estimate_wind_energy(num_flights=1, air_speed=250, efficiency=0.3, rotor_area=1.5):
    air_density = 1.225  
    return num_flights * 0.5 * air_density * rotor_area * (air_speed**3) * efficiency  

# Erstellen Sie die Dash-Anwendung.
# Crear la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Flugverfolgung - OpenSky API"

app.layout = dbc.Container([
    
    # Dashboard-Titel
    # Título del Dashboard
    html.H1("Flugverfolgung - OpenSky API", className="text-center mt-3"),
    
    # Informationen über die Anzahl der geladenen Flüge
    # Información de cantidad de vuelos cargados
    html.Div(id="flight-count-info", className="text-center mb-3", style={"font-size": "14px"}),

    # Schaltfläche zum Laden von Flügen
    # Botón para cargar vuelos
    dbc.Row([
        dbc.Col(dbc.Button("Flüge laden", id="load-flights-btn", color="primary", className="mb-3 text-white"), width=2),
    ]),
    
    # Kartenausschnitt und Metriken
    # Sección del Mapa y Métricas
    dbc.Row([
        # Flugkarte
        # Mapa de Vuelos
        dbc.Col(dl.Map(id="flight-map", children=[
            dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
        ], 
        style={"width": "100%", "height": "600px"}, 
        center=[20, 0], 
        zoom=2,  
        minZoom=2,  
        maxBounds=[[-85, -180], [85, 180]]), width=9),
        
        # Abschnitt Metriken und Flugdaten
        # Sección de Métricas y Datos de Vuelo
        dbc.Col([
            html.Div([
                html.H5("Globale Metriken", className="text-center mt-0"),
                html.Div(id="global-stats", className="text-right bg-light p-3 border rounded mb-3", style={"font-size": "12px"}),

                html.H5("Mögliche alternative Energien (Global)", className="text-center mt-0"),
                html.Div(id="global-alternative-energy", className="text-right bg-light p-3 border rounded mb-3", style={"font-size": "12px"}),

                html.H5("Fluginformationen", className="text-center mt-0"),
                html.Div(id="flight-info", className="text-right bg-light p-3 border rounded", style={"font-size": "12px"}),

                html.H5("Mögliche alternative Energien (Flug)", className="text-center mt-0"),
                html.Div(id="alternative-energy", className="text-right bg-light p-3 border rounded mb-3", style={"font-size": "12px"}),
            ], style={"position": "absolute", "top": "0", "right": "0", "width": "25%"})
        ])
    ]),

    # Fußzeile mit Informationen und Referenzen
    # Footer con Información y Referencias
    html.Footer([
        html.P(
            "Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic und Matthias Wilhelm. "
            "„Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research“. "
            "In Proceedings of the 13th IEEE/ACM International Symposium on Information Processing in Sensor Networks (IPSN), "
            "Seiten 83-94, April 2014.", 
            className="text-center mt-4", 
            style={"font-size": "12px"}
        ),
        html.P([
            "Dieses Dashboard ist Teil des Repositories ",
            html.A("Flugkarte_co2", href="https://github.com/kentvalerach/Flugkarte_co2", target="_blank"),
            " von Kent Valera Chirinos, und ist eine unabhängige Studie, die die Implementierung alternativer Energien in Flugzeugen "
            "sowie den Übergang zur Nutzung alternativer Kraftstoffe für Luftfahrzeuge untersucht."
	    " Sie können auch sehen:",
            html.A(" co2_2000_2011_tableau" , href="https://public.tableau.com/app/profile/kent.valera.chirinos/viz/CO2_emision_2000_2011/CO2PerCapita#1"),
        ],
            className="text-center",
            style={"font-size": "12px"}
        )
    ], style={"background-color": "#f8f9fa", "padding": "10px", "margin-top": "20px", "text-align": "center"})
])

# Callback für das Hochladen von Flügen und globalen Metriken
# Callback para cargar vuelos y métricas globales
@app.callback(
    [Output("flight-map", "children"), Output("flight-count-info", "children"),
     Output("global-stats", "children"), Output("global-alternative-energy", "children")],
    Input("load-flights-btn", "n_clicks"),
    prevent_initial_call=True
)
def update_flights(n_clicks):
    flights, total_flights = get_flights_with_tracks()
    if not flights:
        return [], "Keine aktiven Flüge gefunden.", "Keine globalen Metriken verfügbar.", "Keine alternativen Energiedaten verfügbar."

    num_loaded_flights = len(flights)
    total_fuel, total_co2 = estimate_fuel_and_co2(1000, num_loaded_flights)
    total_solar = estimate_solar_energy(num_loaded_flights)
    total_wind = estimate_wind_energy(num_loaded_flights)

    markers = [
        dl.Marker(
            position=[flight["latitude"], flight["longitude"]],
            icon={"iconUrl": "https://raw.githubusercontent.com/kentvalerach/Flugkarte_co2/main/flug.png", "iconSize": [15, 15]},
            id={"type": "flight-btn", "index": flight["icao24"]},
            children=[
                dl.Tooltip(f"Flug: {flight['callsign']} | Land: {flight['country']}"),
                dl.Popup(html.Button("Details anzeigen", id={"type": "flight-btn", "index": flight["icao24"]}, n_clicks=0))
            ]
        ) for flight in flights.values()
    ]

    return [
        [dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")] + markers,
        f"Zeigt {num_loaded_flights} von {total_flights} Flügen.",
        html.Div([
            html.P(f"Gesamter Treibstoffverbrauch: {total_fuel:.2f} kg"),
            html.P(f"Gesamte CO2-Emissionen: {total_co2:.2f} kg"),
        ]),
        html.Div([
            html.P(f"Solarenergie: {total_solar:.2f} W"),
            html.P(f"Windenergie: {total_wind:.2f} W"),
        ])
    ]
def get_aircraft_category(icao24):
    url = f"https://opensky-network.org/api/metadata/aircraft/icao/{icao24}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("category", 4)  # Si no hay categoría, devolver 4 (Mediano)
    except requests.RequestException:
        return 4  # Valor por defecto si hay un error

# Callback für die Anzeige der einzelnen Metriken mit dynamischer Aktualisierung
# Callback para mostrar métricas individuales con actualización dinámica
@app.callback(
    [Output("flight-info", "children"), Output("alternative-energy", "children")],
    Input({"type": "flight-btn", "index": ALL}, "n_clicks"),
    State("flight-map", "children"),
    prevent_initial_call=True
)
def show_flight_info(n_clicks, map_children):
    ctx = dash.callback_context

    if not ctx.triggered:
        return "Keine Fluginformationen verfügbar.", ""

    # Ermitteln, welche Taste zuletzt gedrückt wurde
    # Determinar qué botón se presionó más recientemente
    triggered_flight = max(
        ctx.triggered,
        key=lambda t: t["value"] if t["value"] is not None else 0
    )

    # Abfrage der ID des ausgewählten Fluges
    # Obtener el ID del vuelo seleccionado
    selected_flight_id = eval(triggered_flight["prop_id"].split(".")[0])["index"]

    # Suche nach den Flugzeuginformationen in den Kartenmarkierungen. 
    # Buscar la información de la aeronave en los markers del mapa
    for marker in map_children[1:]:
        if marker["props"]["id"]["index"] == selected_flight_id:
            tooltip_text = marker["props"]["children"][0]["props"]["children"]
            callsign = tooltip_text.split("|")[0].replace("Flug: ", "").strip()
            country = tooltip_text.split("|")[1].replace("Land: ", "").strip()
 
            # Dynamische Flugzeugdaten abrufen
            # Obtener datos dinámicos de la aeronave
            try:
                velocity_mps = float(marker["props"]["id"].get("velocity", random.uniform(150, 900)))  # Valor aleatorio si no hay datos
                altitude_m = float(marker["props"]["id"].get("altitude", random.uniform(5000, 12000)))  # Altitud en metros
                category = get_aircraft_category(selected_flight_id)  # Obtener categoría real
            except ValueError:
                velocity_mps = 250
                altitude_m = 10000
                category = 4

            # Geschwindigkeit in km/h umrechnen und geschätzte Entfernung berechnen
            # Convertir velocidad a km/h y calcular distancia recorrida estimada
            velocity_kmh = velocity_mps * 3.6
            estimated_distance_km = velocity_kmh * random.uniform(1.0, 3.0)  # Suponiendo entre 1 y 3 horas de vuelo

            # Anpassung des Kraftstoffverbrauchs an die aktuelle Kategorie
            # Ajustar consumo de combustible según la categoría real
            category_fuel_rate = {
                2: 1.0,   # Ligero
                3: 2.0,   # Pequeño
                4: 3.5,   # Mediano
                5: 5.0,   # Pesado
                6: 7.0    # Super Pesado (Ej. Boeing 747)
            }
            fuel_rate = category_fuel_rate.get(category, 3.5)  

            # Anpassung der Effizienz an die Höhe
            # Ajustar eficiencia según altitud
            altitude_factor = 0.85 if altitude_m >= 3000 else 1.0

            # Berechnung von Kraftstoffverbrauch und CO2 mit den Einstellungen
            # Calcular consumo de combustible y CO2 con los ajustes
            fuel, co2 = estimate_fuel_and_co2(estimated_distance_km, fuel_rate * altitude_factor)

            # Berechnung der alternativen Energieerzeugung
            # Calcular generación de energía alternativa
            solar = estimate_solar_energy()
            wind = estimate_wind_energy()

            return html.Div([
                html.P(f"Flugnummer: {selected_flight_id}"),
                html.P(f"Callsign: {callsign}"),
                html.P(f"Herkunftsland: {country}"),
                html.P(f"Geschätzte Flugdistanz: {estimated_distance_km:.2f} km"),
                html.P(f"Flugzeugkategorie: {category}"),
                html.P(f"Kraftstoffverbrauch: {fuel:.2f} kg"),
                html.P(f"CO2 Emissionen: {co2:.2f} kg"),
            ]), html.Div([
                html.P(f"Solarenergie: {solar:.2f} W"),
                html.P(f"Windenergie: {wind:.2f} W"),
            ])

    return "Keine Fluginformationen gefunden.", ""

# Start Application
# Iniciar Aplicación

if __name__ == "__main__":
    app.run_server(debug=True)
