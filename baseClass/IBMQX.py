#import the ibm code
from IBMQuantumExperience import *
from interactCfg import *
from helperFunction import *
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
			dic = tokenDic['connectivity'][self.device]
			#change the key and item from str to int
			self.connectivity = {}
			for key in dic:
				for item in dic[key]:
					if int(key) in self.connectivity:
						self.connectivity[int(key)].append(int(item))
					else:
						self.connectivity[int(key)] = [int(item)]
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
		totalCNOT = {}
		cnotQList = []
		for cnot in CNOTList:
			if cnot[0] not in cnotQList:
				cnotQList.append(cnot[0])
			if cnot[1] not in cnotQList:
				cnotQList.append(cnot[1])
			if cnot[0] in totalCNOT:
				totalCNOT[cnot[0]].append(cnot[1])
			else:
				totalCNOT[cnot[0]] = [cnot[1]]
			if cnot[1] in totalCNOT:
				totalCNOT[cnot[1]].append(cnot[0])
			else:
				totalCNOT[cnot[1]] = [cnot[0]]
		choiceList = []
		for cq in totalCNOT:
			tmp = []
			for tcq in totalConnectivity:
				if len(totalConnectivity[tcq]) >= len(totalCNOT[cq]):
					tmp.append(tcq)
			choiceList.append(tmp)
		#the solution space is choiceList[]
		solution = [-1] * len(cnotQList)
		newMaps = self.__backTrace(0,len(cnotQList),solution,totalConnectivity,choiceList,cnotQList)
		if newMaps != None:
			self.__changeQASMandCNOT(newMaps)
			return True
		else:
			reason = "Can't adjust the connectivity in your circuit to satisfy the requirement of the IBM chip!"
			reasonList.append(reason)
			return False
	def __backTrace(self,depth,N,solution,tc,choiceList,cnotQList):
		if depth >= N:
			dic = self.__getQubitMap(cnotQList,solution,tc)
			if self.__checkMapConstraint(dic,tc):
				return dic
			else:
				return None
		else:
			for i in range(0,len(choiceList[depth])):
				if choiceList[depth][i] in solution[0:depth+1]:
					continue
				else:
					solution[depth] = choiceList[depth][i]
					res = self.__backTrace(depth+1,N,solution,tc,choiceList,cnotQList)
					if res != None:
						return res

	#use two list to construct a map: the key is from the first list and the value is from the second list
	#note: the dimension of l1 and l2 must be same with each other
	#and if there is qubits in qubitList but not in CNOTList, we should append the item in the dict
	def __getQubitMap(self,l1,l2,tc):
		if len(l1) != len(l2):
			try:
				raise IBMError("The dimension of the Qubit list should be same with the dimension of the solution!")
			except IBMError as ie:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				writeErrorMsg(ie.value,funName,line)
		dic = {}
		availalbleQ = [i for i in range(0,len(tc))]

		for index in range(0,len(l1)):
			dic[l1[index]] = l2[index]
			availalbleQ.remove(l2[index])

		for q in qubitList:
			if q in dic:
				continue
			else:
				dic[q] = availalbleQ[0]
				del availalbleQ[0]
		return dic

	#adjust the copy of CNOTList according to the map, and call the __checkAllConstraint
	def __checkMapConstraint(self,maps,tc):
		if len(maps) != len(qubitList):
			return False
		cCNOTList = CNOTList.copy()
		for i in range(0,len(cCNOTList)):
			cCNOTList[i] = [maps[cCNOTList[i][0]],maps[cCNOTList[i][1]]]
		return self.__checkAllConstraint(cCNOTList,tc)


	#change the global parameter qubitList, QASM, CNOTList according to the qmap
	def __changeQASMandCNOT(self,qMap):
		#change the id in CNOTList to satisfy the requirement
		for i in range(0,len(CNOTList)):
			for j in range(0,len(CNOTList[i])):
				CNOTList[i][j] = qMap[CNOTList[i][j]]

		#change the QASM code
		mode = re.compile(r'\d+')
		for l in range(0,len(QASM)):
			if l == 0:
				continue
			else:
				qs = mode.findall(QASM[l])
				if len(qs) == 1:
					#single-qubit gate
					QASM[l] = QASM[l].replace("[" + str(qs[0]) + "]","[" + str(qMap[int(qs[0])]) + "]")
				elif len(qs) == 2 and qs[0] == qs[1]:
					#measurement 
					QASM[l] = QASM[l].replace("[" + str(qs[0]) + "]","[" + str(qMap[int(qs[0])]) + "]")
				else:
					#multi-qubits gate
					newQASM = QASM[l].split(" ")[0] + " "
					qubit = QASM[l].split(" ")[1].split(",")
					for qi in range(0,len(qs)):
						newQASM += qubit[qi].replace("[" + str(qs[qi]) + "]","[" + str(qMap[int(qs[qi])]) + "]")
						if qi != len(qs)-1:
							newQASM += ","
					QASM[l] = newQASM

		#change the qubitList according to the qMap
		for qi in range(0,len(qubitList)):
			if qubitList[qi] in qMap:
				qubitList[qi] = qMap[qubitList[qi]]

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
				tQ = int(strs[1][2])
				cQ = int(strs[0][2])
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
