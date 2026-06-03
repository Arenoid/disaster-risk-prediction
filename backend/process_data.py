import geopandas as gpd
import pandas as pd
import numpy as np
import ast
from shapely.ops import nearest_points

districts = gpd.read_file("data/districts/npl_admin2.shp")
districts = districts[['adm2_name', 'adm2_pcode', 'center_lat', 'center_lon', 'area_sqkm', 'geometry' ]]


bipad = pd.read_csv("data/bipad_cleaned.csv")
usgs = pd.read_csv("data/usgs_clean.csv")

bipad['coords'] = bipad['point'].apply(ast.literal_eval)
bipad['lon'] = bipad['coords'].apply(lambda x : x['coordinates'][0])
bipad['lat'] = bipad['coords'].apply(lambda x: x['coordinates'][1])
bipad_gdf = gpd.GeoDataFrame(bipad, geometry = gpd.points_from_xy(bipad['lon'],bipad['lat']),crs = 'EPSG:4326')
bipad_joined = gpd.sjoin(bipad_gdf, districts[['adm2_name', 'adm2_pcode','geometry']], how = 'left', predicate='within')

usgs_gdf = gpd.GeoDataFrame(usgs, geometry = gpd.points_from_xy(usgs['longitude'], usgs['latitude']), crs = 'EPSG:4326')
usgs_joined = gpd.sjoin(usgs_gdf, districts[['adm2_name', 'adm2_pcode', 'geometry']], how = 'left', predicate='within')


districts['centroid'] = districts.geometry.centroid
def nearest_district(point, districts):
    distances = districts['centroid'].distance(point)
    return districts.iloc[distances.idxmin()]['adm2_name']


unmatched_idx = usgs_joined[usgs_joined['adm2_name'].isna()].index
for idx in unmatched_idx:
    usgs_joined.at[idx, 'adm2_name'] = nearest_district(usgs_joined.at[idx, 'geometry'],districts)


floods = bipad_joined[bipad_joined['hazard'] == 11].groupby('adm2_name').size().rename('flood_count')
landslides = bipad_joined[bipad_joined['hazard'] == 17].groupby('adm2_name').size().rename('landslide_count')
eq_stats = usgs_joined.groupby('adm2_name').agg(
    eq_count = ('mag', 'count'),
    eq_avg_mag = ('mag', 'mean'),
    eq_max_mag = ('mag', 'max')
)

features = districts[['adm2_name', 'adm2_pcode', 'center_lat', 'center_lon', 'area_sqkm']].copy()
features = features.merge(floods, on = 'adm2_name', how = 'left')
features = features.merge(landslides, on = 'adm2_name', how = 'left')
features = features.merge(eq_stats, on= 'adm2_name', how = 'left')
features = features.fillna(0)
features = features.fillna(0)


print(features.shape)
print(features.head())



from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

features['flood_risk'] = pd.qcut(features['flood_count'], q=3, labels = ['low', 'medium', 'high'])
features['landslide_risk'] = pd.qcut(features['landslide_count'], q = 3, labels = ['low', 'medium', 'high'])

X = features[['center_lat', 'center_lon', 'area_sqkm', 'eq_count', 'eq_avg_mag', 'flood_count', 'landslide_count', 'eq_max_mag']]
le = LabelEncoder()

y_flood = le.fit_transform(features['flood_risk'])
X_train, X_test, y_train, y_test = train_test_split(X, y_flood, test_size=0.2, random_state=42)
flood_model = XGBClassifier(n_estimators = 100, random_state = 42)
flood_model.fit(X_train, y_train)
print("Flood Model:")
print(classification_report(y_test, flood_model.predict(X_test)))


y_land = le.fit_transform(features['landslide_risk'])
X_train, X_test, y_train, y_test = train_test_split(X, y_land,test_size = 0.2, random_state=42)
land_model = XGBClassifier(n_estimators = 100, random_state = 42)
land_model.fit(X_train, y_train)
print("Landslide Model:")
print(classification_report(y_test, land_model.predict(X_test)))


features['eq_score'] = (
    0.5* (features['eq_count']/ features['eq_count'].max())+
    0.3* (features['eq_avg_mag'] / features['eq_avg_mag'].max())+
    0.2 *(features['eq_max_mag']/ features['eq_max_mag'].max())
)

features['eq_risk'] = pd.qcut(features['eq_score'], q = 3 , labels = ['low', 'medium', 'high'])

features['flood_risk_pred'] = le.inverse_transform(flood_model.predict(X))
features['landslide_risk_pred'] = le.inverse_transform(land_model.predict(X))

features.to_csv("data/features.csv", index = False)
print("Saved Features.csv")
print(features[['adm2_name', 'flood_risk_pred', 'landslide_risk_pred', 'eq_risk']].head(10))