from header import *

def SWAP():
	c = Circuit(True)
	q1 = Qubit()
	q2 = Qubit()
	X(q2)
	########SWAP gate########
	CNOT(q1,q2)
	CNOT(q2,q1)
	CNOT(q1,q2)
	#########################
	M(q1)
	M(q2)
	c.execute(1024)