from header import *

def grover():
	totalElement = 4
	#the number of the qubits in theory
	n = 0
	amount = 2 ** n
	while amount < totalElement:
		amount *= 2
		n += 1
	#the number of qubits actually used
	N = 2*n - 1
	c = Circuit()
	qList = []
	for i in range(0,N):
		q = Qubit()
		qList.append(q)
	#there are three kinds of qubits:
	#1.actual qubit:qList[0,1,3,5,...]
	#2.auxiliary qubit:qList[2,4,6,...]
	#3.sign qubit: the last qubit in the list
	actualQubit = []
	auxiliaryQubit = []
	signQubit = []
	for i in range(0,len(qList)):
		if i & 1 != 0 or i == 0:
			actualQubit.append(i)
		elif i & 1 == 0 and i != 0:
			auxiliaryQubit.append(i)
		else:
			signQubit.append(i)
	X(qList[N-1])
	for i in actualQubit:
		H(qList[i])
	H(qList[N-1])
	times = executeTimes(totalElement)
	for i in range(0,times):
		G(qList)
	#measure the qubits
	for q in actualQubit:
		M(qList[q])
	c.execute(1024)

#the parameter is the size of the database.
#and the target is supposed to one element
def executeTimes(n):
	theta = math.asin(math.sqrt(1 / n)) / math.pi * 180
	times = (90 - theta) / (2 * theta)
	if times > int(times) + 0.5:
		return int(times) + 1
	else:
		return int(times)

def G(qList:list):
	#oracle--H--phase--H
	actualQubit = []
	auxiliaryQubit = []
	signQubit = []
	for i in range(0,len(qList)):
		if i & 1 != 0 or i == 0:
			actualQubit.append(i)
		elif i & 1 == 0 and i != 0:
			auxiliaryQubit.append(i)
		else:
			signQubit.append(i)

	for i in range(2,len(qList),2):
		Toffoli(qList[i-2],qList[i-1],qList[i])

	for i in actualQubit:	
		H(qList[i])
		X(qList[i])
	H(qList[len(qList)-2])
	tmpList = actualQubit.copy()
	for j in range(0,len(actualQubit)-3):
		tmpList.append(auxiliaryQubit[j])
	tmpList.sort()
	if len(tmpList) == 2:
		CNOT(qList[tmpList[0]],qList[tmpList[1]])
	else:
		for i in range(2,len(tmpList),2):
			Toffoli(qList[i-2],qList[i-1],qList[i])

	H(qList[len(qList)-2])
	for i in actualQubit:	
		X(qList[i])
		H(qList[i])


