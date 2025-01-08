from miniworldmaker import *

board = Board(400, 240)

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
i = 0 
for month in months:
    Rectangle((0,i), month * 10, 20)
    n = Number((200,i), month)
    n.font_size = 10
    i = i + 20
    
board.run()
    
   