from header import *

def wrong():
	c = Circuit(True)
	q = Qubit()
	#the qubit has the same id of q
	q_wrong = Qubit(False,0)
	M(q)
	c.execute(1024)