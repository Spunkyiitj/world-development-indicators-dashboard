"""
World Bank Indicators - ETL script
----------------------------------
Fetches 26 development indicators (2016 onwards) for all countries from the
World Bank API, enriches them with country metadata (region, income level,
lending type, coordinates) and saves one CSV per theme into data/raw/.

Usage:  python scripts/fetch_worldbank_data.py
"""
import numpy as np
import pandas as pd
import requests
import time 



#importing the countries
url = "https://api.worldbank.org/countries?format=json&per_page=300"
response = requests.get(url)
data = response.json()
countries = data[1]
df = pd.DataFrame(countries)
df["region"] = df["region"].apply(lambda x:x['value'])
df["incomeLevel"] = df["incomeLevel"].apply(lambda x : x["value"])
df["lendingType"] = df["lendingType"].apply(lambda x : x["value"])

df2=df
df2=df2.drop(columns=["adminregion","capitalCity"])
df2.rename(columns={"iso2Code":"country_id"},inplace=True)



indicators = {
    "economic_activity_growth": [
        "NY.GDP.MKTP.KD.ZG",  # GDP growth (annual %)
        "NY.GDP.PCAP.CD",     # GDP per capita (current US$)
    ],

    "labour_market_indicators": [
        "SL.UEM.TOTL.ZS",     # Unemployment, total (% of total labor force) (modeled ILO estimate)
        "SL.UEM.1524.ZS",     # Unemployment, youth total (% of total labor force ages 15-24) (modeled ILO estimate)
        "SL.TLF.TOTL.IN",     # Labor force, total
    ],

    "trade_globalisation": [
        "NE.EXP.GNFS.CD",     # Exports of goods and services (current US$)
        "NE.IMP.GNFS.CD",     # Imports of goods and services (current US$)
    ],

    "poverty_inequality": [
        "SI.POV.NAHC",         # Poverty headcount ratio at national poverty lines (% of population)
        "SI.POV.GINI",         # Gini index
    ],

    "environmental_indicators": [
        "EG.FEC.RNEW.ZS",     # Renewable energy consumption (% of total final energy consumption)
        "AG.LND.FRST.ZS",     # Forest area (% of land area)
    ],

    "health_indicators": [
        "SP.DYN.LE00.IN",     # Life expectancy at birth, total (years)
        "SP.DYN.IMRT.IN",     # Mortality rate, infant (per 1,000 live births)
        "SH.H2O.BASW.ZS",     # People using at least basic drinking water services (% of population)
        "SH.XPD.CHEX.GD.ZS",   # Current health expenditure (% of GDP)
        "SH.IMM.IDPT",         # Immunization, DPT (% of children ages 12-23 months)
        "SH.IMM.MEAS",         # Immunization, measles (% of children ages 12-23 months)
        "SH.MMR.RISK.ZS",      # Lifetime risk of maternal death (%)
        "SH.DTH.COMM.ZS",      # Cause of death, by communicable diseases and maternal, prenatal and nutrition conditions (% of total)
        "SH.TBS.INCD",         # Incidence of tuberculosis (per 100,000 people)
        "SH.STA.BRTC.ZS",      # Births attended by skilled health staff (% of total)
        "SH.STA.MMRT",         # Maternal mortality ratio (modeled estimate, per 100,000 live births)
        "SP.POP.0014.TO.ZS",   # Population ages 0-14 (% of total population)
        "SH.HIV.INCD.ZS",      # Incidence of HIV, ages 15-49 (per 1,000 uninfected population ages 15-49)
    ],

    "technology_indicators": [
        "IT.NET.USER.ZS",      # Individuals using the Internet (% of population)
        "IT.CEL.SETS.P2",      # Mobile cellular subscriptions (per 100 people)
    ],
}




base_url = "https://api.worldbank.org/countries/all/indicators/{}?format=json&per_page=1000&page={}"

category_dataframes={}
for category,indicator in indicators.items():
    print(f"Fetching category: {category}")
    category_df=[]
    
    for indicator_code in indicator:        
        print(f"  indicator: {indicator_code}")
        page=1
        
        while True:
            url=base_url.format(indicator_code,page)
            response=requests.get(url)
        
            if response.status_code!=200:
                print(f"No Data For Indicator {indicator_code} on page {page}")
        
            data=response.json()
            if len(data)<2:
                print(f"Failed at page {page}")
                break
            total_page=data[0]["pages"]
            record=data[1]
            df=pd.json_normalize(record)

            df=df[["date","value","indicator.id","indicator.value","country.id","country.value"]].rename(
                columns={
                "indicator.id":"indicator_id",
                "indicator.value":"indicator_value",
                "country.id":"country_id",
                "country.value":"country_value",
                "date":"year"
            })
            df=df[df["year"].astype(int)>2015]
            category_df.append(df)

            if page>=total_page:
                break
            else:
                page+=1
                time.sleep(0.3)

    if category_df:
        combined_df=pd.concat(category_df,ignore_index=True)
        category_dataframes[category] = combined_df
        print(f"Total rows collected for {category}: {len(combined_df)}")
    else:
        print(f"No data collected for {category}")

print("Data fetching complete")
            

              
    
economic_activity = category_dataframes.get("economic_activity_growth",pd.DataFrame())

labour_activity = category_dataframes.get("labour_market_indicators",pd.DataFrame())

trade_globalisation = category_dataframes.get("trade_globalisation",pd.DataFrame())

poverty_inequality_activity = category_dataframes.get("poverty_inequality",pd.DataFrame())

environmental_indicators = category_dataframes.get("environmental_indicators",pd.DataFrame())

health = category_dataframes.get("health_indicators",pd.DataFrame())

technology_indicators = category_dataframes.get("technology_indicators",pd.DataFrame())





# merge each theme with country metadata
economic = pd.merge(economic_activity,df2,on="country_id",how="inner")

labour_market = pd.merge(labour_activity,df2,on="country_id",how="inner")

trade = pd.merge(trade_globalisation,df2,on="country_id",how="inner")

poverty_inequality = pd.merge(poverty_inequality_activity,df2,on="country_id",how="inner")

environmental = pd.merge(environmental_indicators,df2,on="country_id",how="inner")

health = pd.merge(health,df2,on="country_id",how="inner")

technology = pd.merge(technology_indicators,df2,on="country_id",how="inner")






economic.drop(columns=["indicator_id","id","name"],inplace=True)
labour_market.drop(columns=["indicator_id","id","name"],inplace=True)
trade.drop(columns=["indicator_id","id","name"],inplace=True)
poverty_inequality.drop(columns=["indicator_id","id","name"],inplace=True)
environmental.drop(columns=["indicator_id","id","name"],inplace=True)
health.drop(columns=["indicator_id","id","name"],inplace=True)
technology.drop(columns=["indicator_id","id","name"],inplace=True)


# save one CSV per theme
import os
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw")
os.makedirs(out_dir, exist_ok=True)
outputs = {
    "economic": economic,
    "labour_market": labour_market,
    "trade": trade,
    "poverty_inequality": poverty_inequality,
    "environmental": environmental,
    "health": health,
    "technology": technology,
}
for name, frame in outputs.items():
    frame.to_csv(os.path.join(out_dir, f"{name}.csv"))
    print(f"Saved {name}.csv ({len(frame)} rows)")
