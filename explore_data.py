import pandas as pd

df = pd.read_excel("Sepsis_Dataset ....xlsx")

print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head(10))
print(df.isna().sum())
print(df.nunique())
