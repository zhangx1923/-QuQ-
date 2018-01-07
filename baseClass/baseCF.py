from Qubit import *
sys.path.append('../tools/')
from interactCfg import writeErrorMsg
from helperFunction import get_curl_info

class ControlFlow:
	def __init__(self,q,v):
		self.ql = []
		self.vl = []
		typeQ = type(q)
		typeV = type(v)
		if typeQ == Qubit and typeV == int:
			self.ql.append(q)
			self.vl.append(v)
		elif typeQ == list and typeV == list:
			if len(q) != len(v):
				try:
					raise ValueError()
				except ValueError as t:
					info = get_curl_info()
					funName = info[0]
					line = info[1]
					writeErrorMsg("The length of the qubit list should be same with the length of the value list!",funName,line)				
			if repeatElement(q):
				info = get_curl_info()
				writeErrorMsg("There are repeating elements in the control-qubits list!",info[0],info[1])
			self.ql = q
			self.vl = v
		elif typeQ == list and typeV == int:
			self.ql = q
			self.vl.append(v)
		else:
			try:
				raise TypeError()
			except TypeError as t:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("The types of the two arguments aren't allowed,\
				 they should be (Qubit,int),(list,list) or (list,int)!",funName,line)

	def __enter__(self):
		return True
	def __exit__(self,a,b,c):
		pass

