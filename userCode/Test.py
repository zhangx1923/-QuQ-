from header import *

def u():
	c = Circuit()
	q = Qubit()
	qList = []
	for i in range(0,3):
		qList.append(Qubit())
	X(qList[0])
	X(q)
	Toffoli(q,qList[0],qList[1])
	M(q)
	M(qList[0])
	M(qList[1])
	# with DMif([qList[0],qList[1],qList[2]],[0,0,1]) as dmo:
	# 	dmo.X(q)
		#print(dmo.v)
	c.execute(1024)