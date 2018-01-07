from header import *

def u():
	c = Circuit()
	q = Qubit()
	qList = []
	for i in range(0,3):
		qList.append(Qubit())
	X(qList[0])
	X(q)
	#Toffoli(q,qList[0],qList[1])
	CNOT(qList[0],qList[1])
	# with DMif([qList[0],qList[1],qList[2]],[1,1,0,]) as dmo:
	# 	dmo.X(q)
	with DMif([qList[0]],[0]) as dmo:
		dmo.Z(q)
	#M(qList[1])
	QSprint(q)
	M(q)
	c.execute(1024)