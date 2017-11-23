import sys
sys.path.append('../tools/')
from interactCfg import *
from Bit import Bit
from Qubit import *
from helperFunction import *
from Circuit import Circuit
from Error import *
import numpy as np
import math
#get the info about the function name and the line number
def get_curl_info():
	try:
		raise Exception
	except:
		f = sys.exc_info()[2].tb_frame.f_back
	return [f.f_code.co_name, f.f_lineno]
################################################################
#there are three kinds of gates in QuanSim:
#1.single Qubit gate(I,X,Y,Z,H,S,Sd,T,Td),Sd is S^\dagger
#2.multi Qubit gate(CNOT)
#3.non-unitary gate, that is, Measurement
#the gates 1 and 2 are unisersal
#In addition, user can design their own gate
################################################################

#check the type of the input, only Qubit is allowed.
def checkType(ql:list):
	for q in ql:
		types = type(q)
		if types == Bit:
			try:
				raise TypeError
			except TypeError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("Bit " + str(q.ids) + " has been meaured! You can't act any quntum gate on it!",funName,line)
		if types != Qubit:
			try:
				raise TypeError
			except TypeError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("The type of the date should be Qubit!",funName,line)


#check the number of rows and cols, the result must be n*1 or m*m, otherwise raise an error
def checkMatrix(m:list):
	rows = len(m)
	try:
		cols = len(m[0])
		for i in range(0,rows):
			if cols != len(m[i]):
				#each row must have the same number of elements
				raise ValueError("each row doesn't have the same number of elements")
		if cols != 1 and cols != rows:
			raise ValueError("the format of the list is wrong")
	except KeyError as ke:
		info = get_curl_info()
		funName = info[0]
		line = info[1]
		writeErrorMsg(ke,funName,line)
	except ValueError as ve:
		info = get_curl_info()
		funName = info[0]
		line = info[1]
		writeErrorMsg(ve,funName,line)
	lists = [rows,cols]
	return lists

#compution the matrix multiplication
def matrixCompution(l1:list,l2:list):
	rc1 = checkMatrix(l1)
	rc2 = checkMatrix(l2)
	if rc1 == None or rc2 == None or rc1[1] != rc2[0]:
		info = get_curl_info()
		funName = info[0]
		line = info[1]
		writeErrorMsg("the matrix is error",funName,line)
	gate = np.matrix(l1)
	qubit = np.matrix(l2)
	return (gate*qubit)

#if the input of GATE is in entanglement, then call this function
def handleQubits(gate:list , q:Qubit):
	qs = q.entanglement
	#get the index of the q in qs
	position = qs.getIndex(q)
	totalQubit = len(qs.qubitList)
	basic = 2 ** (totalQubit - position - 1)
	endResult = []
	for i in range(0,2 ** totalQubit):
		tmpResult = []
		for n in range(0,2 ** totalQubit):
			tmpResult.append([0])
		amplitude = qs.getAmp()[i]
		#pass the number i
		if amplitude == 0.0:
			endResult.append(tmpResult)
			continue
		#the target qubit is in |0>
		if i & basic == 0:
			tmpMatrix = [[1],[0]]
			result = matrixCompution(gate,tmpMatrix).tolist()
			try:
				result[0][0] = amplitude * result[0][0]
				result[1][0] = amplitude * result[1][0]
			except IndexError as ie:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ie,funName,line)	
			tmpResult[i][0] = result[0][0]
			tmpResult[i + basic][0] = result[1][0]
		#the target qubit is in |1>
		else:
			tmpMatrix = [[0],[1]]
			result = matrixCompution(gate,tmpMatrix).tolist()
			try:
				result[0][0] = amplitude * result[0][0]
				result[1][0] = amplitude * result[1][0]
			except IndexError as ie:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ie,funName,line)
			tmpResult[i][0] = result[1][0]
			tmpResult[i - basic][0] = result[0][0]	
			#print(newMatrix)
		endResult.append(tmpResult)
	sumResult = endResult[0]
	for r in range(1,len(endResult)):
		for x in range(0,len(endResult[r])):
			sumResult[x][0] += endResult[r][x][0]
	qs.setMatrix(sumResult)	
	return q	

#record the execution
#if the environment is wrong, will cause the EnvironmentError 
#if the return-value is None, then there is somrthing wrong with the Circuit instance, and the program should be end
#or the current qubit is not stored in the executeList
#1.recordSingleExecution: record single gate, i.e. X,Y..
#2.recordMultiExecution:record multi gate, i.e. CNOT..
def recordSingleExecution(gate:str,q:Qubit):
	circuit = checkEnvironment()
	#record the execution according to the qubit.ids
	ids = q.ids
	exeRecord = circuit.qubitExecuteList
	strs = gate + " " + str(ids)
	try:
		#a qubit can only be measured once, and once the qubit was measured, you can't act any gate on it.
		if "M "+str(ids) in exeRecord[q] or "qif "+str(ids) in exeRecord[q]:
			try:
				raise ValueError
			except ValueError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]		
				writeErrorMsg("Qubit: q"+ str(q.ids) + " has been measured! You can't act any gate on it!",funName,line)			
		exeRecord[q].append(strs)
	except KeyError as ke:
		info = get_curl_info()
		funName = info[0]
		line = info[1]
		writeErrorMsg("the current qubit is not stored in the execute list, please check your code!",funName,line)
	return circuit

def recordmultiExecution(gate:str,qs:list):
	circuit = checkEnvironment()
	if circuit != None:
		exeRecord = circuit.qubitExecuteList
		strs = gate + " "
		maxLength = 0
		#make up the multi gate string
		for i in range(0,len(qs)):
			ids = qs[i].ids
			try:
				length = len(exeRecord[qs[i]])
			except KeyError as ke:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("the current qubit is not stored in the execute list, please check your code",funName,line)			
			if maxLength < length:
				maxLength = length
			strs += str(ids)
			if i != len(qs) - 1:
				strs += ","
		#add the multi gate string to the execution of each qubit; 
		#and add NULL to the shorter execution to occupy the position so that we can draw the circuit easily
		for item in qs:
			while len(exeRecord[item]) < maxLength:
				tmpStr = "NULL " + str(item.ids)
				exeRecord[item].append(tmpStr)
			exeRecord[item].append(strs)
	return circuit

#add noise to the gate; the noise value is read from errorRate.cfg
#attention, only the execute mode is 'simulator', then the function is useful
def noise(qList:list,gate:list):
	circuit = checkEnvironment()
	error = 0.0
	if circuit.mode == "theory":
		return True
	elif circuit.mode == "simulator":
		qNum = len(qList)
		if qNum == 1:
			error = interactCfg.readCfgGE("single",qList[0].ids)
		elif qNum == 2:
			error = interactCfg.readCfgGE("multi")
		else:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("There are only single-qubit or double-qubit gate error!",funName,line)
		for i in range(0,len(gate)):
			for j in range(0,len(gate[0])):
				if gate[i][j] == 0:
					gate[i][j] = 1 - (1.0 * (1 - error))
				else:
					gate[i][j] = gate[i][j] * (1 - error)
		return True
	else:
		try:
			raise ExecuteModeError()
		except ExecuteModeError as em:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg(em,funName,line)

def X(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("X",q)
	if circuit == None:
		return False
	qs = q.entanglement
	X = [[0,1],[1,0]]
	noise([q],X)
	#the qubit is in entanglement
	if qs != None:
		q = handleQubits(X,q)
	else:
		result = matrixCompution(X,q.getMatrix()).tolist()
		q.setMatrix(result)		
	return q

def Y(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("Y",q)
	if circuit == None:
		return False
	qs = q.entanglement
	Y = [[0,-1j],[1j,0]]
	noise([q],Y)
	if qs != None:
		q = handleQubits(Y,q)
	else:
		result = matrixCompution(Y,q.getMatrix()).tolist()
		q.setMatrix(result)	
	return q

def Z(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("Z",q)
	if circuit == None:
		return False
	qs = q.entanglement
	Z = [[1,0],[0,-1]]
	noise([q],Z)
	if qs != None:
		q = handleQubits(Z,q)
	else:
		result = matrixCompution(Z,q.getMatrix()).tolist()
		q.setMatrix(result)		
	return q

def I(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("I",q)
	if circuit == None:
		return False
	qs = q.entanglement
	I = [[1,0],[0,1]]
	noise([q],I)
	if qs != None:
		q = handleQubits(I,q)
	else:
		result = matrixCompution(I,q.getMatrix()).tolist()
		q.setMatrix(result)	
	return q

def H(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("H",q)
	if circuit == None:
		return False
	qs = q.entanglement
	H = [[1/math.sqrt(2),1/math.sqrt(2)],[1/math.sqrt(2),-1/math.sqrt(2)]]
	noise([q],H)
	#the qubit is in entanglement
	if qs != None:
		q = handleQubits(H,q)
	else:
		result = matrixCompution(H,q.getMatrix()).tolist()
		q.setMatrix(result)	
	return q

def S(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("S",q)
	if circuit == None:
		return False
	qs = q.entanglement
	S = [[1,0],[0,1j]]
	noise([q],S)
	if qs != None:
		q = handleQubits(S,q)
	else:
		result = matrixCompution(S,q.getMatrix()).tolist()
		q.setMatrix(result)	
	return q

def Sd(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("Sd",q)
	if circuit == None:
		return False
	qs = q.entanglement
	Sd = [[1,0],[0,-1j]]
	noise([q],Sd)
	if qs != None:
		q = handleQubits(Sd,q)
	else:
		result = matrixCompution(Sd,q.getMatrix()).tolist()
		q.setMatrix(result)
	return q

def T(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("T",q)
	if circuit == None:
		return False
	qs = q.entanglement
	T = [[1,0],[0,(1+1j)/math.sqrt(2)]]
	noise([q],T)
	if qs != None:
		q = handleQubits(T,q)
	else:
		result = matrixCompution(T,q.getMatrix()).tolist()
		q.setMatrix(result)
	return q

def Td(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("Td",q)
	if circuit == None:
		return False
	qs = q.entanglement
	Td = [[1,0],[0,(1-1j)/math.sqrt(2)]]
	noise([q],Td)
	if qs != None:
		q = handleQubits(Td,q)
	else:
		result = matrixCompution(Td,q.getMatrix()).tolist()
		q.setMatrix(result)		
	return q

#return a Qubits, which has two entanglement qubit
#the two qubit can be independent qubits, or one of them are a part of engtanlement 
#the first qubit is the control-qubit, the second qubit is the target-qubit
def CNOT(q1:Qubit,q2:Qubit):
	checkType([q1,q2])
	circuit = recordmultiExecution("CNOT",[q1,q2])
	if circuit == None:
		return False
	CNOT = [[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]]
	noise([q1,q2],CNOT)
	q1Entangle = q1.entanglement
	q2Entangle = q2.entanglement
	#the twp qubits are single qubit
	if q1Entangle == None and q2Entangle == None:
		#construct the qubits
		qs = Qubits(q1,q2)
		result = matrixCompution(CNOT,qs.getMatrix()).tolist()
		qs.setMatrix(result)
		return qs
	#the two qubits are in the same qubits
	elif q1Entangle != None and q1Entangle == q2Entangle:
		qs = q1Entangle
		q = q2
	#at least one of the two qubits are in entanglement
	else:
		#append q into qs
		if q1Entangle == None:
			qs = q2Entangle
			q = q1
		else:
			qs = q1Entangle
			if q2Entangle == None:
				q = q2
			else:
				q = q2Entangle
		#add q to qs, no matter the type of q is Qubit or Qubits
		qs.addNewItem(q)
	#note that the position of q1 and q2 may be different from before
	q1Position = qs.getIndex(q1)
	q2Position = qs.getIndex(q2)
	#compute the result according to the function of CNOT
	#if the control qubit aren't in |1>
	if q1.getMatrix()[1] == 0:
		return qs
	totalQubit = len(qs.qubitList)
	basicNum = 2 ** (totalQubit - q1Position - 1)
	floatNum = 2 ** (totalQubit - q2Position - 1)
	swapList = []

	for i in range(basicNum, 2 ** totalQubit - floatNum):
		#decide whether i has been in the swapList
		whetherIn = False
		for item in swapList:
			if i in item:
				whetherIn = True
				break
		if whetherIn == True:
			continue
		#we should make sure that the q1Postionth bit of 'i' is 1; if so, it means that the control bit is |1>, and 
		#we need to flip the target; if not, the target qubit doesn't beed to be flipped 
		if i & basicNum != 0:
			tmpList = [i,i+floatNum]
			swapList.append(tmpList)
	newQSMatrix = qs.getMatrix()
	for lists in swapList:
		newQSMatrix[lists[0]],newQSMatrix[lists[1]] = newQSMatrix[lists[1]],newQSMatrix[lists[0]]
	qs.setMatrix(newQSMatrix)
	return qs

#sort the list1 according to the list2
def adjustOrder(list1:list,list2:list):
	for i in range(1,len(list2)):
		tmp = i-1
		while tmp >=0:
			if list2[tmp] > list2[i]:
				list2[i],list2[tmp] = list2[tmp],list2[i]
				list1[i],list1[tmp] = list1[tmp],list1[i]
				i = tmp
			tmp -= 1
	return True

#execute the measurement, the types of the input must be Qubit
def M(q:Qubit):
	#just store the M gate in circuit.qubitExecuteList, 
	#the measurement will actually occur when function circuit.execute is called  
	checkType([q])
	circuit = recordSingleExecution("M",q)
	#store the measurement qubit in the self.measureList
	circuit.measureList.append(q)
	if circuit == None:
		return None
	return q.degenerate()
	#return data.degenerate()

#Toffoli gate, three input and three output
def Toffoli(q1:Qubit,q2:Qubit,q3:Qubit):
	H(q3)
	CNOT(q2,q3)
	Td(q3)
	CNOT(q1,q3)
	T(q3)
	CNOT(q2,q3)
	Td(q3)
	CNOT(q1,q3)
	Td(q2)
	T(q3)
	CNOT(q1,q2)
	H(q3)
	Td(q2)
	CNOT(q1,q2)
	T(q1)
	S(q2)
	return True

#the follow is the control-flow
def qif(q:Qubit):
	checkType([q])
	circuit = recordSingleExecution("qif",q)
	circuit.measureList.append(q)
	q = q.degenerate()
	#print(ql[0])
	return q