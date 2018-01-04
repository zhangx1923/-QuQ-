#!/usr/bin/python3
from baseGate import *
from Gate import *
import copy
#only X,Y,Z,I,H,S,Sd,T,Td,CNOT is allowed

#delay measure opertor class
class DMO:
	def __init__(self,ql,vl):
		n = len(ql) + 1
		I = [[1,0],[0,1]]
		tmp = I.copy()
		#this variable is used to storage the position of the target qubit 
		self.DMOposition = 0
		for i in range(0,n-1):
			tmp = constructPM(tmp,I)
			if len(vl) == 1:
				value = vl[0]
			else:
				value = vl[i]
			if value == 1:
				exp = n-1-i
				self.DMOposition += 2 ** exp
		self.DMOv = tmp
		#storage the control-qubit list
		self.DMOql = ql
		self.__setControlGName(vl)
		self.split = SplitGate()

	#get the info about the function name and the line number
	def get_curl_info(self):
		try:
			raise Exception
		except:
			f = sys.exc_info()[2].tb_frame.f_back
		return [f.f_code.co_name, f.f_lineno]

	#construct the matrix of the multi-controlled gate
	def __constructM(self,v:list):
		mx = copy.deepcopy(self.DMOv)
		try:
			mx[self.DMOposition][self.DMOposition] = v[0][0]
			mx[self.DMOposition][self.DMOposition+1] = v[0][1]
			mx[self.DMOposition+1][self.DMOposition] = v[1][0]
			mx[self.DMOposition+1][self.DMOposition+1] = v[1][1]
			return mx
		except IndexError:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("The matrix of the controlled-operator doesn't \
				have line" + str(self.DMOposition) + " or line" + str(self.DMOposition+1) + "!",funName,line)	

	#set the name of the control qubit gate:if there are 3 qubit in self.DMOql and vl = [1,0,1],
	#then the full name should be c1-c0-c1-SingleQubitGate. This function should set self.cgn = c1-c0-c1
	def __setControlGName(self,vl:list):
		name = ""
		for i in range(0,len(self.DMOql)):
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
		self.cgn = name[0:len(name)-1]

	#get the full name of the multi-controlled gate
	def __getFullGName(self,gn:str):
		return (self.cgn + "-" + gn)

	def X(self,q:Qubit):
		ql = self.DMOql.copy()
		#CNOT gate
		if len(ql) == 1 and self.DMOv[0] == 1:
			return CNOT(ql[0],q)

		X = [[0,1],[1,0]]
		cG = self.__constructM(X)
		ql.append(q)
		fullGName = self.__getFullGName('X')
		#append the multi-controlled gate to Dict "allowGate", which is defined in baseGate.py
		allowGate[fullGName] = len(ql)
		#init the Gate instance
		gate = Gate(ql,cG,fullGName)
		c = gate.recordmultiExecution()

		return self.splitAndExe(ql,fullGName)

	def CNOT(self,q1:Qubit,q2:Qubit):
		ql = self.DMOql.copy()
		#convert the CNOT gate to c1-X, then the code is same with the DMO.singleQubit
		return True


	#split the multi-controlled gate to the gate set(H,Z,X,Y,S,Sd,T,Td,CNOT), and Execute the gate sequence
	#the paremeter 'gn' stands for Full Multi-Controlled Gate Name
	#and the parameter 'ql' stands for the qubit list
	def splitAndExe(self,ql:list,gn:str):
		qGL = gn.split("-")
		N = len(qGL)
		
		actualN = 2 * N - 3
		#construct the c1-c1-c1-c1...-U should with the help of auxiliary qubits
		#and the initial state of all the auxiliary qubits should be |0>
		for k in range(0,actualN - N):
			auxQ = Qubit()
			position = 2 * (k+1)
			ql.insert(position,auxQ)
		for j in range(2,actualN,2):
			Toffoli(ql[j-2],ql[j-1],ql[j])

		#return the target qubit 	
		return ql[len(ql)-1]


	
		