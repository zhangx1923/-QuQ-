#!/usr/bin/python3
from baseGate import *

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
				self.position += 2 ** exp
		self.DMOv = tmp
		#storage the control-qubit list
		self.DMOql = ql

	#get the info about the function name and the line number
	def get_curl_info(self):
		try:
			raise Exception
		except:
			f = sys.exc_info()[2].tb_frame.f_back
		return [f.f_code.co_name, f.f_lineno]

	def __constructM(self,v:list):
		try:
			self.v[self.DMOposition][self.DMOposition] = X[0][0]
			self.v[self.DMOposition][self.DMOposition+1] = X[0][1]
			self.v[self.DMOposition+1][self.DMOposition] = X[1][0]
			self.v[self.DMOposition+1][self.DMOposition+1] = X[1][1]
		except IndexError:
			info = self.get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("The matrix of the controlled-operator doesn't \
				have line" + str(self.DMOposition) + " or line" + str(self.DMOposition+1) + "!",funName,line)	

	def X(self,q:Qubit):
		X = [[0,1],[1,0]]
		self.__constructM(X)
		self.DMOql.append(q)
		gate = Gate(self.DMOql,self.DMOv,"c-X")
		
		#return gate.singleOperator()
		
	#多种受控门分为两种情况：1.执行的时候按照基本的构造方法将现有的进行拆分，再执行
	#2.在导出线路图的时候，对于多种受控门，直接绘制
	
		