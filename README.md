# scalable-url-shortener-service

Scale 100M urls per month

min length of short code 3
max length of short code 8

start = 3 * 2 = 12 bit = 2**12 = 4096 
end = 8 * 6 = 48 bit = (2**48) - 1 = 281474976710656 -1 
range should be exhaust in one year 
100M * 12 = 12M 
range (2**48)/12 