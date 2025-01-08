from miniworldmaker import *

months = []
months.append(1.9)
months.append(2.5)
months.append(5.9)
months.append(10.3)
months.append(14.6)
months.append(18.1)
months.append(20)
months.append(19.6)
months.append(15.7)
months.append(10.9)
months.append(6.2)
months.append(2.8)

print(months)
sum = 0

print(months[1], months[4])

for month in months:
    sum = sum + month
    
print(sum/12)
   