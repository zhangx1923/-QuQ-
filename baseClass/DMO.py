#!/usr/bin/python3
from baseGate import *
from Gate import *
import copy
#only X,Y,Z,I,H,S,Sd,T,Td,CNOT is allowed
import re


#delay measure opertor class used in DMif
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
	def Operator(self,gateName:str,tq:Qubit,cq = None,angle = None):

		ql = self.DMOql.copy()
		vl = self.DMOvl.copy()

		QASM = ""
		if cq != None:
			#CNOT gate call this function. We shoulde convert the format of CNOT
			ql.append(cq)
			vl.append(1)
		fullGName = self.__fullGName(gateName,vl,ql)
		#CNOT gate
		if fullGName == "c1-X":
			return CNOT(ql[0],tq)

		#the return value is a list consisted of all the control-qubits and the target-qubit	
		if re.match(r'^(c\d-){1}.{1,2}$',fullGName) != None:
			#split the CU and execute the computation
			return self.split.CU(fullGName,ql[0],tq,vl,angle,True)
		else:
			#split the MCU and execute the computation
			return self.split.MCU(fullGName,ql,tq,vl,angle,True)


	def X(self,q:Qubit):
		gateName = "X"
		return self.Operator(gateName,q)

	def Y(self,q:Qubit):
		gateName = "Y"
		return self.Operator(gateName,q)

	def Z(self,q:Qubit):
		gateName = "Z"
		return self.Operator(gateName,q)

	def H(self,q:Qubit):
		gateName = "H"
		return self.Operator(gateName,q)

	def S(self,q:Qubit):
		gateName = "S"
		return self.Operator(gateName,q)

	def Sd(self,q:Qubit):
		gateName = "Sd"
		return self.Operator(gateName,q)

	def T(self,q:Qubit):
		gateName = "T"
		return self.Operator(gateName,q)

	def Td(self,q:Qubit):
		gateName = "Td"
		return self.Operator(gateName,q)

	def CNOT(self,q1:Qubit,q2:Qubit):
		gateName = "X"
		return self.Operator(gateName,q2,q1)

	def Rz(self,phi,q:Qubit):
		gateName = "Rz"
		return self.Operator(gateName,q,None,phi)

	def Ry(self,phi,q:Qubit):
		gateName = "Ry"
		return self.Operator(gateName,q,None,phi)



#measure operator class used in Mif and Qif
class MO(DMO):
	def __init__(self,ql,vl):
		self.MOql = ql
		self.MOvl = vl
		self.header = ""
		bitList = self.MO(ql,vl)
		self.bool = True
		
		if len(vl) == 1:
			for bit in bitList:
				if bit.value != vl[0]:
					self.bool = False
					break
		else:
			for j in range(0,len(bitList)):
				if bitList[j] != vl[j]:
					self.bool = False
					break


	#this kind of measure is used in Mif;
	#ql means the qubit list need be measured; and the vl stands for the target result of measurement
	def MO(self,ql:list,vl:list):
		if len(ql) != len(vl):
			try:
				raise CodeError("The element number of Qubit List should be same with Value List!")
			except CodeError as ce:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ce,funName,line)
		bitList = []
		for q in ql:
			bitList.append(M(q,False))

		#construct the if statement
		# ifstr = "if ("
		# for i in range(0,len(ql)):
		# 	c = str(ql[i].ids)
		# 	tmp = "c[" + c + "]==" + str(vl[i])
		# 	if i != len(ql)-1:
		# 		tmp += " && "
		# 	ifstr += tmp
		# ifstr += "){}"
		ifstr = ""
		for v in vl:
			ifstr += "M" + str(v) + "-"
		self.header = ifstr

		return bitList

	def recordGate(self,gate:str,ql:list):
		circuit = checkEnvironment()
		maxL = 0
		content = gate + " "
		for i in range(0,len(ql)):
			length = len(circuit.qubitExecuteList[ql[i]])
			maxL = max(length,maxL)
			content += str(ql[i].ids)
			if i != len(ql)-1:
				content += ','

		for q in ql:
			try:
				while len(circuit.qubitExecuteList[q]) < maxL:
					circuit.qubitExecuteList[q].append("NULL "+str(q.ids))
				circuit.qubitExecuteList[q].append(content)
				if circuit.withOD:
					while len(circuit.qubitExecuteListOD[q]) < maxL:
						circuit.qubitExecuteListOD[q].append("NULL "+str(q.ids))
					circuit.qubitExecuteListOD[q].append(content)
			except KeyError:
				info = get_curl_info()
				writeErrorMsg("Qubit: q" + str(q.ids) + " hasn't been stored in circuit.qubitExeucetList!\
					" ,info[0],info[1])

		# print(circuit.qubitExecuteList)
		# print(circuit.qubitExecuteListOD)

	#overwrite the operator method
	def Operator(self,gateName:str,tq:Qubit,cq = None,angle = None):
		if cq != None:
			gateName = "c1-X"
		fullGName = self.header + gateName

		#no matter what's self.bool, record the Measure Operator in qubitExecuteList
		if self.bool:
			#if the last position of the full gate name is 1, then the gate is executed
			fullGName += "1"
		else:
			#if the last position of the gate name is 0, then the gate isn't executed
			fullGName += "0"
		ql = self.MOql.copy()
		if cq != None:
			ql.append(cq)
		ql.append(tq)
		self.recordGate(fullGName,ql)

		#execute the operator according to self.bool
		if gateName == "c1-X":
			gateName = "CNOT"
		q = None
		if self.bool:
			#execute the gate function in Gate.py
			if cq == None:
				exeStr = "q = " + gateName + "(tq,False,True)"
			else:
				exeStr = "q = " + gateName + "(cq,tq,False,True)"
			#print(exeStr)
			exec(exeStr)
		else:
			#don't exeucte the gate
			pass

		return q

	#the single gate operator and the double gate operator were inherited from DMO class
	#def X
	#def Y
	#def Z
	#def H
	#def S
	#def Sd
	#def T
	#def Td
	#def CNOT
	#def Rz
	#def Ry
	#def get_curl_info

	
		


#delay measure operator class used in Qwhile
class QWMO(DMO):
	def __init__(self,ql,vl,angle):
		DMO.__init__(ql,vl)
		self.angle = angle

	def end(self):
		for q in ql:
			Rx(angle,q)
		if True:
			return True
		else:
			return False