#!/usr/bin/python3
#the custom exceptions are written in this file
import sys
sys.path.append('../tools/')
from interactCfg import *
from helperFunction import *

#check the environment: whether the current circuit is equal to this instance 
def checkEnvironment():
	from Circuit import Circuit
	circuitNum = len(Circuit.currentIDList)
	#there only can be one instance and the id of this instance must be equal with self.ids
	if circuitNum == 1:
		if Circuit.currentIDList[0] == Circuit.instance.ids:
			return Circuit.instance
	try:
		strs = "there are " + str(len(Circuit.currentIDList)) + " Circuit instance, please check your code"
		raise EnvironmentError(strs)
	except EnvironmentError as ee:
		info = get_curl_info()
		funName = info[0]
		line = info[1]
		writeErrorMsg(ee,funName,line)
		

class NoCloning(Exception):
	def __init__(self,msg = None):
		if msg == None:
			self.value = ""
		else:
			self.value = msg
	def __str__(self):
		result = "Error Type: NoCloning\r\n"
		result += "Error Message: " + self.value 
		return result

#the function named 'checkEnvironment' will cause this error
#there only can be one Circuit instance in runtime, more than one or none instance will cause this error 
class EnvironmentError(Exception):
	def __init__(self,msg = None):
		if msg == None:
			self.value = "There are zero or more than one Circuit instance!"
		else:
			self.value = msg
	def __str__(self):
		result = "Error Type: EnvironmentError\r\n"
		result += "Error Message: " + self.value
		return result		

#there are something wrong with the code
class CodeError(Exception):
	def __init__(self,msg=None):
		if msg == None:
			self.value = "There is something wrong with the QASM code!"
		else:
			self.value = msg
	def __str__(self):
		result = "Error Type: CodeError\r\n"
		result += "Error Message: " + self.value
		return result	

#the gate name is not defined in this platfrom
class GateNameError(Exception):
	def __init__(self,msg=None):
		if msg == None:
			self.value = "There is gates which have not defined in this platfrom!"
		else:
			self.value = msg
	def __str__(self):
		result = "Error Type: GateNameError\r\n"
		result += "Error Message: " + self.value
		return result	


#calling the IBMQX api lead to error
class IBMError(Exception):
	def __init__(self,msg = None):
		if msg == None:
			self.value = "There is something wrong when calling the API of IBMQX!"
		else:
			self.value = msg 
	def __str__(self):
		result = "Error Type: IBMError\r\n"
		result += "Error Message: " + self.value
		return result 

#the execute mode must be either theory or simulator, but we get another value
class ExecuteModeError(Exception):
	def __init__(self,msg = None):
		if msg == None:
			self.value = "executeMode must be either 'theory' or 'simulator', but we get another mode"
		else:
			self.value = msg
	def __str__(self):
		result = "Error Type: ExecuteModeError\r\n"
		result += "Error Message: " + self.value
		return result

#the id of the qubit must be unique
class IDRepeatError(Exception):
	def __init__(self,msg=None):
		if msg == None:
			self.value = "the id of the qubit has been used, please choose another id"
		else:
			self.value = msg
	def __str__(self):
		result = "Error Type: IDRepeatError\r\n"
		result += "Error Message: " + self.value
		return result

#the qubit or qubits is not normal
class NotNormal(Exception):
	def __init__(self,msg=None):
		if msg == None:
			self.value = "the qubit or qubits is not normal, please normalize the measured qubit!"
		else:
			self.value = msg
	def __str__(self):
		result = "Error Type: NotNormal\r\n"
		result += "Error Message: " + self.value
		return result
