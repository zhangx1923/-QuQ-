#import the ibm code
from IBMQuantumExperience import *
from interactCfg import *
from Error import *
import os
import sys
#get the info about the function name and the line number
def get_curl_info():
	try:
		raise Exception
	except:
		f = sys.exc_info()[2].tb_frame.f_back
	return [f.f_code.co_name, f.f_lineno]

#the max execute times is made by IBM stuff
MAXTIMES = 8192

class IBMQX:
	def __init__(self):
		print("Connecting to the Server...")
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
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ie.value,funName,line)	
		if self.shot < 1 or self.shot > MAXTIMES:
			try:
				raise IBMError("the execute times must be from 1 to 8192, but the input is " + str(self.shot))
			except IBMError as ie:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ie.value,funName,line)
		#get the connectivity map of the device according to the name of the device
		try:
			self.connectivity = tokenDic['connectivity'][self.device]
		except KeyError as ke:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("the IBMToken.cfg doesn't have the connectivity of the current device: " + self.device,funName,line)
		#create a new folder to save the data of IBMQX
		circuit = checkEnvironment()
		if os.path.exists(circuit.urls + "/IBMQX") == False:
			try:
				os.makedirs(circuit.urls + "/IBMQX") 
			except OSError:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("Can't create the new folder 'IBMQX'!",funName,line)	

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
		print("Optimizing the QASM-code, please wait for a while...")
		#the code has been store in circuit.url/QASM.txt
		circuit = checkEnvironment()
		if circuit == None:
			return None
		codeLocation = circuit.urls + "/QASM.txt"
		#this function must be called after circuit.execute()
		if os.path.exists(codeLocation) == False:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("The QASM code hasn't been generated, please check your code!",funName,line)	
		file = open(codeLocation)
		QASM = file.readlines()	
		file.close()
		CNOTError = []
		CNOTList = []
		code = ""
		#store the qubit has been measured
		measured_q = []
		lineN = 0
		while lineN < len(QASM):
			q = QASM[lineN].split(" ")[1]
			if q in measured_q:
				#the qubit has been measured
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("QuanSim can't act any gate on a measured qubit!",funName,line)
			
			#the measure must be the last gate on qubits
			if "measure" in QASM[lineN]:
				if "," in q:
					info = get_curl_info()
					funName = info[0]
					line = info[1]
					writeErrorMsg("QuanSim can't measure more than one qubit at the same time!",funName,line)
				measured_q.append(q)
			if "cx" in QASM[lineN]:
				strs = q.split(',')
				#get the id of control-qubit and target-qubit
				tQ = strs[1][2]
				cQ = strs[0][2]
				CNOTList.append([cQ,tQ])
				if cQ in self.connectivity and tQ in self.connectivity[cQ]:
					#directly satisfy the constraint
					lineN += 1
					continue
				elif tQ in self.connectivity and cQ in self.connectivity[tQ]:
					#add H gate to satisfy the constraint
					hExternal = "h q[" + str(cQ) + "];\r\nh q[" + str(tQ) + "];\r\n"
					QASM.insert(lineN,hExternal)
					QASM[lineN+1] = "cx q[" + str(tQ) + "],q[" + str(cQ) + "];\r\n"
					QASM.insert(lineN+2,hExternal)
					lineN += 1
					continue
				else:
					###################################
					###################################
					#how to adjust the map of CNOT
					###################################
					###################################
					pass
				tmp = [cQ,tQ]
				if tmp in CNOTError:
					lineN += 1
					continue
				CNOTError.append(tmp)
			lineN += 1
		#check the CNOT list whether satisfies the constraint of the connectivity
		canExecute = True
		reasonList = []
		if len(CNOTError) == 0:
			pass
		else:
			for item in CNOTError:
				cq = str(item[0])#the controlQubit
				tq = str(item[1])#the targetQubit			
				#record the reason for why can,'t execute the code
				canExecute = False
				reason = "Can't utilize Q" + cq + " as the control Qubit and Q" + tq + " as the target Qubit!"
				reasonList.append(reason)

		if canExecute:
			for line in QASM:
				code += line
			try:
				file = open(circuit.urls + "/IBMQX/QASM-modified.txt","w")
				file.write(code)	
				file.close()	
			except IOError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("Can't write QASM code to QASM-modified.txt!",funName,line)		
			return code
		file = open(circuit.urls + "/IBMQX/codeWarning.txt",'a')
		file.write("WARNING:\n")
		#write the reason in codeWarning.txt
		for i in range(0,len(reasonList)):
			strs = str(i+1) + "." + reasonList[i] + "\n"
			file.write(strs)
		return None

	#execute the code
	def executeQASM(self,experimentName = None):
		code = self.__canExecute()
		circuit = checkEnvironment()
		if code == None:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("The QASM code generated by QuanSim doesn't satisfy the requirement of IBMQX!",funName,line)
			return False
		try:
			data = self.api.run_experiment(code,self.device,self.shot,experimentName)
		except ConnectionError as ce:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("Can't connect to the server, Please try again later!",funName,line)
		#analyse the message
		try:
			file = open(circuit.urls + "/IBMQX/rawData_IBMQX.txt","w",encoding='utf-8')
			file.write(str(data))
			file.close()
		except IOError:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("Can't write the raw data of IBMQX to rawData_IBMQX.txt!",funName,line)
		try:
			status = data['status']
			result = data['result']
			measure = result['measure']
			qubits = measure['qubits']
			labels = measure['labels']
			values = measure['values']
			rList = []
			for i in range(0,len(labels)):
				states = ""
				for q in qubits:
					state = labels[i][len(labels[i])-q-1]
					states += state
				rList.append([states,values[i]])
			dataMsg = "-" * 30
			dataMsg += " the data of IBMQX "
			dataMsg += "-" * 31
			dataMsg += "\r\n"
			dataMsg += "Result:\r\n"
			for r in rList:
				prob = float(r[1]) * 100
				dataMsg += " "*8+"|" + r[0] + ">----%.2f%%"%(prob)
				dataMsg += "\r\n"
			dataMsg += "-" * 80
			print(dataMsg)
		except KeyError:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("There are some keys aren't in the result returned by IBMQX!",funName,line)
		try:
			file = open(circuit.urls + "/IBMQX/Data_IBMQX.txt","w",encoding='utf-8')
			file.write(dataMsg)
			file.close()
		except IOError:
			info = get_curl_info()
			funName = info[0]
			line = info[1]
			writeErrorMsg("Can't write the raw data of IBMQX to Data_IBMQX.txt!",funName,line)
