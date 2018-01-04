#!/usr/bin/python3
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
import cmath

allowGate = {
	'X':1,
	'Y':1,
	'Z':1,
	'CNOT':2,
	'S':1,
	'Sd':1,
	'T':1,
	'Td':1,
	'H':1,
	'I':1,
	'M':1
}

class Gate:
	def __init__(self,ql:list,gate:list,gateName:str):
		self.gateName = gateName
		self.gate = gate
		if self.__checkType(ql):
			self.ql = ql
		
	
	def singleOperator(self,record = True):
		q = self.ql[0]
		circuit = self.recordSingleExecution(record)
		if circuit == None:
			return False
		qs = q.entanglement
		noise = Noise(self.ql)
		v = noise.simNoise(self.gate)
		del noise
		#the qubit is in entanglement
		if qs != None:
			q = self.__handleQubits(v,q)
		else:
			result = self.__matrixCompution(v,q.getMatrix()).tolist()
			q.setMatrix(result)		
		return q
	
	def CNOTOperator(self,record = True):
		q1 = self.ql[0]
		q2 = self.ql[1]
		#q1 is same with q2
		if id(q1) == id(q2):
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("The control-qubit can't be same with the target-qubit of CNOT gate!",funName,line)	
		circuit = self.recordmultiExecution(record)
		if circuit == None:
			return False
		noise = Noise(self.ql)
		v = noise.simNoise(self.gate)
		del noise
		q1Entangle = q1.entanglement
		q2Entangle = q2.entanglement
		#the twp qubits are single qubit
		if q1Entangle == None and q2Entangle == None:
			#construct the qubits
			qs = Qubits(q1,q2)
			result = self.__matrixCompution(v,qs.getMatrix()).tolist()
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

	def MOperator(self,auQubit = False):
		q = self.ql[0]
		#just store the M gate in circuit.qubitExecuteList, 
		#the measurement will actually occur when function circuit.execute is called  
		if auQubit == False:
			circuit = self.recordSingleExecution()
			#store the measurement qubit in the self.measureList
			circuit.measureList.append(q)
			if circuit == None:
				return None
		return q.degenerate()
		#return data.degenerate()

	#get the info about the function name and the line number
	def get_curl_info(self):
		try:
			raise Exception
		except:
			f = sys.exc_info()[2].tb_frame.f_back
		return [f.f_code.co_name, f.f_lineno]

	#check the number of rows and cols, the result must be n*1 or m*m, otherwise raise an error
	def __checkMatrix(self,m:list):
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
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg(ke,funName,line)
		except ValueError as ve:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg(ve,funName,line)
		lists = [rows,cols]
		return lists

	#check the type of the input, only Qubit is allowed.
	def __checkType(self,ql:list):
		for q in ql:
			types = type(q)
			if types == Bit:
				try:
					raise TypeError
				except TypeError:
					info = self.get_curl_info()
					funName = info[0]
					line = info[1]
					writeErrorMsg("Bit " + str(q.ids) + " has been meaured! You can't act any quntum gate on it!",funName,line)
			if types != Qubit:
				try:
					raise TypeError
				except TypeError:
					info = self.get_curl_info()
					funName = info[0]
					line = info[1]
					writeErrorMsg("The type of the date should be Qubit!",funName,line)	
		try:
			qN = allowGate[self.gateName]
			if qN != len(ql) or 2**qN != len(self.gate):
				raise ValueError
		except KeyError:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("Gate: " + self.gateName + " hasn't been defined!",funName,line)
		except ValueError:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("Gate " + self.gateName + " can't act on the quantum state composed of " + str(qN) + " qubits!",funName,line)	
		return True	

	#compution the matrix multiplication
	def __matrixCompution(self,l1:list,l2:list):
		rc1 = self.__checkMatrix(l1)
		rc2 = self.__checkMatrix(l2)
		if rc1 == None or rc2 == None or rc1[1] != rc2[0]:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("the matrix is error",funName,line)
		gate = np.matrix(l1)
		qubit = np.matrix(l2)
		return (gate*qubit)

	#if the input of GATE is in entanglement, then call this function
	def __handleQubits(self,gate:list , q:Qubit):
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
				result = self.__matrixCompution(gate,tmpMatrix).tolist()
				try:
					result[0][0] = amplitude * result[0][0]
					result[1][0] = amplitude * result[1][0]
				except IndexError as ie:
					info = self.get_curl_info()
					funName = info[0]
					line = info[1]
					writeErrorMsg(ie,funName,line)	
				tmpResult[i][0] = result[0][0]
				tmpResult[i + basic][0] = result[1][0]
			#the target qubit is in |1>
			else:
				tmpMatrix = [[0],[1]]
				result = self.__matrixCompution(gate,tmpMatrix).tolist()
				try:
					result[0][0] = amplitude * result[0][0]
					result[1][0] = amplitude * result[1][0]
				except IndexError as ie:
					info = self.get_curl_info()
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
	def recordSingleExecution(self,record = True):
		q = self.ql[0]
		circuit = checkEnvironment()
		if record == False:
			return circuit
		#record the execution according to the qubit.ids
		ids = q.ids
		exeRecord = circuit.qubitExecuteList
		strs = self.gateName + " " + str(ids)
		try:
			#a qubit can only be measured once, and once the qubit was measured, you can't act any gate on it.
			if "M "+str(ids) in exeRecord[q]:
				try:
					raise ValueError
				except ValueError:
					info = self.get_curl_info()
					funName = info[0]
					line = info[1]		
					writeErrorMsg("Qubit: q"+ str(q.ids) + " has been measured! You can't act any gate on it!",funName,line)			
			exeRecord[q].append(strs)
		except KeyError as ke:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("the current qubit is not stored in the execute list, please check your code!",funName,line)
		return circuit

	def recordmultiExecution(self,record = True):
		circuit = checkEnvironment()
		if record == False:
			return circuit
		if circuit != None:
			exeRecord = circuit.qubitExecuteList
			strs = self.gateName + " "
			maxLength = 0
			#make up the multi gate string
			for i in range(0,len(self.ql)):
				ids = self.ql[i].ids
				try:
					length = len(exeRecord[self.ql[i]])
				except KeyError as ke:
					info = self.get_curl_info()
					funName = info[0]
					line = info[1]
					print(exeRecord)
					print(self.ql[i])
					writeErrorMsg("Qubit: q" + str(self.ql[i].ids) + " is not stored in the execute list, please check your code!",funName,line)			
				if maxLength < length:
					maxLength = length
				strs += str(ids)
				if i != len(self.ql) - 1:
					strs += ","
			#add the multi gate string to the execution of each qubit; 
			#and add NULL to the shorter execution to occupy the position so that we can draw the circuit easily
			for item in self.ql:
				while len(exeRecord[item]) < maxLength:
					tmpStr = "NULL " + str(item.ids)
					exeRecord[item].append(tmpStr)
				exeRecord[item].append(strs)
		return circuit



	#the following gates aren't allowd in QASM and ibm quantum chip for now
	# #theta is expressed in radian
	# def Rx(q:Qubit,theta):
	# 	checkType([q])
	# 	circuit = recordSingleExecution("Rx",q)
	# 	if circuit == None:
	# 		return False
	# 	qs = q.entanglement
	# 	Rx = [[math.cos(theta/2),math.sin(theta/2)*-1j],[math.sin(theta/2)*-1j,math.cos(theta/2)]]
	# 	noise([q],Rx)
	# 	if qs != None:
	# 		q = handleQubits(Rx,q)
	# 	else:
	# 		result = matrixCompution(Rx,q.getMatrix()).tolist()
	# 		q.setMatrix(result)
	# 	return q

	# #theta is expressed in radian
	# def Ry(q:Qubit,theta):
	# 	checkType([q])
	# 	circuit = recordSingleExecution("Ry",q)
	# 	if circuit == None:
	# 		return False
	# 	qs = q.entanglement
	# 	Ry = [[math.cos(theta/2),-math.sin(theta/2)],[math.sin(theta/2,math.cos(theta/2))]]
	# 	noise([q],Ry)
	# 	if qs != None:
	# 		q = handleQubits(Ry,q)
	# 	else:
	# 		result = matrixCompution(Ry,q.getMatrix()).tolist()
	# 		q.setMatrix(result)
	# 	return q

	# #theta is expressed in radian
	# def Rz(q:Qubit,theta):
	# 	checkType([q])
	# 	circuit = recordSingleExecution("Rz",q)
	# 	if circuit == None:
	# 		return False
	# 	qs = q.entanglement
	# 	pows = (-1)*theta/2j
	# 	Rz = [[cmath.exp(-pows),0],[0,cmath.exp(pows)]]
	# 	noise([q],Rz)
	# 	if qs != None:
	# 		q = handleQubits(Rz,q)
	# 	else:
	# 		result = matrixCompution(Rz,q.getMatrix()).tolist()
	# 		q.setMatrix(result)
	# 	return q

#add noise to the gate; the noise value is read from errorRate.cfg
#attention, only the execute mode is 'simulator', then the function is useful
class Noise:
	def __init__(self,qList:list):
		circuit = checkEnvironment()
		self.error = 0.0
		self.qList = qList
		if circuit.mode == "theory":
			pass
		elif circuit.mode == "simulator":
			qNum = len(qList)
			if qNum == 1:
				self.error = interactCfg.readCfgGE("single",qList[0].ids)
			elif qNum == 2:
				self.error = interactCfg.readCfgGE("multi")
			else:
				info = self.get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("There are only single-qubit or double-qubit gate error!",funName,line)
		else:
			try:
				raise ExecuteModeError()
			except ExecuteModeError as em:
				info = self.get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(em,funName,line)

	def simNoise(self,gate:list):
		if self.error == 0.0:
			return gate
		else:
			for i in range(0,len(gate)):
				for j in range(0,len(gate[0])):
					if gate[i][j] == 0:
						gate[i][j] = 1 - (1.0 * (1 - self.error))
					else:
						gate[i][j] = gate[i][j] * (1 - self.error)
			return gate




