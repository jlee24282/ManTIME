import os

for i in range(0,1100):
    while True:
        try:
            os.system("python mantime.py test ./dataCleaned english")
        except:
            continue
        break
