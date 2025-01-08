from miniworldmaker import *
board = Board()

@board.register
def act(self):
    m_vec = Vector(board.get_mouse_x(), board.get_mouse_y())
    center = Vector(200, 200)
    m_vec = m_vec - center
    print(m_vec.x, m_vec.y)
    m_vec.normalize()
    m_vec.multiply(100)
    m_vec.add(center)
    #print((m_vec.x, m_vec.y), (center.x, center.y))
    Line((center.x, center.y),(m_vec.x,m_vec.y))
    
board.run()