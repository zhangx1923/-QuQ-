#!/usr/bin/python3
from baseGate import *

#the dict will be used in SplitGate of Gate.py
elementGate = {
	"Y":"Sd tq-0;CNOT cq-0,tq-0;S tq-0;",
	"Z":"H tq-0;CNOT cq-0,tq-0;H tq-0;",
	"H":"H tq-0;Sd tq-0;CNOT cq-0,tq-0;H tq-0;T tq-0;CNOT cq-0,tq-0;T tq-0;H tq-0;S tq-0;X tq-0;S cq-0;",
	"S":"T tq-0;CNOT cq-0,tq-0;Td tq-0;CNOT cq-0,tq-0;",
	"Sd":"Td tq-0;CNOT cq-0,tq-0;T tq-0;CNOT cq-0,tq-0;",
	"T":"Rz(math.pi/8) tq-0;CNOT cq-0,tq-0;Rz(-math.pi/8) tq-0;CNOT cq-0,tq-0;",
	"Td":"Rz(-math.pi/8) tq-0;CNOT cq-0,tq-0;Rz(math.pi/8) tq-0;CNOT cq-0,tq-0;",
	"Rz":"Rz(alpha) tq-0;CNOT cq-0,tq-0;Rz(beta) tq-0;CNOT cq-0,tq-0;",
	"Ry":"Ry(alpha) tq-0;CNOT cq-0,tq-0;Ry(beta) tq-0;CNOT cq-0,tq-0;",
	#the alpha and beta is a angle, and will be replaced by parameter of CU and MCU
	#alpha = -beta
}

#split a gate to the elements in the Dic "allowGate"
class SplitGate:
	def __init__(self):
		self.allowSet = []
		for key in allowGate:
			if key == 'M':
				continue
			self.allowSet.append(key)

	#get the info about the function name and the line number
	def get_curl_info(self):
		try:
			raise Exception
		except:
			f = sys.exc_info()[2].tb_frame.f_back
		return [f.f_code.co_name, f.f_lineno]

	#convert the c0 to c1 by addind a X gate on the control-qubit
	#or restore the state of the control-qubit
	def __convert0to1(self,cql:list,vl:list):
		QASM = ""
		for i in range(0,len(cql)):
			if len(vl) == 1:
				j = 0
			else:
				j = i
			if vl[j] == 0:
				QASM += "X cq-" + str(i) + ";"
		#then the circuit is equal to c1-c1-c1-c1...-U
		return QASM

	#C-U means that this is a controlled-gate with only one control qubit
	#return value is the QASM code
	def CU(self,gateName:str,cq:Qubit,tq:Qubit,vl:list,angle = None,executeStatus = False):
		QASM = ""
		QASM += self.__convert0to1([cq],vl)
		#all the control-gate can be split into CNOT and single-gate
		singleGate = gateName.split("-")[1]
		#the singleGate can only be an element of the set "Y,Z,H,S,Sd,T,Td,Rz,Ry"
		tmpQASM = ""
		#ignore the global phase
		try:
			tmpQASM = elementGate[singleGate]
			if angle != None:
				#the U is Ry or Rz
				angleN = angle/2
				tmpQASM = tmpQASM.replace("alpha",str(angleN),1)
				tmpQASM = tmpQASM.replace("beta",str(-angleN),1)
		except KeyError:
			info = get_curl_info()
			writeErrorMsg("Gate: "+ singleGate + " hasn't been definded in Dict:elementGate in defines.py!",info[0],info[1])
		QASM += tmpQASM
		QASM += self.__convert0to1([cq],vl)
		if executeStatus:
			return self.execute(QASM,[cq],[tq],gateName,angle)
		return QASM

	#MC-U means that this is a controlled-gate with more than one control qubit
	#MCU will be split to Toffoli and CCU
	#return value is the QASM code of this MCU
	def MCU(self,gateName:str,cql:list,tq:Qubit,vl:list,angle = None,executeStatus = False):
		if gateName == "c1-c1-X" or gateName == "Toffoli":
			QASM = self.__Toffoli(["cq-0","cq-1"],"tq-0")
		else:
			#the multi-controlled qubit gate "c1-c1-c1-c1...-X" can be split to a series of Toffoli gates
			#then c1-c1-c1-c1...-U is same with this case
			N = len(cql) + 1
			actualN = 2 * N -3
			for i in range(0,actualN-1):
				if i % 2 == 0 and i > 0:
					#insert an auxiliary qubit 
					cql.insert(i,Qubit(True)) 
					#the auxiliary qubit need NOT to use X gate to fix the state
					vl.insert(i,1)
			QASM = ""
			QASM += self.__convert0to1(cql,vl)
			for j in range(2,actualN-1,2):
				QASM += self.__Toffoli(["cq-"+str(j-2),"cq-"+str(j-1)],"cq-"+str(j))
			#the rest of the circuit is CCU
			#the CCU is Toffoli
			singleG = gateName.split("-")[-1]
			if singleG == "X":
				QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
			else:
				#the general case: CCU
				try:
					if angle != None:
						#the U is Rz or Ry
						angleN = angle/2
						if singleG == "Rz":
							QASM += "Rz("+ str(angleN) +") tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "Rz("+ str(-angleN) +") tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
						elif singleG == "Ry":
							QASM += "Ry("+ str(angleN) +") tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "Ry("+ str(-angleN) +") tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
						else:
							raise GateNameError(singleGate)					
					else:
						if singleG == "Y":
							QASM += "Sd tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "S tq-0;"
						elif singleG == "Z":
							QASM += "H tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "H tq-0;"
						elif singleG == "H":
							QASM += "H tq-0;Sd tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "H tq-0;T tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "T tq-0;H tq-0;S tq-0;X tq-0;"
							QASM += "S cq-"+str(actualN-3)+";S cq-"+str(actualN-2)+";"
						elif singleG == "S":
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "Td tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "T tq-0;T cq-"+str(actualN-3)+";T cq-"+str(actualN-2)+";"
						elif singleG == "Sd":
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "T tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "Td tq-0;Td cq-"+str(actualN-3)+";Td cq-"+str(actualN-2)+";"
						elif singleG == "T":
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "Rz(-math.pi/8) tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "Rz(math.pi/8) tq-0;Rz(math.pi/8) cq-"+str(actualN-3)+";Rz(math.pi/8) cq-"+str(actualN-2)+";"
						elif singleG == "Td":
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "Rz(math.pi/8) tq-0;"
							QASM += self.__Toffoli(["cq-"+str(actualN-3),"cq-"+str(actualN-2)],"tq-0")
							QASM += "Rz(-math.pi/8) tq-0;Rz(-math.pi/8) cq-"+str(actualN-3)+";Rz(-math.pi/8) cq-"+str(actualN-2)+";"
						else:
							raise GateNameError(singleG)
				except GateNameError as gne:
					info = get_curl_info()
					writeErrorMsg(gne,info[0],info[1])			
				pass
			QASM += self.__convert0to1(cql,vl)
			#print(QASM)
		
		if executeStatus:
			return self.execute(QASM,cql,[tq],gateName,angle)
		return QASM

	#special-case, this is an important element in constructing MCU
	#cqIndexL stands for the list of the index of the control-qubits in the cqL
	#tqIndex stands for the index of the target qubit in the tqL 
	def __Toffoli(self,cqIndexL:list,id_tq:str):
		id_cq0 = cqIndexL[0]
		id_cq1 = cqIndexL[1]
		QASM = "H "+id_tq+";CNOT "+id_cq1
		QASM += ","+id_tq+";Td "+id_tq+";CNOT "+id_cq0
		QASM += ","+id_tq+";T "+id_tq+";CNOT "+id_cq1
		QASM += ","+id_tq+";Td "+id_tq+";CNOT "+id_cq0
		QASM += ","+id_tq+";Td "+id_cq1+";T "+id_tq
		QASM += ";CNOT "+id_cq0+","+id_cq1+";H "+id_tq
		QASM += ";Td "+id_cq1+";CNOT "+id_cq0+","+id_cq1
		QASM += ";T "+id_cq0+";S "+id_cq1 +";"
		#print(QASM)
		return QASM

	#record the entire gate in circuit.qubitExecuteList
	def __recordEG(self,gateName:str,cql:list,tql:list,angle = None):
		resQL = cql.copy()
		for tq in tql:
			resQL.append(tq)

		#record the entire gate in circuit.qubitExecuteList

		i = 0
		while i < len(resQL):
			if resQL[i].tag == "AX":
				#the qubit is an auxiliary qubit
				del resQL[i]
				continue
			i += 1

		cG = [[0] * (2**len(resQL))] * (2**len(resQL))
		
		#append the multi-controlled gate to Dict "allowGate", which is defined in baseGate.py
		#allowGate[gateName] = len(resQL)

		#init the Gate instance
		gate = Gate(resQL,cG,gateName)
		if len(resQL) == 1:
			c = gate.recordSingleExecution(True,angle)
			#print(c.qubitExecuteList)
		else:
			c = gate.recordmultiExecution(True,angle)
			#print(c.qubitExecuteList)

	#'er' is the QASM code generated by the other methods in this class
	#note that all the Single-Gate and Double-Gate in this function shouldn't be stored in circuit.qubitExecuteList	
	def execute(self,er,cqL:list,tqL:list,gateName:str,angle = None):
		self.__recordEG(gateName,cqL,tqL,angle)
		#execute the component gate
		erL = er.split(";")
		for item in erL:
			if item == "":
				continue
			tmpStr = item.split(" ")
			gate = tmpStr[0]
			import re
			#if the gate has parameter
			m = re.match("(.*)\((.*)\)(.*)", gate)
			if m != None:
				gate = m.group(1)
				parameter = m.group(2)
				exeStr = gate + "(" + parameter + ","
			else:
				exeStr = gate + "("
			q = tmpStr[1].split(",")
			for i in range(0,len(q)):
				qType = q[i].split("-")[0]
				index = q[i].split("-")[1]
				try:
					if qType == "cq":
						exeStr += "cqL[" + index + "]"
					elif qType == "tq":
						exeStr += "tqL[" + index + "]"
					else:
							raise ValueError
				except ValueError:
					info = self.get_curl_info()
					writeErrorMsg("Qubit List: "+qtype+" isn't defined in Class SplitGate!",info[0],info[1])
				except IndexError:
					info = self.get_curl_info()
					writeErrorMsg("The index of the target element is our of range!",info[0],info[1])
				if i != len(q)-1:
					exeStr += ","
			exeStr += ",False)"
			exec(exeStr)
			
		resQL = cqL.copy()
		for tq in tqL:
			resQL.append(tq)
		return resQL

def X(q:Qubit,record = True):
	X = [[0,1],[1,0]]
	gate = Gate([q],X,"X")
	return gate.singleOperator(record)

def Y(q:Qubit,record = True):
	Y = [[0,-1j],[1j,0]]
	gate = Gate([q],Y,"Y")
	return gate.singleOperator(record)

def Z(q:Qubit,record = True):
	Z = [[1,0],[0,-1]]
	gate = Gate([q],Z,"Z")
	return gate.singleOperator(record)

def I(q:Qubit,record = True):
	I = [[1,0],[0,1]]
	gate = Gate([q],I,"I")
	return gate.singleOperator(record)


def H(q:Qubit,record = True):
	H = [[1/math.sqrt(2),1/math.sqrt(2)],[1/math.sqrt(2),-1/math.sqrt(2)]]
	gate = Gate([q],H,"H")
	return gate.singleOperator(record)

def S(q:Qubit,record = True):
	S = [[1,0],[0,1j]]
	gate = Gate([q],S,"S")
	return gate.singleOperator(record)

def Sd(q:Qubit,record = True):
	Sd = [[1,0],[0,-1j]]
	gate = Gate([q],Sd,"Sd")
	return gate.singleOperator(record)


def T(q:Qubit,record = True):
	T = [[1,0],[0,(1+1j)/math.sqrt(2)]]
	gate = Gate([q],T,"T")
	return gate.singleOperator(record)

def Td(q:Qubit,record = True):
	Td = [[1,0],[0,(1-1j)/math.sqrt(2)]]
	gate = Gate([q],Td,"Td")
	return gate.singleOperator(record)

#all the single qubit gate can be constructed by the following two gate according to ZYZ decompose
#the argument "phi" is a rotation angle in radians
def Rz(phi,q:Qubit,record = True):
	pows = 1j*phi / 2
	Rz = [[cmath.exp(-pows),0],[0,cmath.exp(pows)]]
	gate = Gate([q],Rz,"Rz")
	return gate.singleOperator(record,phi)

def Ry(theta,q:Qubit,record = True):
	Ry = [[math.cos(theta/2),-math.sin(theta/2)],[math.sin(theta/2),math.cos(theta/2)]]
	gate = Gate([q],Ry,"Ry")
	return gate.singleOperator(record,theta)

#this gate is implemented by Rz and Ry
def Rx(phi,q:Qubit,record = True):
	PI = math.pi
	I = [[1,0],[0,1]]
	q = Rz(PI/2,q,False)
	q = Ry(-phi,q,False)
	q = Rz(-PI/2,q,False)
	gate = Gate([q],I,"Rx")
	gate.recordSingleExecution(True,phi)
	return q


#return a Qubits, which has two entanglement qubit
#the two qubit can be independent qubits, or one of them are a part of engtanlement 
#the first qubit is the control-qubit, the second qubit is the target-qubit
def CNOT(q1:Qubit,q2:Qubit,record = True):
	CNOT = [[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]]
	gate = Gate([q1,q2],CNOT,"CNOT")
	return gate.CNOTOperator(record)


#execute the measurement, the types of the first argument must be Qubit; the second argument is optional,
#if the parameter "result" is "False", then the result of the measurement won't be appeared in the end result 
def M(q:Qubit,result = True):
	I = [[1,0],[0,1]]
	#print([q])
	gate = Gate([q],I,"M")
	return gate.MOperator(result)

#Toffoli gate, three input and three output
def Toffoli(q1:Qubit,q2:Qubit,q3:Qubit):
	sg = SplitGate()
	qL = sg.MCU("Toffoli",[q1,q2],q3,[1,1],None,True)
	return qL
