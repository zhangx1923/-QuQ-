#!/usr/bin/python3
from baseGate import *
from Gate import *
import copy
#only X,Y,Z,I,H,S,Sd,T,Td,CNOT is allowed
import re

#delay measure opertor class
class DMO:
	def __init__(self,ql,vl):
		#storage the control-qubit list
		self.DMOql = ql
		self.split = SplitGate()
		self.DMOvl = vl

	#get the info about the function name and the line number
	def get_curl_info(self):
		try:
			raise Exception
		except:
			f = sys.exc_info()[2].tb_frame.f_back
		return [f.f_code.co_name, f.f_lineno]

	#set the name of the control qubit gate:if there are 3 qubit in self.DMOql and vl = [1,0,1],
	#then the full name should be c1-c0-c1-SingleQubitGate.
	def __fullGName(self,gn:str,vl:list,ql:list):
		name = ""
		for i in range(0,len(ql)):
			name += "c"
			if len(vl) == 1:
				j = 0
			else:
				j = i
			if vl[j] == 0:
				name += "0"
			else:
				name += "1"
			name += "-"
		cgn = name[0:len(name)-1]
		return self.__setFullGName(cgn,gn)

	#get the full name of the multi-controlled gate
	def __setFullGName(self,cgn:str,gn:str):
		return (cgn + "-" + gn)

	#the "cq" is the control-qubit of the CNOT gate
	def __Operator(self,gateName:str,tq:Qubit,cq = None):
		ql = self.DMOql.copy()
		vl = self.DMOvl.copy()
		QASM = ""
		if cq != None:
			#CNOT gate call this function. We shoulde convert the format of CNOT
			ql.append(cq)
			vl.append(1)
		#CNOT gate
		if gateName == "c1-X":
			return CNOT(ql[0],tq)
		fullGName = self.__fullGName(gateName,vl,ql)
		if re.search(r'^(c\d-).$',fullGName) != None:
			QASM = self.split.CU(fullGName,ql[0],tq,vl)
		else:
			#split the MCU and execute the computation
			QASM = self.split.MCU(fullGName,ql,tq,vl)
		#the return value is a list consisted of all the control-qubits and the target-qubit
		return self.split.execute(QASM,ql,[tq],fullGName)		

	def X(self,q:Qubit):
		gateName = "X"
		return self.__Operator(gateName,q)

	def Y(self,q:Qubit):
		gateName = "Y"
		return self.__Operator(gateName,q)

	def Z(self,q:Qubit):
		gateName = "Z"
		return self.__Operator(gateName,q)

	def H(self,q:Qubit):
		gateName = "H"
		return self.__Operator(gateName,q)

	def S(self,q:Qubit):
		gateName = "S"
		return self.__Operator(gateName,q)

	def Sd(self,q:Qubit):
		gateName = "Sd"
		return self.__Operator(gateName,q)

	def T(self,q:Qubit):
		gateName = "T"
		return self.__Operator(gateName,q)

	def Td(self,q:Qubit):
		gateName = "Td"
		return self.__Operator(gateName,q)

	def CNOT(self,q1:Qubit,q2:Qubit):
		gateName = "X"
		return self.__Operator(gateName,q2,q1)



	
		