# This file will help us prototype a join locally before adding it to transforms.py
import pandas as pd
import duckdb
import ibis

# Minimal mock data based on production inspection
weekly_runs_data = [
    {"Week": 1749168000, "Ad": 21, "Spend": 80.76, "Leads": 5, "id": 1},
    {"Week": 1749168000, "Ad": 22, "Spend": 50.00, "Leads": 2, "id": 2},
]

ads_data = [
    {"id": 21, "Name": "Ad A", "Campaign": "Campaign 1"},
    {"id": 22, "Name": "Ad B", "Campaign": "Campaign 1"},
]

con = duckdb.connect(database=":memory:")
con.register("Weekly_runs", pd.DataFrame(weekly_runs_data))
con.register("Ads", pd.DataFrame(ads_data))

ibis_con = ibis.duckdb.connect()
t_runs = ibis_con.create_table("Weekly_runs", pd.DataFrame(weekly_runs_data))
t_ads = ibis_con.create_table("Ads", pd.DataFrame(ads_data))

# Join logic
joined = t_runs.join(t_ads, t_runs["Ad"] == t_ads["id"])
# Rename columns to match expected schema
# We need Week, Campaign, Ad(Name), Spend, Leads

final = joined.select(
    Week=t_runs["Week"],
    Campaign=t_ads["Campaign"],
    Ad=t_ads["Name"],
    Spend=t_runs["Spend"],
    Leads=t_runs["Leads"],
)

print("Joined Schema:")
print(final.schema())

# Try aggregation transform
g = final.group_by(["Week", "Campaign", "Ad"]).aggregate(
    Spend=final["Spend"].sum(),
    Leads=final["Leads"].sum(),
)

# CPL with safe divide
g = g.mutate(CPL=ibis.ifelse(g["Leads"] > 0, g["Spend"] / g["Leads"], ibis.null()))
g = g.mutate(
    Flag_NoLeads=ibis.ifelse(g["Leads"] == 0, True, False),
    Flag_LowSample=ibis.ifelse(g["Leads"] < 3, True, False),
)

print("\nResult:")
print(g.execute())
