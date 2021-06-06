import pandas as pd 

df = pd.read_excel("tmp_out.xlsx", index_col=0)

print(df.head(5))