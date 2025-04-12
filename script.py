# Scale 100M urls per month

# min length of short code 3
# max length of short code 8

# start = 3 * 2 = 12 bit = 2**12 = 4096 
# end = 8 * 6 = 48 bit = (2**48) - 1 = 281474976710656 -1 
# range should be exhaust in one year 
# 100M * 12 = 12M 
# range (2**48)/12 

import psycopg2
from psycopg2.extras import execute_values
import os 


from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT")
}

min_len = 4098
max_len = 281474976710655
per_range = int((12 * (10**8)))
t_range = int(max_len / per_range)
start = min_len


query = "INSERT INTO ticketing(range_start,range_end,current) VALUES %s"
data = []
for i in range(t_range):
    data.append(
        (start,start + per_range,start)
    )
    start = start + per_range + 1

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

execute_values(cursor,query,data)
conn.commit()
cursor.close()
conn.close()
    
    

