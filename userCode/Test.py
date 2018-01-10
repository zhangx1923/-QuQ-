from header import *

def u():
	c = Circuit()
	q = Qubit()
	qList = []
	for i in range(0,3):
		qList.append(Qubit())
	X(qList[0])
	Rx(PI,qList[0])
	QSprint(qList[0])
	#X(q)
	#Toffoli(q,qList[0],qList[1])
	#CNOT(qList[0],qList[1])
	# with DMif([qList[0],qList[1],qList[2]],[1,1,0,]) as dmo:
	# 	dmo.X(q)
	# with DMif([qList[0],qList[1]],[1,0]) as dmo:
	# 	dmo.H(q)
	#M(qList[1])
	#QSprint(q)
	#QSprint(q.entanglement)
	#M(q)
	M(qList[0])
	c.execute(1024)