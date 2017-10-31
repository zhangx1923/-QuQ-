#import the ibm code
from IBMQuantumExperience import *
from interactCfg import *
from Error import *
import os

#the max execute times is made by IBM stuff
MAXTIMES = 8192

class IBMQX:
	def __init__(self):
		#change the config message in config/IBMToken.cfg
		tokenDic = readCfgPM()
		self.__config = {
   			"url": tokenDic['url']
		}	
		#init the api
		self.api = IBMQuantumExperience(tokenDic['token'], self.__config)
		deviceList = self.__getAvailalbeBak()
		self.device = tokenDic['device']
		self.shot = int(tokenDic['shot'])
		if self.device not in deviceList:
			try:
				raise IBMError("the seleted device isn't available")
			except IBMError as ie:
				writeErrorMsg(ie.value)	
		if self.shot < 1 or self.shot > MAXTIMES:
			try:
				raise IBMError("the execute times must be from 1 to 8192, but the input is " + str(self.shot))
			except IBMError as ie:
				writeErrorMsg(ie.value)
		#get the connectivity map of the device according to the name of the device
		try:
			self.connectivity = tokenDic['connectivity'][self.device]
		except KeyError as ke:
			writeErrorMsg("the IBMToken.cfg doesn't have the connectivity of the current device: " + self.device)


	#get the availalbe backend, return the backend list
	def __getAvailalbeBak(self):
		result = []
		lists = self.api.available_backends()
		for item in lists:
			backend = item['name']
			result.append(backend)
		return result

	#adjust the QASM code, which is producted by circuit.QASM(), so that the qubits can satisfy the constraint
	#of the CNOT connectivity
	def __canExecute(self):
		#the code has been store in circuit.url/QASM.txt
		circuit = checkEnvironment()
		if circuit == None:
			return None
		codeLocation = circuit.urls + "/QASM.txt"
		#this function must be called after circuit.execute()
		if os.path.exists(codeLocation) == False:
			print("the QASM code hasn't been generated, please check your code")
			return None	
		file = open(codeLocation)
		QASM = file.readlines()	
		file.close()
		CNOTlist = []
		code = ""
		for line in QASM:
			if "cx" in line:
				strs = line.split(" ")[1].split(',')
				#get the id of control-qubit and target-qubit
				targetQ = strs[1][2]
				controlQ = strs[0][2]
				tmp = [controlQ,targetQ]
				CNOTlist.append(tmp)
			code += line
		#check the CNOT list whether satisfies the constraint of the connectivity
		canExecute = True
		reasonList = []

		for item in CNOTlist:
			cq = str(item[0])#the controlQubit
			tq = str(item[1])#the targetQubit
			if cq in self.connectivity:
				if tq in self.connectivity[cq]:
					#satisfy the constraint
					continue

			#record the reason for why can,'t execute the code
			canExecute = False
			reason = "can't utilize Q" + cq + " as control Qubit and Q" + tq + " as target Qubit!"
			reasonList.append(reason)
		if canExecute:
			return code
		file = open(circuit.urls + "/codeWarning.txt",'a')
		file.write("WARNING:\n")
		#write the reason in codeWarning.txt
		for i in range(0,len(reasonList)):
			strs = str(i+1) + "." + reasonList[i] + "\n"
			file.write(strs)
		return None

	#execute the code
	def executeQASM(self,experimentName = None):
		code = self.__canExecute()
		if code == None:
			return False
		try:
			result = self.api.run_experiment(code,self.device,self.shot,experimentName)
		except ConnectionError as ce:
			writeErrorMsg("can't connect to the server")
		print(result)



		