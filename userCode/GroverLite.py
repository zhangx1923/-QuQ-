from header import *

def groverLite():
	totalElement = 4
	#the number of the qubits in theory
	N = 3
	c = Circuit()
	qList = []
	for i in range(0,N):
		q = Qubit()
		qList.append(q)
	actualQubit = [0,1]
	signQubit = [2]
	X(qList[N-1])
	for i in actualQubit:
		H(qList[i])
	H(qList[N-1])
	G(qList)
	#measure the qubits
	for q in actualQubit:
		qList[q] = M(qList[q])
	c.execute(1024)

def G(qList:list):
	actualQubit = [0,1]
	signQubit = [2]

	Toffoli(qList[0],qList[1],qList[2])

	for i in actualQubit:	
		H(qList[i])
		X(qList[i])
	H(qList[len(qList)-2])
	CNOT(qList[0],qList[1])
	H(qList[len(qList)-2])
	for i in actualQubit:	
		X(qList[i])
		H(qList[i])


