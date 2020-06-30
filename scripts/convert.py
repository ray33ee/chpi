
import csv

arr = bytearray(10080)

with open("../files/chatsch.csv", "r") as fh:
    
    file = csv.reader(fh)
    
    for row in file:
        weekday = row[0]
        
        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        
        daynum = days.index(weekday)
        
        start = (daynum * 24 + int(row[2])) * 60 + int(row[3])
        finish = (daynum * 24 + int(row[4])) * 60 + int(row[5])
        
        state = 0
        
        if row[1] == 'CH': #Central heating
            state = 1
        if row[1] == 'HW': # Hot water
            state = 2
        if row[1] == 'EO': # Emnergency off
            state = 4
        
        for i in range(start, finish):
            arr[i] |= state
        
    
with open("../files/schedule", "wb") as fh:
    fh.write(arr)
  