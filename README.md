# Energy System Engineering Model

Een energiesysteem simulatie met zonnepanelen (PV), batterij, belasting (gevangenis) en een instabiel netwerk.

## Overzicht

Deze simulatie modelleert een compleet energiesysteem met de volgende componenten:
- **Zonnepanelen (PV)**: Genereert energie op basis van zoninstraling
- **Batterij**: Opslag met rendement en zelfontlading
- **Load (Gevangenis)**: Energieverbruik
- **Netaansluiting**: Import/export met mogelijke instabiliteit

## Energie Flow Prioriteit

1. PV → Load (zonnepanelen voeden eerst de belasting)
2. PV overschot → Batterij (overtollige PV-energie laadt de batterij)
3. Batterij → Load (batterij voedt belasting als PV onvoldoende is)
4. Net → Load (netimport als PV + batterij onvoldoende)
5. PV/Batterij overschot → Net (export naar het net)

## Installatie

```bash
pip install -r requirements.txt
```

## Gebruik

### Quick Start

Genereer voorbeelddata en voer simulatie uit:

```bash
python simulate.py --generate-sample-data
```

### Aangepaste Simulatie

```bash
python simulate.py \
  --irradiation input_data/solar_irradiation.csv \
  --load input_data/load_consumption.csv \
  --grid input_data/grid_stability.csv \
  --pv-peak 100 \
  --battery-capacity 200 \
  --battery-efficiency 0.95 \
  --output-dir output
```

### Parameters

#### Invoerbestanden
- `--irradiation`: CSV met zoninstraling (W/m²)
- `--load`: CSV met energieverbruik (kW)
- `--grid`: CSV met netstabiliteit (boolean)

#### Systeemparameters
- `--pv-peak`: PV piekvermogen in kW (standaard: 100.0)
- `--battery-capacity`: Batterijcapaciteit in kWh (standaard: 200.0)
- `--battery-efficiency`: Batterijrendement 0-1 (standaard: 0.95)
- `--battery-self-discharge`: Zelfontlading per tijdstap (standaard: 0.0001)
- `--timestep`: Tijdstap duur in uren (standaard: 1.0)

#### Output
- `--output-dir`: Map voor resultaten (standaard: output)
- `--generate-sample-data`: Genereer voorbeelddata
- `--days`: Aantal dagen voor voorbeelddata (standaard: 7)

## Invoer CSV Formaat

### solar_irradiation.csv
```csv
hour,irradiation_w_m2
0,0
1,0
2,0
...
```

### load_consumption.csv
```csv
hour,load_kw
0,50.5
1,48.2
2,52.1
...
```

### grid_stability.csv
```csv
hour,grid_stable
0,True
1,True
2,False
...
```

## Output

De simulatie genereert:

1. **simulation_results.csv**: Gedetailleerde resultaten per tijdstap
   - PV generatie
   - Load verbruik
   - Batterij SOC (State of Charge)
   - Grid import/export
   - Zelfvoorzieningsgraad
   - Energiestromen

2. **simulation_results.png**: Grafieken met:
   - PV generatie en load
   - Batterij SOC (%)
   - Grid import/export
   - Energiestroom distributie
   - Zelfvoorzieningsgraad (%)

## Voorbeeldcode

```python
from energy_system import EnergySystem, load_input_data

# Laad invoerdata
data = load_input_data(
    'input_data/solar_irradiation.csv',
    'input_data/load_consumption.csv',
    'input_data/grid_stability.csv'
)

# Initialiseer systeem
system = EnergySystem(
    pv_peak_kw=100.0,
    battery_capacity_kwh=200.0,
    battery_efficiency=0.95,
    battery_self_discharge=0.0001
)

# Voer simulatie uit
results = system.simulate(data, timestep_hours=1.0)

# Maak grafieken
system.plot_results(results, save_path='output/results.png')

# Bekijk statistieken
print(f"Gemiddelde zelfvoorzieningsgraad: {results['self_sufficiency'].mean() * 100:.2f}%")
```

## Model Details

### Batterij Model
- Laad-/ontlaadrendement
- Zelfontlading per tijdstap
- Capaciteitsbegrenzing (0-100% SOC)

### PV Systeem
- Generatie op basis van instraling (W/m²)
- Standaard testcondities: 1000 W/m²

### Energiebalans
- Elk tijdstap: PV generatie, batterij status, load vraag, grid beschikbaarheid
- Automatische optimalisatie van energiestroom
- Tracking van niet-voldane load tijdens griduitval

## Licentie

Dit project is open source.