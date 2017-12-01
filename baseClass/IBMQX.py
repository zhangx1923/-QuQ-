#import the ibm code
from IBMQuantumExperience import *
from interactCfg import *
from Error import *
import os
import sys
import re
#get the info about the function name and the line number
def get_curl_info():
	try:
		raise Exception
	except:
		f = sys.exc_info()[2].tb_frame.f_back
	return [f.f_code.co_name, f.f_lineno]

#the max execute times is made by IBM stuff
MAXTIMES = 8192
#the min executive times is made by IBM stuff
MINTIMES = 1

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
		print("Getting the available backend information...")
		deviceList = self.__getAvailalbeBak()
		self.device = tokenDic['device']
		self.shot = int(tokenDic['shot'])
		if self.device not in deviceList:
			try:
				raise IBMError("The seleted device isn't available")
			except IBMError as ie:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ie.value,funName,line)	
		if self.shot < MINTIMES or self.shot > MAXTIMES:
			try:
				raise IBMError("The execute times must be from " + str(MINTIMES) + " to " + str(MAXTIMES) + ", but the input is " + str(self.shot))
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
			try:
				backend = item['name']
				result.append(backend)
			except KeyError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("Can't get the key:'name' in the backend information!".funName,line)
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
		global QASM,qubitList,CNOTList
		QASM = file.readlines()	
		file.close()
		#record the ids of qubits in the current circuit
		qubitList = []
		#record the cnot map in the current circuit
		CNOTList = []

		#fine the num in the str
		mode = re.compile(r'\d+')
		#analyse the QASM code
		for l in range(0,len(QASM)):
			if l == 0:
				continue
			else:
				qs = mode.findall(QASM[l])
				if "measure" in QASM[l]:
					qs = [qs[0]]
				for q in qs:
					if int(q) in qubitList:
						continue
					else:
						qubitList.append(int(q))
				if "cx" in QASM[l]:
					#get the id of control-qubit and target-qubit
					tQ = int(qs[1])
					cQ = int(qs[0])
					#the reverse cnot won't be appended to the list
					if [cQ,tQ] in CNOTList or [tQ,cQ] in CNOTList:
						continue
					CNOTList.append([cQ,tQ])
		
		totalConnectivity = self.__getTotalConnectivity()
		print(CNOTList)
		print(qubitList)
		print(self.connectivity)
		print(totalConnectivity)
		#record the reason for why can't execute the code
		reasonList = []
		cnotBool = True
		idBool = True
		idBool = self.__determindID(totalConnectivity,reasonList)
		if idBool:
			cnotBool = self.__checkAllConstraint(CNOTList,totalConnectivity)
			if cnotBool == False:
				#when __adjustCNOT was called, the CNOTList doesn't satisfy the constraint of IBM directly
				cnotBool = self.__adjustCNOT(totalConnectivity,reasonList)

		#the circuit can be executed
		if idBool & cnotBool:
			code = ""
			self.__reverseCNOT(QASM)
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

		#can't execute the circuit
		file = open(circuit.urls + "/IBMQX/codeWarning.txt",'a')
		file.write("WARNING:\n")
		#write the reason in codeWarning.txt
		for i in range(0,len(reasonList)):
			strs = str(i+1) + "." + reasonList[i] + "\n"
			file.write(strs)
		return None

	#add self.connectivity and reverse self.connectivity, the type of the returned parameter is dict
	def __getTotalConnectivity(self):
		totalConnectivity = {}
		for cQ in self.connectivity:
			for tQ in self.connectivity[cQ]:
				if cQ in totalConnectivity:
					totalConnectivity[cQ].append(tQ)
				else:
					totalConnectivity[cQ] = [tQ]
				if tQ in totalConnectivity:
					totalConnectivity[tQ].append(cQ)
				else:
					totalConnectivity[tQ] = [cQ]
		return totalConnectivity		

	#determind whether the number of qubit in this circuit is more than the actual number
	#if bigger, return False; else return True;
	#if necessary, adjust the id of the qubit so that they are in line with the actual device
	def __determindID(self,totalConnectivity,reasonList):
		#we assume that there is no qubit isolated in ibm chip!
		useQubit = len(qubitList)
		actualQubit = len(totalConnectivity)
		if useQubit > actualQubit:
			reasonList.append("There are "+ str(useQubit) + " have been used! But the device you choose only have " + str(actualQubit) + " qubits!")
			return False
		if max(qubitList) < actualQubit:
			return True
		qubitList.sort()
		availalbleQ = [i for i in range(0,actualQubit)]
		qMap = {}
		for q in qubitList:
			qMap[q] = q
			if q < actualQubit:
				try:
					availalbleQ.remove(q)
				except ValueError:
					info = get_curl_info()
					funName = info[0]
					line = info[1]
					writeErrorMsg("Q "+ str(q) + " isn't available!",funName,line)
				continue
			#q >= actualQubit
			#because actualQubit is more than useQubit, the actualQubit[0] is always existing
			qMap[q] = availalbleQ[0]
			availalbleQ.remove(availalbleQ[0])
		self.__changeQASMandCNOT(qMap)
		return True

	#check the CNOT list whether satisfies the constraint of the connectivity
	#if satisfies or we can adjust the cnot to satisfy the constraint, return True;
	#else return False and store the 'bad' cnot in reasonList 
	def __adjustCNOT(self,totalConnectivity,reasonList):
 		cnotNum = len(CNOTList)
 		ibmNum = 0
 		for k in self.connectivity:
 			ibmNum += len(self.connectivity[k])
 		if cnotNum > ibmNum:
 			reason = "There are " + str(cnotNum) + " different connectivities in this circuit, but only " + str(ibmNum) + " are allowd in IBM chip!"
 			reasonList.append(reason)
 			return False
 		CNOTDic = {}
 		for c in CNOTList:
 			if c[0] in CNOTDic:
 				CNOTDic[c[0]].append(c[1])
 			else:
 				CNOTDic[c[0]] = [c[1]]
 		#{degree1:[qubit.ids,...],degree2:[qubit1.ids..]}
 		degCNOTDic = {}
 		degList = []
 		for cQ in CNOTDic:
 			degree = len(CNOTDic[cQ])
 			degList.append(degree)
 			if degree in degCNOTDic:
 				degCNOTDic[degree].append(cQ)
 			else:
 				degCNOTDic[degree] = [cQ]
 		degList.sort()
 		degList.reverse()

 		degtCNOTDic = {}
 		degtList = []
 		for tcQ in totalConnectivity:
 			degree = len(totalConnectivity[tcQ])
 			degtList.append(degree)
 			if degree in degtCNOTDic:
 				degtCNOTDic[degree].append(tcQ)
 			else:
 				degtCNOTDic[degree] = [tcQ]
 		degtList.sort()
 		degtList.reverse()

 		if len(degList) > len(degtList):
 			reason = "There are " + str(len(degList)) + " entangled with other qubits, but only " + str(len(degtList)) + " are allowd in IBM!"
 			reasonList.append(reason)
 			return False

 		posMap = {}
 		# for d in degList:
 		# 	if d > max(degtList):
 		# 		for q in degCNOTDic[d]:
 		# 			reason = "Q" + str(q) + " can't connect with " + max(degtList) + " qubits!"
 		# 			reasonList.append(reason)
 		# 		return False
 		# 	for dt in degtList:
 		# 		if dt >= d:
 		
 		#degList,degCNOTDic,degtList,degtCNOTDic
 		for iDT in range(0,len(degtList)):
			if degtList[iDT] >= degList[iDT]
				set a map
				continue
 					





				# reason = "Can't utilize Q" + str(CNOTList[iTH][0]) + " as the control Qubit and Q" + str(CNOTList[iTH][1]) + " as the target Qubit!"
				# reasonList.append(reason)			


	#the type of qMap is dict
	def __changeQASMandCNOT(self,qMap):
		#change the id to satisfy the requirement
		for i in range(0,len(CNOTList)):
			for j in range(0,len(CNOTList[i])):
				CNOTList[i][j] = qMap[CNOTList[i][j]]
		mode = re.compile(r'\d+')
		for l in range(0,len(QASM)):
			if l == 0:
				continue
			else:
				qs = mode.findall(QASM[l])
				for q in qs:
					QASM[l] = QASM[l].replace("[" + str(q) + "]","[" + str(qMap[int(q)]) + "]")

	#the the max neighbor in totalconnectivity
	def __getMaxNeighbor(self,tc):
		if type(tc) != dict:
			try:
				raise TypeError
			except TypeError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("The type of the argument must be Dict!",funName,line)
		maxs = 0
		for c in tc:
			maxs = max(maxs,len(tc[c]))
		return maxs

	#check cnot whether satisfies the constraint
	#the format of cnot should be [1,3]
	def __checkSingleConstraint(self,cnot:list,tc):
		if len(cnot) != 2:
			try:
				raise ValueError
			except ValueError:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg("The cnot should be two-dimension!",funName,line)
		cQ = cnot[0]
		tQ = cnot[1]
		if cQ in tc and tQ in tc[cQ]:
			#directly satisfy the constraint
			return True
		else:
			return False
	def __checkAllConstraint(self,cnotList,tc):
		for c in cnotList:
			if self.__checkSingleConstraint(c,tc):
				continue
			else:
				return False
		return True

	#get the legal cnot gate in current device
	def __getLegalCNOT(self):
		legalCList = []
		for cQ in self.connectivity:
			for tQ in self.connectivity[cQ]:
				if [cQ,tQ] not in legalCList:
					legalCList.append([cQ,tQ])
				if [tQ,cQ] not in legalCList:
					legalCList.append([tQ,cQ])
		return legalCList

	#modify the qasm code by adding H to reverse the current CNOT
	def __reverseCNOT(self,QASM):
		lineN = 0
		while lineN < len(QASM):
			if 'cx' in QASM[lineN]:
				q = QASM[lineN].split(" ")[1]
				strs = q.split(',')
				#get the id of control-qubit and target-qubit
				tQ = strs[1][2]
				cQ = strs[0][2]
				if cQ in self.connectivity and tQ in self.connectivity[cQ]:
					pass
				elif tQ in self.connectivity and cQ in self.connectivity[tQ]:				
					#add H gate to satisfy the constraint
					hExternal = "h q[" + str(cQ) + "];\r\nh q[" + str(tQ) + "];\r\n"					
					gateStr = "cx q[" + str(cQ) + "],q[" + str(tQ) + "];"
					if gateStr in QASM[lineN]:
						QASM.insert(lineN,hExternal)
						QASM[lineN+1] = "cx q[" + str(tQ) + "],q[" + str(cQ) + "];\r\n"
						QASM.insert(lineN+2,hExternal)
				else:
					pass
			lineN += 1 


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
