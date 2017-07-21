
import os

for i in range(0,1100):
    while True:
        try:
            os.system("python mantimeTest.py test ./testInput english")
        except:
            continue
        break
