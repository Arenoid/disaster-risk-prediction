from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

df = pd.read_csv("data/features.csv")

@app.get("/api/districts")
def get_districts():
    return df.to_dict(orient="records")


@app.get("/api/districts/{name}")
def get_district(name: str):
    row = df[df['adm2_name'].str.lower() == name.lower()]
    if row.empty:
        return {"error": "District not found"}
    return row.iloc[0].to_dict()
