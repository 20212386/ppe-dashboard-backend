import pandas as pd
import random

path = "app/data/sample_logs.csv"

df = pd.read_csv(path, encoding="utf-8-sig")

if "site" not in df.columns:
    random.seed(42)
    sites = ["현장1", "현장2", "현장3"]
    df.insert(2, "site", [random.choice(sites) for _ in range(len(df))])

df.to_csv(path, index=False, encoding="utf-8-sig")
print("site 컬럼 추가 완료")