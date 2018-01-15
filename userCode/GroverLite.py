from header import *

def groverLite():
	totalElement = 4
	targetElement = "11"
	#the number of the qubits in theory
	N = 3
	c = Circuit()
	qList = []
	for i in range(0,N):
		q = Qubit()
		qList.append(q)

	X(qList[N-1])
	for i in range(0,N):
		H(qList[i])
	
	#apply the G operator on the qubits
	G(qList,targetElement)

	#measure the qubits
	for i in range(0,N-1):
		qList[i] = M(qList[i])

	#execute the circuit for 1024 times
	c.execute(1024)

def G(qList:list,target):
	vl = []
	for i in range(0,len(target)):
		vl.append(int(target[i]))

	with DMif([qList[0],qList[1]],vl) as dmo:
		dmo.X(qList[2])

	for i in range(0,2):	
		H(qList[i])
		X(qList[i])
	H(qList[1])
	CNOT(qList[0],qList[1])
	H(qList[1])
	for i in range(0,2):	
		X(qList[i])
		H(qList[i])


