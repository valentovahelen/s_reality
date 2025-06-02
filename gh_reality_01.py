import pandas as pd
from geopy.geocoders import Nominatim
from gh_reality_00 import price_max, sqm_min, dispozice_list
import datetime as dt
import os

# Load & Inspect the Dataset ---------------------------------------------------------------------------------------------------
# Load the dataset
df = pd.read_csv("s_reality.csv")

# Display basic info
def inspect_data(df):
    print("\nData Overview:")
    print(df.info())  # Column types, missing values
    print("\nFirst Few Rows:")
    print(df)

# Handling Missing Data ------------------------------------------------------------------------------------------------------------
# already done in previous step 00

# Formatting Data ------------------------------------------------------------------------------------------------------------
def extract_numeric(value):
    value = value.split(" Kč")[0]
    value = value.replace(" ", "")
    return value

def convert_columns(value):
    return int(value)

def formatting_data(df):
    df["Price"]  = df['Price'].apply(extract_numeric)

    df["Price"]  = df['Price'].apply(convert_columns)
    df["m2"]  = df['m2'].apply(convert_columns)

    # address in more detail
    df["Street"] = df["Address"].apply(lambda x: x.split(", ")[0] if ", " in x else None) # musí být takto aby se aplikovalo na každý řádek zvlášť
    df["City_part"] = df["Address"].apply(lambda x: x.split(", ")[1] if ", " in x else x)

    return df

# sneaky add - lools exactly like normal listing
def detect_sneaky_adds(df):
    df = df.drop(df[df["Price"] > price_max].index)
    df = df.drop(df[df["m2"] < sqm_min].index)
    df = df.drop(df[~df["Disposition"].isin(dispozice_list)].index) # ~ negace
    return df

# add georeferenced data - knihovna - from geopy.geocoders import Nominatim
def geo_data(df):
    try:
        print("Loading georeferenced data...")
        geolocator = Nominatim(user_agent="mapa_app")
        for index, row in df.iterrows():
            location = geolocator.geocode(row["Address"])
            if location:
                df.loc[index, "geo_latitute"] = location.latitude
                df.loc[index, "geo_longitude"] = location.longitude
                print("Georeferenced data loaded.")
            else:
                print(f"Address not found: {row['Address']}")
    except:
        print("Georeferenced data failed.")

    return df

# Data Analysis & Visualization ------------------------------------------------------------------------------------------------------------
def summarize_data(df):
    print("\nSummary Statistics:")
    print(df.describe())

# Database with older listings -----------------------------------------------------------------------------------------------------------------------
reality_all_link = "s_reality_all.csv"

def delete_csv_data():
    try:
        open(reality_all_link, "w").close()
        print(f"Promazal se {reality_all_link}")
    except:
        print(f"Něco se pokazilo při promazávaní {reality_all_link}")

def df_all():
    try:
        if os.path.isfile(reality_all_link):
            try:
                df_all_original = pd.read_csv(reality_all_link)
            except pd.errors.EmptyDataError:
                df_all_original = pd.DataFrame()  # Pokud je soubor prázdný
        else:
            df_all_original = pd.DataFrame()

        if df_all_original.empty:
            df_new = df.copy()
        else:
            df_new = df[~df['Link'].isin(df_all_original['Link'])]

        df_new["Date"] = dt.date.today()

        if not df_new.empty:
            df_new.to_csv(reality_all_link, mode='a', index=False, header=not os.path.isfile(reality_all_link))
            print(f"Přidáno {len(df_new)} nových záznamů.")
        else:
            print("Žádné nové záznamy k přidání.")
    except:
        print(f"Nastala chyba při práci se souborem all.")

# Run Script & Save Cleaned Data -----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__": # "Spusť následující blok kódu jen tehdy, když tento skript spouštím přímo."
    inspect_data(df)
    df = formatting_data(df) 
    df = detect_sneaky_adds(df) 
    df = geo_data(df)
    summarize_data(df)
    
    # Save the cleaned dataset
    df.to_csv("s_reality_cleaned.csv", index=False)
    print("Cleaned data saved as 's_reality_cleaned.csv'.")

    # Creating a database with older listings
    #delete_csv_data()
    df_all()
    

# Notes - other ------------------------------------------------------------------------------------------------------
# if __name__ == "__main__": <- dunder name, main = double underscore
# když si chceme importovat věci z jiných kodu-modulu-knihoven tak se importuje celá a nejen ta proměnná

# počet knihoven
# Používej virtuální prostředí (venv) pro izolaci závislostí na projekty.
