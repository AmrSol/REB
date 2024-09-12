IATA_PEROD_FOLDER = "Data/IATA_perOD"
IATA_PERSEGMENT_FOLDER = "Data/IATA_perSegment"
MIDT_FLOW_FOLDER = "Data/MIDT_flow"
MIDT_LOADFACTOR_FOLDER = "Data/MIDT_loadfactor"
OAG_TOFROM_FOLDER = "Data/OAG_toFrom"

TAX_ASSUMPTIONS_FILE = "Data/Data_Assumptions/Tax.csv"
ANCILLARY_ASSUMPTIONS_FILE = "Data/Data_Assumptions/Ancillary.csv"
EXIT_LIMIT_ASSUMPTIONS_FILE = "Data/Data_Assumptions/e_seats.csv"

SEA_AIRPORT_AIRLINE_PAIRS = {
    "SIN-PER": ["SQ", "QF", "TR"],
    "SIN-MEL": ["SQ", "QF", "TR", "EK"],
    "SIN-SYD": ["SQ", "QF", "TR", "BA"],
    "SIN-KIX": ["SQ", "TR"],
    "SIN-JED": ["SV", "TR"],
    "KUL-PER": ["MH", "OD", "D7"],
    "KUL-SYD": ["MH", "D7"],
    "KUL-PEK": ["D7", "MH", "CA"],  # AIRPORT-PAIR
    "KUL-KIX": ["MH", "D7"],
    "KUL-HND": ["NH", "D7"],  # AIRPORT-PAIR
    "KUL-NRT": ["D7", "JL", "MH", "NH"],  # AIRPORT-PAIR
    "KUL-JED": ["D7", "MH"],
}

SEA_CITY_PAIRS = {
    "SIN-PER": "SIN-PER",
    "SIN-MEL": "SIN-MEL",
    "SIN-SYD": "SIN-SYD",
    "SIN-KIX": "SIN-OSA",
    "SIN-JED": "SIN-JED",
    "KUL-PER": "KUL-PER",
    "KUL-SYD": "KUL-SYD",
    "KUL-PEK": "KUL-BJS",  # AIRPORT-PAIR
    "KUL-KIX": "KUL-OSA",
    "KUL-HND": "KUL-TYO",  # AIRPORT-PAIR
    "KUL-NRT": "KUL-TYO",  # AIRPORT-PAIR
    "KUL-JED": "KUL-JED",
}

MIDT_FLOW_COLUMNS = [
    "Leg Type",
    "Leg Origin Airport",
    "Leg Destination Airport",
    "Leg Operating Airline",
    "Origin Airport",
    "Origin City Name",
    "Destination Airport",
    "Destination City Name",
    "Cabin Class",
    "Year",
    "Month",
    "Leg 2",
    "Leg 3",
    "Leg 4",
    "Leg 1 Operating Airline",
    "Leg 2 Operating Airline",
    "Leg 3 Operating Airline",
    "Leg 4 Operating Airline",
    "Passengers",
    "OD Avg. Base Fare(USD)",
    "OD Base Revenue(USD)",
    "Leg Avg. Base Fare (USD) Stline",
    "Leg Base Revenue (USD) Stline",
]

MIDT_LF_COLUMNS = [
    "Origin Airport",
    "Destination Airport",
    "Operating Airline",
    "Year",
    "Month",
    "Airline Share",
    "Passengers",
    "PPDEW",
    "Load Factor",
    "ASK (Millions)",
    "RPK (Millions)",
    "OD Avg. Base Fare(USD)",
    "OD Base Revenue(USD)",
    "OD Avg. Total Fare(USD)",
    "OD Total Revenue(USD)",
    "Leg Avg. Base Fare (USD) Stline",
    "Leg Base Revenue (USD) Stline",
    "Leg Avg. Total Fare (USD) Stline",
    "Leg Total Revenue (USD) Stline",
    "Flow Share",
    "Departures",
    "Yield(Cent/KM)",
    "Distance (km)",
]

OAG_TO_FROM_COLUMNS = [
    "Carrier Code",
    "Dep Airport Code",
    "Dep City Code",
    "Dep City Name",
    "Arr Airport Code",
    "Arr City Code",
    "Arr City Name",
    "Specific Aircraft Code",
    "Seats",
    "GCD (km)",
    "Flying Time",
    "Ground Time",
    "Frequency",
    "Seats (Total)",
    "Time series",
    "Date",
    "Month",
    "Year",
]

TAX_COLUMNS = ["Origin", "Destination", "USD"]

ANCILLARY_COLUMNS = ["Leg Operating Airline", "ARPP($)"]

EXIT_LIMIT_COLUMNS = [
    "Specific Aircraft Code",
    "Equipment name",
    "Equipment Code",
    "# of e-seats",
    "WB_NB",
]

DF_COLUMN_DICT = {
    "df": MIDT_FLOW_COLUMNS,
    "df_lf": MIDT_LF_COLUMNS,
    "df_to_from": OAG_TO_FROM_COLUMNS,
    "df_tax": TAX_COLUMNS,
    "df_ancillary": ANCILLARY_COLUMNS,
    "df_exit_limit": EXIT_LIMIT_COLUMNS,
}

DICT_DISC_POINTS = {}
