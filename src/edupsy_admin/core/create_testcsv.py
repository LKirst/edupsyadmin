import pandas as pd
import os

os.chdir("projects3/edupsy_admin")
print(os.getcwd())

# create a class csv
data = {
    "first_name": ["Abraham", "Benjamin", "Cedric", "Daniel"],
    "last_name": ["Adler", "Bär", "Chaplin", "Danner"],
}

df = pd.DataFrame(data)

df.to_csv("testcsv.csv", index=False)
