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
	#the target element
	targetE = "11"
	#check the length of the target element and the totalElement
	if checkE(totalElement,targetE):
		c = Circuit()
		qList = []
		for i in range(0,N):
			q = Qubit()
			qList.append(q)

		X(qList[N-1])
		for i in range(0,N):
			H(qList[i])

		#act the G operator for "times" times
		times = executeTimes(totalElement)
		for i in range(0,times):
			G(qList,targetE)

		#measure the qubits
		for i in range(0,N-1):
			qList[i] = M(qList[i])

		#execute the circuit for 1024 times
		c.execute(1024)
	else:
		writeErrorMsg("The length of the target element isn't correspond with the number of the total elements!")

#the parameter is the size of the database.
#and the target is supposed to one element
def executeTimes(n):
	theta = math.asin(math.sqrt(1 / n)) / math.pi * 180
	times = (90 - theta) / (2 * theta)
	if times > int(times) + 0.5:
		return int(times) + 1
	else:
		return int(times)

def checkE(toE:int,taE:str):
	if toE <= (2 ** len(taE)):
		return True
	else:
		return False

def G(qList:list,taE:str):
	qn = len(qList)
	#there are four phase in this G operator
	#PH1: apply the oracle operator
	vl = []
	for k in range(0,len(taE)):
		vl.append(int(taE[k]))
	tmp1 = []
	for j in range(0,qn-1):
		tmp1.append(qList[j])
	with DMif(tmp1,vl) as dmo1:
		dmo1.X(qList[qn-1])

	#PH2: act H gates on the qubits except the last element
	for i in range(0,qn-1):
		H(qList[i])

	#PH3: act the phase operator on the qubits except the last element
	for i in range(0,qn-1):
		X(qList[i])
	H(qList[qn-2])

	tmp2 = []
	for j in range(0,qn-2):
		tmp2.append(qList[j])
	with DMif(tmp2,1) as dmo2:
		dmo2.X(qList[qn-2])
	
	H(qList[qn-2])
	for i in range(0,qn-1):
		X(qList[i])

	#PH4: act the H gates on all the qubits
	for i in range(0,qn):
		H(qList[i])


