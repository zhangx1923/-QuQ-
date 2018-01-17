#!/usr/bin/python3
import sys
import os
sys.path.append('../tools/')
from interactCfg import *
from Bit import Bit
from Qubit import *
from helperFunction import *
#from Circuit import Circuit
from Error import *
import numpy as np
import math
import cmath

#baseGate.py and Gate.py will use the DIC
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
	'M':1,
	'Rz':1,
	'Ry':1,
	#'Rx':1
}

class Gate:
	def __init__(self,ql:list,gate:list,gateName:str):
		self.gateName = gateName
		self.gate = gate
		if self.__checkType(ql):
			self.ql = ql
		
	#the method has two parameters:
	#the former stands for whether record the gate in qubitExecuteList
	#the latter stands fot the angle parameter of the gate, 
	#only the parameter of Rx,Ry and Rz gate isn't None 
	def singleOperator(self,record = True,angle = None,forceQuit = False):
		q = self.ql[0]
		if angle != None and self.gateName not in ["Rx","Ry","Rz"]:
			try:
				raise GateNameError()
			except GateNameError as gne:
				info = self.get_curl_info()
				writeErrorMsg(gne,info[0],info[1])

		circuit = self.recordSingleExecution(record,angle,forceQuit)

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
	
	def CNOTOperator(self,record = True,forceQuit = False):
		q1 = self.ql[0]
		q2 = self.ql[1]

		#q1 is same with q2
		try:
			if id(q1) == id(q2):
				raise CodeError("The control-qubit can't be same with the target-qubit of CNOT gate!")
		except CodeError as ce:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg(ce,funName,line)	
		
		circuit = self.recordmultiExecution(record,None,forceQuit)

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

	def MOperator(self,result = True):
		q = self.ql[0]
		#just store the M gate in circuit.qubitExecuteList, 
		#the measurement will actually occur when function circuit.execute is called  
		if q.tag == "AC":
			circuit = self.recordSingleExecution()
		if result == True:
			#store the measurement qubit in the self.measureList
			circuit.measureList.append(q)

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
			#print(types)
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
	def recordSingleExecution(self,record = True,angle = None,forceQuit = False):
		#only Mif and Qif will give the forceQuit to True
		#if forceQuit is true, then end this method directly
		if forceQuit:
			return None
		c = self.__recordSE(record,None,angle)
		if c.withOD:
			return self.__recordSE(True,c.qubitExecuteListOD,angle)
		return c

	def recordmultiExecution(self,record = True,angle = None,forceQuit = False):
		if forceQuit:
			return None
		c = self.__recordME(record,None,angle)
		if c.withOD:
			return self.__recordME(True,c.qubitExecuteListOD,angle)
		return c

	def __recordSE(self,record,executeList = None,angle = None):
		q = self.ql[0]
		circuit = checkEnvironment()
		if record == False:
			return circuit
		#record the execution according to the qubit.ids
		ids = q.ids

		if executeList == None:
			executeList = circuit.qubitExecuteList
		else:
			#if the parameter "executeList" isn't None
			#then it means that we are recording the executive record in circuit.qubitexecutelistOD
			if self.gateName not in allowGate:
				return circuit
		#print(self.gateName)

		if angle == None:
			strs = self.gateName + " " + str(ids)
		else:
			#change format of the parameter "angle" to multiples of "PI"
			tmpAngle = ""
			multiplesList = str(angle / math.pi).split(".")
			if len(multiplesList[1]) > 3:
				tmpAngle = multiplesList[0] + "." + multiplesList[1][0:3]
			else:
				tmpAngle = multiplesList[0] + "." + multiplesList[1]
			angleS = tmpAngle + "*pi"
			strs = self.gateName + "(" + angleS + ") " + str(ids)

		try:
			#a qubit can only be measured once, and once the qubit was measured, you can't act any gate on it.
			if "M "+str(ids) in executeList[q]:
				try:
					raise ValueError
				except ValueError:
					info = self.get_curl_info()
					funName = info[0]
					line = info[1]		
					writeErrorMsg("Qubit: q"+ str(q.ids) + " has been measured! You can't act any gate on it!",funName,line)			

			executeList[q].append(strs)

		except KeyError as ke:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("The current qubit is not stored in the execute list, please check your code!",funName,line)
		return circuit

	def __recordME(self,record,executeList = None,angle = None):
		circuit = checkEnvironment()
		if record == False:
			return circuit
		if circuit != None:
			if executeList == None:
				executeList = circuit.qubitExecuteList
			else:
				#if the parameter "executeList" isn't None
				#then it means that we are recording the executive record in circuit.qubitexecutelistOD
				if self.gateName not in allowGate:
					return circuit

			#print(exeRecord)
			if angle == None:
				strs = self.gateName + " "
			else:
				#change format of the parameter "angle" to multiples of "PI"
				tmpAngle = ""
				multiplesList = str(angle / math.pi).split(".")
				if len(multiplesList[1]) > 3:
					tmpAngle = multiplesList[0] + "." + multiplesList[1][0:3]
				else:
					tmpAngle = multiplesList[0] + "." + multiplesList[1]
				angleS = tmpAngle + "*pi"
				strs = self.gateName + "(" + angleS + ") "

			maxLength = 0
			#make up the multi gate string
			for i in range(0,len(self.ql)):
				ids = self.ql[i].ids
				try:
					length = len(executeList[self.ql[i]])
					if "M " + str(ids) in executeList[self.ql[i]]:
						raise ValueError
				except KeyError as ke:
					info = self.get_curl_info()
					funName = info[0]
					line = info[1]
					writeErrorMsg("Qubit: q" + str(self.ql[i].ids) + " is not stored in the execute list, please check your code!",funName,line)			
				except ValueError:
					info = self.get_curl_info()
					funName = info[0]
					line = info[1]		
					writeErrorMsg("Qubit: q"+ str(self.ql[i].ids) + " has been measured! You can't act any gate on it!",funName,line)						
				if maxLength < length:
					maxLength = length
				strs += str(ids)
				if i != len(self.ql) - 1:
					strs += ","
			#add the multi gate string to the execution of each qubit; 
			#and add NULL to the shorter execution to occupy the position so that we can draw the circuit easily
			for item in self.ql:
				while len(executeList[item]) < maxLength:
					tmpStr = "NULL " + str(item.ids)
					executeList[item].append(tmpStr)
				executeList[item].append(strs)
		return circuit

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




