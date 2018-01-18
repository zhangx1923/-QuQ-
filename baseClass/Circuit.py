import sys
import os
import psutil
sys.path.append('../tools/')
import interactCfg
import helperFunction
import datetime
import random
from Bit import Bit
from Qubit import *
from Error import *
from IBMQX import *
#from Gate import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.axes_grid.anchored_artists import AnchoredText
import csv
import re

#the circuit.py will use this one 
styleDic = {
	"I":[" I ","C5"],
	"X":["X","C0"],
	"Y":["Y","C1"],
	"Z":["Z","C1"],
	"H":["H","C2"],
	"S":["S","C8"],
	"T":["T","C4"],
	#"CNOT":["+","C0"],
	"Td":["Td","C6"],
	"Sd":["Sd","C7"],
	"M":["M","C3"],
	"qif":["qif","C3"],
	"Rz":["Rz","C5"],
	"Ry":["Ry","C5"],
	"Rx":["Rx","C5"]
	#"Toffoli":["+","C0"],
	#multi-controlled gate
}


ResLocation = "../results/"

#the data-type is the elementary unit of executing and export
class Circuit:
	#mark the environment: we can execute the code when there is only one circuit in the environment
	currentIDList = []
	instance = None

	#the parameter "withOriginalData" is True, then record the componone elements of MCU
	#instead of the whole gateName. And in this mode, it will figure out more detailed data
	def __init__(self,withOriginalData = False,experimentName=None):
		self.beginMemory = psutil.Process(os.getpid()).memory_info().rss
		self.endMemory = 0
		self.beginTime = datetime.datetime.now()
		self.endTime = 0
		if experimentName == None:
			dt = self.beginTime
			experimentName = "EXP" + str(dt.date()) + '-' + str(dt.strftime('%X')).replace(':','.')
		self.name = experimentName
		#use this value to uniquely identify
		self.ids = id(self)

		folderName = ResLocation+self.name
		#create a new folder to save the experiment
		helperFunction.createFolder(folderName)

		self.urls = folderName
		#each qubit stands for a individual dimension
		#see /doc/Class-relation.doc for details
		self.qubitExecuteList = {}
		self.qubitNum = 0
		Circuit.currentIDList.append(self.ids)
		Circuit.instance = self
		#put all the qubit which need measurement in this list
		self.measureList = []
		#record the execute mode of the current instance
		self.mode = interactCfg.readCfgEM()

		if withOriginalData:
			self.withOD = True
		else:
			self.withOD = False

		#print information and decide whether execute IBMQX
		self.ibm = False#whether execute experiments on IBM platform
		self.__printPreMsg()

		if self.withOD:
			self.qubitNumOD = 0
			self.qubitExecuteListOD = {}	
		#the if statement of QASM will be stored in this dict so that the statement won't be repeated
		self.IFList = []	
		self.IFDic = {}


	#the destory function
	def __del__(self):
		ids = id(self)
		if ids in Circuit.currentIDList:
			Circuit.currentIDList.remove(id(self))
		else:
			return

	#check the environment: whether the current circuit is equal to this instance 
	def checkEnvironment(self):
		#if there is ErrorMsg.txt in the folder, then exit <QuQ>
		#it means that there is exception in With block and we should exit the program
		if os.path.exists(self.urls + "/errorMsg.txt"):
			#True
			sys.exit(1)

		circuitNum = len(Circuit.currentIDList)
		if self.qubitNum != len(self.qubitExecuteList):
			return False
		#there only can be one instance and the id of this instance must be equal with self.ids
		if circuitNum == 1 and Circuit.currentIDList[0] == self.ids:
			return True
		try:
			strs = "There are " + str(len(Circuit.currentIDList)) + " Circuit instance, please check your code"
			raise EnvironmentError(strs)
		except EnvironmentError as ee:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg(ee.value,funName,line)

	#figure out the number of the auxiliary qubits and the actual qubits
	def __countACandAX(self):
		if self.withOD:
			er = self.qubitExecuteListOD
		else:
			er = self.qubitExecuteList
		AX = 0
		AC = 0
		for q in er:
			if q.tag == "AX":
				AX += 1
			else:
				AC += 1
		return [AX,AC]

	#if the statement is Qif or Mif, then execute the method
	#"content" stands for the executive record of this qubit 
	#"gate" stands for the gate name
	#"m" stands for the m-th record in content
	#"qubits" stands for the string consisted of q.ids and "," as separator
	#"code" stands for the QASM list
	#if the function return False, then the gate isn't the Mif or Qif
	def __generateIF(self,content,gate,m,qubits,code):
		#judge whether the statement is the "if-statement"
		if re.search(r'^(M\d-)+.+$',gate) != None:
			#Mif or Qif

			MgateList = re.findall(r'(M\d)',gate)
			#construct the control guard
			guard = ""
			for j in range(0,len(MgateList)):
				guard += "M[" + qubits[j] + "]=" + MgateList[j].split("M")[1]
				if j != len(MgateList)-1:
					guard += " && "

			#judge whether the qubit is the measured qubit 
			#or qubits are required to act quantum gate
			tag = False
			for k in range(0,m):
				if re.search(r'^M \d+$',content[k]) != None:
					#the measured qubit
					if guard in self.IFList:
						pass
					else:
						#construct the if-statement
						ifStr = "if("
						for j in range(0,len(MgateList)):
							tmpStr = "c[" + qubits[j] + "]=="
							tmpStr += MgateList[j][1]
							if j != len(MgateList)-1:
								tmpStr += " && "
							ifStr += tmpStr
						ifStr += ")"
						code.append(ifStr)
						self.IFList.append(guard)
					tag = True
					break

			#qubits are required to act quantum gate
			if tag == False:
				#store the statement in self.IFStatement and write them to QASM.txt in the end of the method
				statement = ""
				gl = gate.split("-")
				if len(gl) != len(qubits):
					try:
						raise CodeError("The gate number isn't same with the qubit number!")
					except CodeError as ce:
						info = helperFunction.get_curl_info()
						funName = info[0]
						line = info[1]
						interactCfg.writeErrorMsg(ce,funName,line)

				ifGate = ""
				ifQ = ""
				for i in range(0,len(gl)):
					if re.search(r'^M\d$',gl[i]) != None:
						pass
					else:
						ifGate += gl[i]
						ifQ += "q["+qubits[i]+"]"
						if i != len(gl)-1:
							ifQ += ","
				if re.search(r'^c\dX\d$',ifGate) != None:
					ifGate = "CNOT"
				else:
					ifGate = ifGate[0:len(ifGate)-1]

				#store the statement
				reStr = ifGate + " " + ifQ + ";"
				if guard not in self.IFDic:
					self.IFDic[guard] = []
				if reStr in self.IFDic[guard]:
					pass
				else:
					self.IFDic[guard].append(reStr)
			return True
		return False

	#write the statement to QASM.txt 
	#"statement" stands for the QASM list
	#and append the if statement according to self.IFDic and self.IFList
	def __printCode(self,fileName,statement):
		#append content in the original txt file
		try:
			code = open(fileName,"w")
			for c in statement:
				codeStr = ""
				#the if statement
				if re.search(r'if(.+)',c) != None:
					#the format of c is "if(c[0]==1 && c[1]==0)"
					codeStr = c + "{\n"			
					guard = re.findall(r'\((.*?)\)',c)[0]
					#the format of key is "M[0]=1 && M[1]=0"
					guard = guard.replace("c","M").replace("==","=")
					for s in self.IFDic[guard]:
						#append the indentation
						codeStr += "  "+ s + "\n"
					codeStr += "}\n"
				else:
					codeStr = c
				code.write(codeStr)
			code.close()
		except IOError:
			info = helperFunction.get_curl_info()
			interactCfg.writeErrorMsg("Can't write the QASM code to " + fileName + "!",info[0],info[1])

		#restore the value of the IFDic and IFList
		self.IFList = []
		self.IFDic = {}


	#draw the circuit according to the qubitExecuteList
	#the parameter "typeQN" is a list [the number of AX qubits, the number of AC qubits]
	def __exportCircuit(self,er,typeQN,fileLocation):
		global alertMsg
		if self.checkEnvironment():
			if alertMsg:
				print("begin drawing the circuit...")
			#set the canvas
			Fig = plt.figure('circuit',figsize=(12,6))                      
			#set the axis off
			plt.axis('off')
			#devide the canvas into 1row 1col, and our pic will be draw on the first place(from up to down, from left to right)
			Ax = Fig.add_subplot(111)
			qubitNum = typeQN[1]
			############################draw the line according to self.qubitNum###########################
			partition = 100 // qubitNum
			for i in range(0,qubitNum):
				X = range(0,100)
				Y = [i*partition] * 100
				Ax.plot(X,Y,'#000000')
			############################the line has been completed########################################
			
			############################draw the gate according to self.qubitExecuteList###################
			j = 0
			maxLength = 0
			q_keys = []
			for qe in er.keys():
				#the auxiliary qubit won't be in the q_keys
				if qe.tag == "AX":
					#the qubit is the auxiliary qubit
					pass
				else:
					maxLength = max(maxLength,len(er[qe]))
					q_keys.append(qe)
			quickSortQubit(q_keys,0,len(q_keys)-1)
			for q in q_keys:
				if q.tag == "AX":
					#the qubit is an auxiliary qubit and need NOT be drawed
					continue
				if maxLength < 20:
					factor = 1
				else:
					factor = maxLength / 20
				#label the ids
				label = 'Q' + str(q.ids)
				Ax.annotate(label,xy=(0, j*partition), xytext=(-4, j*partition-0.5),size=12,)
				#draw the gate
				executeList = er[q]
				x_position = 4 / factor
				for item in executeList:
					gate = item.split(" ")[0]
					style = "square"
					#the gate 'NULL' was stored to the list is to occupy the postion so that we can draw the circuit easily
					if gate == 'NULL':
						x_position += 5 / factor
						continue

					#remove the parameter of the gate
					if re.search(r'^R\w{1}\(.+\)$',gate) != None:
						gate = gate.split("(")[0]

					if gate in styleDic:
						gateName = styleDic[gate][0]
						gateColor = styleDic[gate][1]
						ann = Ax.annotate(gateName,
							xy=(1, 20), xycoords='data',
							xytext=(x_position, j*partition), textcoords='data',color='w',
							size=12/factor, va="center", ha="center",
							bbox=dict(boxstyle=style, fc=gateColor,pad=0.3,ec=gateColor),
							)
					#it means that the gate is a MCU
					else:
						if gate[-1] == '0' or gate[-1] == '1':
							#the gate is the Mif or Qif
							gate = gate[0:len(gate)-1]
						if gate == "Toffoli":
							gate = "c1-c1-X"
						if gate == "CNOT":
							gate = "c1-X"
						singleGateList = gate.split("-")
						U = singleGateList[-1]

						#remove the parameter of the gate
						if re.search(r'^R\w{1}\(.+\)$',U) != None:
							U = U.split("(")[0]

						try:
							if U == "X":
								if re.search(r'M\d',gate) != None and singleGateList[len(singleGateList)-2] != "c1":
									gateName = styleDic[U][0]
								else:
									gateName = "+"
							else:
								gateName = styleDic[U][0]
							gateColor = styleDic[U][1]
						except KeyError as ke:
							info = helperFunction.get_curl_info()
							funName = info[0]
							line = info[1]
							interactCfg.writeErrorMsg("Key: " + str(ke) + " is not in Dict:styleDic!",funName,line)
						#wheter the current qubit is the control-qubit
						qubitStrList = item.split(" ")[1].split(",") 
						targetQubit = qubitStrList[len(qubitStrList) - 1]
						controlQubit = qubitStrList[0:len(qubitStrList)-1]
						#the index of the target qubit
						indexOfTarget = 0
						#get the index of the target qubit
						for tmp in q_keys:
							if str(tmp.ids) != targetQubit:
								indexOfTarget += 1
							else:
								break
						
						#draw a circle in the control qubit
						if str(q.ids) in controlQubit:	
							#print(indexOfTarget)
							smaller = min(indexOfTarget,j)
							bigger = max(indexOfTarget,j)
							x1 = [x_position] * (bigger * partition - smaller * partition)
							y1 = range(smaller * partition,bigger * partition)

							#print(gate)
							#draw the control-line
							
							#if the gate is Mif or Qif							
							if re.search(r'^(M\d-)+.+$',gate) != None:
								#judge whether the gate is Mif-CNOT or Qif-CNOT
								if re.search(r'(c\d-){1}',gate) != None and str(q.ids) == controlQubit[-1]:
									#the gate is CNOT then judge whether the qubit is the penult element
									Ax.plot(x1,y1,gateColor)
								else:
									gateColor = "black"
									Ax.plot(x1,y1,gateColor,linestyle = ":")
							else:	
								Ax.plot(x1,y1,gateColor)
							
							indexOfCurrentQubit = controlQubit.index(str(q.ids))
							#print(type(singleGateList[indexOfCurrentQubit][1:len(singleGateList[indexOfCurrentQubit])]))
							if singleGateList[indexOfCurrentQubit][1:len(singleGateList[indexOfCurrentQubit])] == '0':
								#the color of the inside
								fc = "White"

							else:
								fc = gateColor
							#the color of the frame
							ec = gateColor
							ann = Ax.annotate("1",
                  				xy=(1, 20), xycoords='data',color=fc,
                  				xytext=(x_position, j*partition), textcoords='data',
                  				size=6/factor, va="center", ha="center",
                  				bbox=dict(boxstyle="circle", fc=fc,pad=0.3,ec=ec),
                  			)
                  			#don't draw the CX
						else:
							if gateName == "+":
								style = "circle"
							ann = Ax.annotate(gateName,
								xy=(1, 20), xycoords='data',
								xytext=(x_position, j*partition), textcoords='data',color='w',
								size=12/factor, va="center", ha="center",
								bbox=dict(boxstyle=style, fc=gateColor,pad=0.3,ec=gateColor),
								)
					x_position += 5/factor							

				j += 1
			############################the gate has completed########################################
			#plt.show()
			#save the circuit
			fileName = fileLocation + "circuit.jpg"
			Fig.savefig(fileName)			
			#print("the circuit has been stored in " + self.urls.split("..")[1]  + "/circuit.jpg")
			if alertMsg:
				print("the circuit has been drawn!\n")
			return True
		else:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("the circuit instance is wrong, please check your code",funName,line)

	#translate the code of the current circuit to QASM, so that they can be executed on IBMQX
	def __QASM(self,er,fileLocation):
		global alertMsg
		if alertMsg:
			print("begin export the QASM code of the circuit...")
		if self.checkEnvironment():
			self.IFList = []
			self.IFDic = {}
			qubitNum = len(er.keys())
			fileName = fileLocation + "QASM.txt"
			code = []
			#get the ids of the qubit
			qubitList = []
			for q in er.keys():
				qubitList.append(q)
			#get the max length of the circuit depth
			maxGate = 0
			for i in range(0,qubitNum):
				if maxGate < len(er[qubitList[i]]):
					maxGate = len(er[qubitList[i]])
			for m in range(0,maxGate):
				for n in range(0,qubitNum):
					content = er[qubitList[n]]
					#print(content)
					length = len(content)
					#if there is no element to be draw, skip the loop
					if m > length-1:
						continue
					item = content[m]

					qubits = item.split(" ")[1].split(",")
					gate = item.split(" ")[0]
					if gate == 'NULL':
						continue
					
					if self.__generateIF(content,gate,m,qubits,code):
						continue
					else:
						pass

					#transform the format of the special case 
					if gate == "Toffoli":
						gate = "c1-c1-X"
					elif gate == "CNOT":
						gate = "c1-X"
					else:
						pass

					#if the gate is MCU and the current qubit is the target, that is ,
					#the current qubit isn't in the first postion, then don't export the gate
					if re.search(r'^(c\d-)+.+$',gate) != None and str(qubitList[n].ids) != qubits[0]:
						continue

					#restore the format of the special case
					if gate == "c1-c1-X":
						gate = "Toffoli"
					elif gate == "c1-X":
						gate = "CNOT"
					else:
						pass

					#print the line of QASM code to QASM.txt
					tmpCode = gate + " "
					if gate == "M":
						if len(qubits) != 1:
							try:
								raise CodeError("Can't measure more than one qubit simultaneously")
							except CodeError as ce:
								info = helperFunction.get_curl_info()
								funName = info[0]
								line = info[1]
								interactCfg.writeErrorMsg(ce,funName,line)
						tmpCode += "q[" + qubits[0] + "] -> c[" + qubits[0] +"];"
						tmpCode += "\n"
						code.append(tmpCode)
						continue
					for i in range(0,len(qubits)):
						tmpCode += "q[" + qubits[i] + "]"
						if i != len(qubits)-1:
							tmpCode += ","
					tmpCode += ";"
					tmpCode += "\n"		
					code.append(tmpCode)			
			#print("the code has been stored in " + self.urls.split("..")[1] + "/qasm.txt")
			if alertMsg:
				print("the QASM code has been exported!\n")
			#write the Mif code or Qif code to QASM.txt
			self.__printCode(fileName,code)

			return True
		else:
			try:
				raise EnvironmentError()
			except EnvironmentError as ee:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg(ee,funName,line)

	#export the result of the measurement to charts
	def __exportChart(self,result:list,prob:list,title:str):
		print("begin exporting the result of measurements to charts...")
		if self.checkEnvironment():
			number = len(result)
			#the dimen of the result must be same with the prob
			if number != len(prob):
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("the dimension of the measurement result is not equal, please check your code",funName,line)
			###################################drawing the charts###################################
			#set the canvas
			Fig = plt.figure('chart',figsize=(12,12))
			#plt.title("11")
			#there are two sub-pictures in this picture
			Ax = Fig.add_subplot(111)
			Ax.set_title(title+ ':bar chart')
			plt.grid(True)
			#set the bar width
			bar_width = 0.5
			#set the position of the elements in x-axis
			xticks = []
			for i in range(0,number):
				xticks.append(i + bar_width/2)
			colors = []
			#draw the line-chart
			bars = Ax.bar(xticks, prob, width=bar_width, edgecolor='none')
			Ax.set_ylabel('Prob')
			Ax.set_xlabel('State')
			#set the position of the x-label
			Ax.set_xticks(xticks)
			Ax.set_xticklabels(result)
			#set the range of X-axis and y-axis
			Ax.set_xlim([bar_width/2-0.5, number-bar_width/2])
			Ax.set_ylim([0, 1])
			#set the color to bar
			for bar, color in zip(bars, colors):
			    bar.set_color(color)
			#write the probability on the top of each bar of the bat chart
			for item in range(0,len(xticks)):
				x_position = xticks[item]
				y_position = prob[item]
				if y_position < 0.1:
					yPosition = y_position + 0.01
				else:
					yPosition = y_position - 0.03
				plt.text(x_position,yPosition,'{:.3f}'.format(y_position),ha='center',va='bottom')
			#save the picture
			#plt.show()
			Fig.savefig(self.urls + "/chart.jpg")			
			#print("the circuit has been stored in " + self.urls.split("..")[1]  + "/chart.jpg")
			print("the chart of the circuit has been exported!\n")
			return True
		else:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("the instance is wrong, please check your code!",funName,line)	

	#the aim of the function is to order the idList and get the right state according to the order 
	#of the ids
	def __orderTheId(self,idList:list,order:list):
		for i in range(1,len(idList)):
			tmp = i-1
			while tmp >=0:
				if idList[tmp] > idList[i]:
					idList[i],idList[tmp] = idList[tmp],idList[i]
					order[i],order[tmp] = order[tmp],order[i]
					i = tmp
				tmp -= 1
		return order

	#execute measurement on the qubits
	def execute(self,executeTimes:int):
		if self.checkEnvironment():
			probList = []
			stateList = []
			qubitList = self.measureList.copy()
			hasMeasure = []
			#record the order of the qubit
			idList = []
			gateNum = self.__countGate()
			totalQubitNum = self.qubitNum
			executeRecord = self.qubitExecuteList.copy()
			if self.withOD:
				executeRecordOD = self.qubitExecuteListOD.copy()

			#figure out the AC qubits number and the AX qubits number
			typeQN = self.__countACandAX()

			print("QuanSim is measuring the qubit, please wait for a while...")
			#execute the measurement of the qubits
			for qubit in qubitList:
				if qubit in hasMeasure:
					continue
				hasMeasure.append(qubit)
				#judge whether act qif on this qubit; if so, pass this loop and continue the next one.
				hasQIF = False
				if hasQIF:
					continue
				qs = qubit.entanglement
				#the current qubit is not in entanglement
				if qs == None:
					result = qubit.decideProb()
					#the result is two-dimen, result[0] is the list of probablity, and result[1] is the corresponding state
					probList.append(result[0])
					stateList.append(result[1])
					idList.append(qubit.ids)
					self.__removeQubit([qubit])
					qubit.delete()
					continue
				#the current qubit is in entanglement
				#find the other qubit ,which is also in qs.qubitList and self.measureList
				qubitGroup = []
				for item in qs.qubitList:
					if item in qubitList:
						#item will be measured with the current qubit simultaneously
						#so delete the element from the list to avoid repeating measurement
						#qubitList.remove(item)
						if item not in hasMeasure:
							hasMeasure.append(item)
						hasQIF = False
						#print(executeRecord[item])
						if hasQIF:
							pass
						else:
							#print(executeRecord[item])
							qubitGroup.append(item)
							idList.append(item.ids)
				result = qubit.decideProb(qubitGroup)
				#delete the measured qubit from its entangle state
				self.__removeQubit(qubitGroup)
				qs.deleteItem(qubitGroup)
				#there is no element in qs.qubitList
				if len(qs.qubitList) == 0:
					del qs
				#there is only one element in qs.qubitList, then there is no need to keep qs
				elif len(qs.qubitList) == 1:
					qs.qubitList[0].entanglement = None
					del qs
				else:
					pass

				probList.append(result[0])
				stateList.append(result[1])
			#use the prbList to compute the end prob
			#and the state to compute the end state
			#e.g., prob = [0.5,0.5],state = ['11','00']
			#the state is 0.7|11> + 0.7|00>
			if len(probList) == 0 and len(stateList) == 0:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("there is no qubit need to be measured!",funName,line)
			#print(stateList)
			prob = probList[0]
			state = stateList[0]
			caseNum = 2 ** len(probList)
			for i in range(1,len(probList)):
				tmpProb = []
				tmpState = []
				for j in range(0,len(prob)):
					for k in range(0,len(probList[i])):
						tmpProb.append(prob[j] * probList[i][k])
						tmpState.append(state[j] + stateList[i][k])
				prob = tmpProb
				state = tmpState

			#delete the zero probility and it corresponding state, and get the result
			probResult = []
			stateResult = []
			orderList = [i for i in range(0,len(idList))]
			order = self.__orderTheId(idList,orderList)
			for index in range(0,len(prob)):
				#if the prob is in [-0.00001,0.00001], then we regard it as 0
				if prob[index] > -0.00001 and prob[index] < 0.00001 :
					continue
				#set the order of qubits by ASC
				newStateStr = ""
				for o in order:
					newStateStr += state[index][int(o)]
				probResult.append(prob[index])
				stateResult.append(newStateStr)
			
			#get the actual measure results according to the probResult
			timesList = self.__randomM(executeTimes,probResult)
			endProbResult = []
			for p in range(0,len(probResult)):
				endProbResult.append(timesList[p] / executeTimes)

			#get the end time of the circuit
			self.endTime = datetime.datetime.now()
			self.endMemory = psutil.Process(os.getpid()).memory_info().rss
			#get the end sequence of the ids of the qubit
			title = ""
			for qid in idList:
				title += "q"
				title += str(qid)

			self.__printExecuteMsg(stateResult,endProbResult,gateNum,typeQN) 
			############################exporting############################
			self.__exportChart(stateResult,endProbResult,title)
			self.__exportOriData(stateResult,timesList)
			############################exporting############################

			############################get the QASM and circuit######################################
			global alertMsg
			#use this global parameter to guarantee the alert message of getting 
			#QASM.txt and circuit.jpg will be printed for only once
			alertMsg = True
			#all the whole gate information are stored in "expName/Logical-Level/"
			fileLocation = self.urls+"/Logical-Level/"
			#create the folder
			helperFunction.createFolder(fileLocation)

			self.__exportCircuit(executeRecord,typeQN,fileLocation)
			self.__QASM(executeRecord,fileLocation)
			alertMsg = False

			#if user want to get the original data, then call the following methods
			if self.withOD:
				#in this case, we should give the folder name of the QASM.txt and circuit.jpg
				#all the actually executive information are stored in "expName/Physical-Level/"
				fileLocation = self.urls+"/Physical-Level/"
				#create the folder
				helperFunction.createFolder(fileLocation)

				#self.__exportCircuit(executeRecordOD,typeQN,fileLocation)
				self.__QASM(executeRecordOD,fileLocation)
			############################get the QASM and circuit######################################
			if self.ibm:
				ibm = IBMQX()
				ibm.executeQASM()
			#call the destory function to clean the current instance
			self.__del__()
		else:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("The instance is wrong, please check your code!",funName,line)


	#remove qubitList from this instance; only the qubit has been measured, it can be removed from this instance
	def __removeQubit(self,ql:list):
		for q in ql:
			try:
				if q in self.qubitExecuteList:
					self.qubitNum -= 1
					del self.qubitExecuteList[q]
					self.measureList.remove(q)
			except KeyError:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("KeyError: Q"+ str(q.ids) + " is not in this Circuit instance!",funName,line)

	#split the unit interval into len(probList) parts, and the length of iTH interval is probList[i]
	#product random number for executeTimes, then count the times of number in each interval 
	def __randomM(self,executeTimes,probList):
		timesList = [0] * len(probList)
		#product the prob interval
		interval = []
		sums = 0
		for index in range(0,len(probList)):
			try:
				if index == 0:
					interval.append([0,probList[0]])
				else:
					interval.append([sums,sums+probList[index]])
				sums += probList[index]
			except KeyError as ke:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("key " + str(ke) + " doesn't exist!",funName,line)
		#the error rate is lower then 0.001
		if abs(1 - sums) > 0.001:
			try:
				raise NotNormal()
			except NotNormal as nn:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg(nn,funName,line)
		#product random number for executeTimes
		for i in range(0,executeTimes):
			#judge the number in which interval
			randomNumber = random.uniform(0,1)
			#the demin of timesList and interval must be same
			for j in range(0,len(interval)):
				if randomNumber >= interval[j][0] and randomNumber < interval[j][1]:
					timesList[j] = timesList[j] + 1
		return timesList

	#count the numbers of the gate
	def __countGate(self):
		#the measured qubits of the circuit
		Measure = self.measureList.copy()

		#count the gate number of the circuit
		Single = 0    #stands for the single-qubit gate without compiled
		Multi = 0.0     #stands for the multi-qubit gate without compiled, such as c1-c1-c1-c1-X
		
		#only if circuit.withOD == True, then compute the following two parameter
		SingleOD = 0  #stands for the single gate after compiled
		DoubleOD = 0  #stands for the CNOT gate after compiled

		try:
			from baseGate import allowGate
		except ImportError:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("Can't import the Dict: allowGate in baseGate.py!",funName,line)
		for key in self.qubitExecuteList:
			for operator in self.qubitExecuteList[key]:
				gate = operator.split(" ")[0]
				#the gate NULL is to occupy the position
				if gate == "NULL" or gate == "M":
					continue
				#the format of the gate is M1-M0-X...
				if re.search(r'^(M\d-)+.+$',gate) != None:
					if gate[-1] == "0":
						#the gate isn't executed
						continue
					else:
						if "CNOT" in gate:
							Multi += 1
						else:
							Single += 1
				#the format of the gate is c1-c0-X...
				if re.search(r'^(c\d-)+.+$',gate) != None:
					#if the gate is c1-c1-X, then actually we count the gate for 3 times
					n = len(re.findall("-",gate)) + 1
					Multi += 1/n
				else:
					Single += 1
		if self.withOD:
			for key in self.qubitExecuteListOD:
				for operator in self.qubitExecuteListOD[key]:
					gate = operator.split(" ")[0]
					#the format of the gate is M1-M0-X...
					if re.search(r'^(M\d-)+.+$',gate) != None:
						if gate[-1] == "0":
							#the gate isn't executed
							continue
						else:
							if "CNOT" in gate:
								DoubleOD += 1
							else:
								SingleOD += 1
						continue
					#the gate NULL is to occupy the position
					if gate == "NULL" or gate == "M":
						continue
					elif gate == "CNOT":
						DoubleOD += 1
					elif gate in allowGate or re.search(r'^R\w{1}\(.+\)$',gate) != None:
						SingleOD += 1
					else:
						try:
							raise GateNameError("Gate:" + gate +" hasn't defined in allowGate!")
						except GateNameError as gne:
							info = helperFunction.get_curl_info()
							interactCfg.writeErrorMsg(gne,info[0],info[1])
			#the number of the CNOT count twice when stored in the list, so we should divide 2
			#and the number must be even number
			if DoubleOD & 1 != 0:
				#the number is odd
				try:
					raise CodeError("We count the CNOT gate twice in <QuQ>, and the number of CNOT \
						must be an even number. However, we got an odd number! Please check your code!")
				except CodeError as ce:
					info = helperFunction.get_curl_info()
					interactCfg.writeErrorMsg(ce,info[0],info[1])
			DoubleOD = DoubleOD // 2 
		num = {'measureQubit':Measure,'single-qubit':Single,'multi-qubit':int(Multi+0.5),\
		'single-qubitOD':SingleOD,'double-qubit':DoubleOD}
		return num

	#print the executive message to cmd 
	def __printExecuteMsg(self,stateList,probList,gateNum,typeQN):
		#the total execute time, the unit of the time is second
		totalTime = (self.endTime - self.beginTime).total_seconds()
		#the total memory, the unit of the memory is MB
		totalMemory = ((self.endMemory - self.beginMemory) / 1024) / 1024
		if self.mode == 'theory':
			singleError = 'None'
			doubleError = 'None'
		elif self.mode == 'simulator':
			singleError = 0
			for q in gateNum['measureQubit']:
				error = interactCfg.readCfgGE('single',q.ids)
				singleError += error
			singleError = "%.4f%%"%(singleError / float(len(gateNum['measureQubit'])) * 100)
			doubleError = "%.4f%%"%(interactCfg.readCfgGE('multi') * 100)
		else:
			try:
				raise ExecuteModeError()
			except ExecuteModeError as em:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg(em,funName,line)

		msg = "total qubits: "+ str(typeQN[0]+typeQN[1]) 
		if self.withOD:
			msg += " (Auxiliary: " + str(typeQN[0]) + ")"
		msg += "\n"
		
		msg += "the number of the measured qubits: "+ str(len(gateNum['measureQubit'])) + "\n"
		
		msg += "the number of single-qubit gate: " + str(gateNum['single-qubit']) 
		if self.withOD:
			msg += " (Actually execute " + str(gateNum['single-qubitOD']) + " Single Gates)"
		msg += "\n"

		msg += "the number of multi-qubit gate: " + str(gateNum['multi-qubit'])
		if self.withOD:
			msg += " (Actually execute " + str(gateNum['double-qubit']) + " CNOTs)"
		msg += "\n"

		msg += "executive Mode: " + self.mode + "\n"
		msg += "single-qubit error: " + singleError + " (AVG)\n"
		msg += "double-qubit error: " + doubleError + " (AVG)\n"	
		msg += "result: " + "\n"
		for i in range(0,len(stateList)):
			msg += "        |" + str(stateList[i]) + ">----" + "%.2f%%"%(probList[i] * 100) + "\n"
		msg += "executive time: " + str(totalTime) + "s\n"
		msg += "memory: " + "{:.4f}".format(totalMemory) + "MB\n\n"
		msg += " "*27
		msg += "the circuit has been executed!!\n"
		msg += "-"*80 + '\n'
		#write the message to cmd and the file named "result.log"
		print(msg)
		try:
			file = open(self.urls + "/result.log","a")
			file.write("\n")
			file.write(msg)
			file.close()
		except IOError as io:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg(io,funName,line)
		return True

	def __printPreMsg(self):
		msg = "\n"
		msg += "-"*80 + "\n"
		msg += " "*27
		msg += "begin executing the circuit...\n\n"
		msg += "the experiment: " + self.name
		#write the message to cmd and the file named "result.log"
		print(msg)

		print("\r")
		self.__callIBM()
		print("\r")
		
		try:
			file = open(self.urls + "/result.log","a")
			if self.ibm:
				boolStr = "True"
			else:
				boolStr = "False"
			file.write("Will the experiment be executed on IBMQX?    "+ boolStr + "\n")
			file.write(msg)
			file.close()
		except IOError as io:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg(io,funName,line)
		return True			

	#export the original data of the experiment to the originalData.csv
	def __exportOriData(self,stateList:list,timesList:list):
		print("begin exporting original date to csv...")
		if len(stateList) != len(timesList):
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("there are something wrong with you code!",funName,line)
		csvFile = open(self.urls + "/originalData.csv","w")
		writer = csv.writer(csvFile)
		writer.writerow(['state', 'times'])
		data = []
		for i in range(0,len(stateList)):
			tuples = ('|' + str(stateList[i]) + '>',str(timesList[i]))
			data.append(tuples)
		writer.writerows(data)
		csvFile.close()
		#print("the csv file has been stored in " + self.urls.split("..")[1]  + "/originalData.csv")
		print("the original data has been exported!\n")
		return True

	#run the experiment on IBMQX by class: IBMQX
	def __callIBM(self):
		boolP = True
		#post the qasm code to ibm API according to the users's input:Y/N
		while boolP:
			boolP = False
			ibmBool = input("Do you want to execute your experiment on IBMQX? [Y/N]")
			if ibmBool == 'Y' or ibmBool == 'y':
				#yes
				self.ibm = True
				if self.withOD == False:
					#the Open-QASM is relied on the physical-level qasm.txt
					self.withOD = True
			elif ibmBool == 'N' or ibmBool == 'n':
				#no
				pass
			else:
				boolP = True
				print("Invalid input: Only 'Y' or 'N' is allowed!")

		
