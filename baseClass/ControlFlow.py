from baseCF import *
from Gate import *
from Circuit import *
from DMO import DMO

#a single qubit can be used as the guard; 
#if there is more the one qubit in the guard, you should pass these qubits as a list
#if the values list has only one element, the value of all the qubits should be same with the value of the element; 
#otherwise the length of the values list should be same with the length of the qubits list
class Qif(ControlFlow):
	def __init__(self,q,v):
		ControlFlow.__init__(self,q,v)
	#this function is quantum teleportation quantum if 
	def __enter__(self):
		resList = []
		for q in self.ql:
			q1 = Qubit()
			q2 = Qubit()
			H(q1)
			CNOT(q1,q2)
			CNOT(q,q1)
			H(q)
			CNOT(q1,q2)
			H(q2)
			CNOT(q,q2)
			H(q2)
			#restore the state of the Qubit "q"
			H(q)
			#destory the auxiliary qubits "q1" and "q2"
			q2 = M(q2,True)
			q1 = M(q1,True)
			resList.append(q2.value)
		if len(self.vl) == 1:
			for r in resList:
				if r != self.vl[0]:
					return False
		else:
			for i in range(0,len(resList)):
				if resList[i] != self.vl[i]:
					return False
		return True

#in the following two methods, the qubit used as the guard can't be appeared in the executive body. 
class DMif(ControlFlow):
	def __init__(self,q,v):
		ControlFlow.__init__(self,q,v)

	#this function is delay measure-based quantum if 
	def __enter__(self):
		dmo = DMO(self.ql,self.vl)
		return dmo
	def __exit__(self,a,b,c):
		return True

class Mif(ControlFlow):
	def __init__(self,q,v):
		ControlFlow.__init__(self,q,v)
	#this function is measure-based quantum if
	def __enter__(self):
		resList = []
		for i in range(0,len(self.ql)):
			self.ql[i] = M(self.ql[i],True)
			#Bit
			resList.append(self.ql[i].value)
		if len(self.vl) == 1:
			for r in resList:
				if r != self.vl[0]:
					return False
		else:
			for j in range(0,len(resList)):
				if resList[j] != self.vl[j]:
					return False
		return True	



class qWhile:
	def __init__(self):
		self.q = []
		return True