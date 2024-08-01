
import os
import pandas as pd

df: pd.DataFrame = pd.DataFrame()

for file in os.listdir():
    if file.endswith('.csv'):
        new_df: pd.DataFrame = pd.read_csv(file)
        df = pd.concat((df, new_df))

df.reset_index(inplace=True)
mislabelled = df[df['MW total (MW)'].notna()].index
df.loc[mislabelled, 'total power (MW)'] = df.loc[mislabelled, 'MW total (MW)']
df.drop(columns=['to nearest (miles)', 'MW total (MW)', 'index'], inplace=True)
df.to_csv('data_centers.csv')
