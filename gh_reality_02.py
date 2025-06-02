import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick # umožňuje přesněji ovládat popisky (tzv. ticky) na osách grafu v matplotlib
import seaborn as sns
import pandas as pd
from gh_reality_00 import price_max, sqm_min, dispozice_list
from gh_reality_01 import geo_data
import streamlit as st
import numpy as np
import folium # interaktivní mapy
from streamlit_folium import st_folium

# Load the dataset ----------------------------------------------------------------------------------------------------------------
df = pd.read_csv("s_reality_cleaned.csv")
price_max = f"{price_max:,}".replace(",", " ")
new_dispozice_list = ''
for disp in dispozice_list:
    new_dispozice_list += disp + ', '
new_dispozice_list = new_dispozice_list[:-2]

# change for beter visialization - 01
df["City_part"] = df["City_part"].apply(lambda x: x.split("- ")[1] if "- " in x else x)

# Visualizing Trends -----------------------------------------------------------------------------------------------------------------------
# Price
def plot_price_distribution(df):
    plt.figure(figsize=(10,5)) # velikost v palcích
    sns.histplot(df['Price'], bins=30, kde=True) # bins = sloupce
    plt.xlabel("Price (in millions)")
    plt.ylabel("Count")
    plt.title(f"Price Distribution of Listings\nWith filters max price = {price_max}")
    plt.show()

# print(f"{price_max:,}") 87000000 -> 8,700,00
# formátuj číslo s oddělovačem tisíců podle standardního (anglického) stylu, tedy pomocí čárky ,

# m2
def analyze_m2(df):
    plt.figure(figsize=(10,5))
    sns.histplot(df['m2'], binwidth=5, kde=True)
    #sns.countplot(x='m2', data=df, binwidth=5, order=sorted(df['m2'].dropna().unique())) - pro kategorie
    # x specifikuje, že na ose X budou hodnoty z sloupce 'Beds' v dataframe df
    # dropna() - odstraní všechny NaN hodnoty
    plt.xlabel("Area m2")
    plt.ylabel("Count")
    plt.title(f"Distribution of area in Listings\nWith filters min area = {sqm_min}")
    plt.show()

# disposition
def analyze_dispozition(df):
    plt.figure(figsize=(10,5))
    sns.countplot(x='Disposition', data=df, order=sorted(df['Disposition'].dropna().unique()))
    plt.xlabel("Disposition")
    plt.ylabel("Count")
    plt.title(f"Distribution of disposition in Listings\nWith filters disposition = {new_dispozice_list}")
    plt.show()

    # disposition
def city_part(df):
    plt.figure(figsize=(10,5))
    sns.countplot(x='City_part', data=df, order=sorted(df['City_part'].dropna().unique()))
    plt.xlabel("City part")
    plt.ylabel("Count")
    plt.title("Distribution of city parts")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

# Creating the Streamlit Dashboard ----------------------------------------------------------------------------------
# UI
# musí se spouštět přes cmd-line: streamlit run c:/Users/H32250/H32250/projects/RealEstate/reality/reality_02.py
st.title("🏡 Brno living dashboard")
st.write("Analyze how bad the situation really is")

show_all = st.sidebar.checkbox("Show All Properties", value=False) # vykreslí zaškrtávací políčko

if show_all:
    filtered_df = df  # Show all properties
else:
    # Determine the max price dynamically and round up to the next 1 million
    min_price_value = max(1000, df["Price"].min())  # Ensure minimum is at least 1,000
    max_price_value = np.ceil(df["Price"].max() / 1_000_000) * 1_000_000  # Round up to next 1M, pomocí _ _ přehlednější zápis čísel

    # Price Slider
    min_price, max_price = st.sidebar.slider(
        "Select Price Range", 
        min_value=int(min_price_value), 
        max_value=int(max_price_value), 
        value=(int(min_price_value), int(max_price_value)),
        format="%d Kč"
    )

    # Square Footage: Ensure a sensible range
    min_sqm= sqm_min
    max_sqm= int(np.ceil(df["m2"].max()))

    selected_sqft = st.sidebar.slider("Square metres", min_sqm, max_sqm, (sqm_min, max_sqm))

    # dispozice
    dispozice = sorted(df["Disposition"].unique())
    vybrane_dispozice = st.sidebar.multiselect("Disposition", options=dispozice, default=dispozice) # bez sidebar bude uporstřed

    # city_part
    city_part_ = sorted(df["City_part"].unique())
    select_all_city = st.sidebar.checkbox("Select all City parts", value=True) 
    if select_all_city:
        vybrane_city_part = st.sidebar.multiselect("City_part", options=city_part_, default=city_part_)
    else:
        vybrane_city_part = st.sidebar.multiselect("City_part", options=city_part_, default=[])

    # Apply Filters - Vytvoří nový DataFrame filtered_df obsahující pouze ty záznamy, které spadají do vybraného cenového rozmezí atd.
    filtered_df = df[
        (df["Price"] >= min_price) & (df["Price"] <= max_price) &
        (df["m2"] >= selected_sqft[0]) & (df["m2"] <= selected_sqft[1]) &
        (df["Disposition"].isin(vybrane_dispozice)) &
        (df["City_part"].isin(vybrane_city_part))

    ]

# Visualizing the Data --------------------------------------------------------------------------------------------------------------
st.subheader(f"📊 {len(filtered_df)} Listings Found")

selected_rows = st.data_editor( # interaktivní tabulka
    filtered_df[["Price", "Disposition", "m2", "City_part", "Address", "Street", "geo_latitute", "geo_longitude", "Link"]] # sloupce
    .sort_values(by="Price", ascending=True)
    .reset_index(drop=True),
    use_container_width=True,
    height=400,
    num_rows="dynamic", # Výška se přizpůsobuje počtu řádků, ale je omezená.
    hide_index=True, # Nezobrazí číselný index vlevo v tabulce
    column_config={"Link": st.column_config.LinkColumn()}, # Říká Streamlitu, že sloupec „Link“ je odkaz – klikací URL.
    key="table_selection"
    # Streamlit si za scénou uchovává stav všech interaktivních prvků (jako jsou formuláře, slidery, checkboxy, tabulky…). 
    # Každý z těchto prvků musí mít unikátní identifikátor, podle kterého si zapamatuje
    # Pokud použiješ více komponent stejného typu (např. víc st.data_editor()), musí se lišit key, jinak by se jejich stav „přepisoval“
    # Pokud key neudáš - Streamlit ho vygeneruje automaticky (např. podle pořadí), při jakékoli změně v kódu se stav nemusí správně zachovat
)

#st.subheader("Price Distribution")
#with st.container(): # možňuje seskupit více Streamlit komponent do jednoho prostoru
 #   plot_price_distribution(df)
  #  st.pyplot(plt.gcf())
    # nemusel se psát nanovo -> stačil přidat poslední řáděk pro vykreslení
    # ale není interkativní !!!!!!!!!!!!!!

st.subheader("Price Distribution")
with st.container(): # možňuje seskupit více Streamlit komponent do jednoho prostoru
    fig, ax = plt.subplots(figsize=(8, 4)) # velikost v palcích
    sns.histplot(filtered_df["Price"], bins=30, kde=True, ax=ax) # ax = ax - vykreslen na předem vytvořené ose (ax
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'{x/1_000_000:.1f}M')) # 1f určuje počet desetiných míst
    ax.set_xlabel("Price (Kč)")
    ax.set_ylabel("Count")
    st.pyplot(fig)

st.subheader("Area")
with st.container(): 
    fig, ax = plt.subplots(figsize=(8, 4))  # subpolots pro více grafů na celé stránce, pokud jen jeden lze použít bez toho
    sns.histplot(filtered_df["m2"], binwidth=5, kde=True, ax=ax)  # předáš osu ručně
    ax.set_xlabel("Area m²")
    ax.set_ylabel("Count")
    st.pyplot(fig) 

st.subheader("Disposition")
with st.container(): 
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.countplot(x='Disposition', data=filtered_df, order=sorted(filtered_df['Disposition'].dropna().unique()))
    ax.set_xlabel("Disposition")
    ax.set_ylabel("Count")
    st.pyplot(fig) 

st.subheader("City part")
with st.container(): 
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.countplot(x='City_part', data=filtered_df, order=sorted(filtered_df['City_part'].dropna().unique()))
    ax.set_xlabel("City part")
    ax.set_ylabel("Count")
    ax.tick_params(axis='x', rotation=90) # jinak
    fig.tight_layout() # na fig ne
    st.pyplot(fig) 

# Interactive Map ----------------------------------------------------------------------------------
# Get selected address (if any)
selected_address = selected_rows.iloc[0]["Address"] if not selected_rows.empty else None

st.subheader("Property Locations")

# Create map centered on 
data = {
    "Address": ["Brno-město"],
    "geo_latitute": [None],
    "geo_longitude": [None]
}
df_map = pd.DataFrame(data)
df_map = geo_data(df_map) # opkaovaná výpis kvůli interanci se steamlit
x = (df_map["geo_latitute"].iloc[0])
y = (df_map["geo_longitude"].iloc[0])

m = folium.Map(location=[x, y], zoom_start=12)

# Add markers for all filtered properties
for _, row in filtered_df.iterrows():
    # pop up okno pokaždé když se najede na konkrétní
    #<b> - tučný text, <br> break - nový řádek
    popup_info = f"""
    <b>{row['Address']}</b><br> 
    Price: {row['Price']:,.0f} Kč<br>
    Disposition: {row['Disposition']}<br>
    Area: {row['m2']:,}<br>
    <a href="{row['Link']}" target="_blank">View Listing</a>"""

    # Highlight the selected property in red, others in blue
    icon_color = "red" if selected_address and row["Address"] == selected_address else "blue"

    # přidání ikon pro každou nemovitost na mapu
    if pd.notnull(row["geo_latitute"]) and pd.notnull(row["geo_longitude"]): # bacha na zápis NULL
        folium.Marker(
            location=[row["geo_latitute"], row["geo_longitude"]],
            popup=popup_info,
            icon=folium.Icon(color=icon_color, icon="home"),
        ).add_to(m) # m je naše pojmenování dřívě vytvořené mapy

# Display map
st_folium(m, width=800, height=500)


# Run Script  -----------------------------------------------------------------------------------------------------------------------
#if __name__ == "__main__": 
 #   plot_price_distribution(df)
  #  analyze_m2(df)
   # analyze_dispozition(df)
    #city_part(df)"""
# správně se komentuje do # 
