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

styleDic = {
	"I":[" I ","C5"],
	"X":["X","C1"],
	"Y":["Y","C1"],
	"Z":["Z","C1"],
	"H":["H","C2"],
	"S":["S","C8"],
	"T":["T","C4"],
	"CNOT":["+","C0"],
	"Td":["Td","C6"],
	"Sd":["Sd","C7"],
	"M":["M","C3"],
	"qif":["qif","C3"]
}
qasmDic = {
	"I":"id",
	"X":"x",
	"Y":"y",
	"Z":"z",
	"H":"h",
	"S":"s",
	"T":"t",
	"CNOT":"cx",
	"Td":"tdg",
	"Sd":"sdg",
	"M":"measure",
	"qif":"qif"
}

ResLocation = "../results/"

#the data-type is the elementary unit of executing and export
class Circuit:
	#mark the environment: we can execute the code when there is only one circuit in the environment
	currentIDList = []
	instance = None

	def __init__(self,experimentName=None):
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
		#create a new folder to save the experiment
		if os.path.exists(ResLocation+self.name) == False:
			#the whole result of the experiment is stored in this folder
			try:
				os.makedirs(ResLocation+self.name) 
			except OSError:
				info = helperFunction.get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg("Can't create the new folder '" + self.name + "'!",funName,line)	

		self.urls = ResLocation+self.name
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
		#print information
		self.__printPreMsg()

	#the destory function
	def __del__(self):
		ids = id(self)
		if ids in Circuit.currentIDList:
			Circuit.currentIDList.remove(id(self))
		else:
			return

	#check the environment: whether the current circuit is equal to this instance 
	def checkEnvironment(self):
		circuitNum = len(Circuit.currentIDList)
		if self.qubitNum != len(self.qubitExecuteList):
			return False
		#there only can be one instance and the id of this instance must be equal with self.ids
		if circuitNum == 1 and Circuit.currentIDList[0] == self.ids:
			return True
		try:
			strs = "there are " + str(len(Circuit.currentIDList)) + " Circuit instance, please check your code"
			raise EnvironmentError(strs)
		except EnvironmentError as ee:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg(ee.value,funName,line)

	#draw the circuit according to the qubitExecuteList
	def __exportCircuit(self,er):
		if self.checkEnvironment():
			print("begin drawing the circuit...")
			#set the canvas
			Fig = plt.figure('circuit',figsize=(12,6))                      
			#set the axis off
			plt.axis('off')
			#devide the canvas into 1row 1col, and our pic will be draw on the first place(from up to down, from left to right)
			Ax = Fig.add_subplot(111)
			qubitNum = len(er.keys())
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
				maxLength = max(maxLength,len(er[qe]))
				q_keys.append(qe)
			quickSortQubit(q_keys,0,len(q_keys)-1)
			for q in q_keys:
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
					#adjust the length of the gate string
					try:
						gateName = styleDic[gate][0]
						gateColor = styleDic[gate][1]
					except KeyError as ke:
						info = helperFunction.get_curl_info()
						funName = info[0]
						line = info[1]
						interactCfg.writeErrorMsg("key " + str(ke) + " is not in Dict:styleDic!",funName,line)
					if gateName == "+":
						style = "circle"
						#wheter the current qubit is the control-qubit
						targetQubit = item.split(" ")[1].split(",")[1]
						controlQubit = item.split(" ")[1].split(",")[0]
						indexOfTarget = 0
						#get the index of the target qubit
						for tmp in q_keys:
							if str(tmp.ids) != targetQubit:
								indexOfTarget += 1
							else:
								break
						#draw a red circle in the control qubit
						if str(q.ids) == controlQubit:
							smaller = min(indexOfTarget,j)
							bigger = max(indexOfTarget,j)
							x1 = [x_position] * (bigger * partition - smaller * partition)
							y1 = range(smaller * partition,bigger * partition)
							Ax.plot(x1,y1,gateColor)
							ann = Ax.annotate("1",
                  				xy=(1, 20), xycoords='data',color=gateColor,
                  				xytext=(x_position, j*partition), textcoords='data',
                  				size=6/factor, va="center", ha="center",
                  				bbox=dict(boxstyle="circle", fc=gateColor,pad=0.3,ec=gateColor),
                  			)
							x_position += 5/factor
                  			#don't draw the CX
							continue
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
			Fig.savefig(self.urls + "/circuit.jpg")			
			#print("the circuit has been stored in " + self.urls.split("..")[1]  + "/circuit.jpg")
			print("the circuit has been drawn!\n")
			return True
		else:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("the circuit instance is wrong, please check your code",funName,line)

	#translate the code of the current circuit to QASM, so that they can be executed on IBMQX
	def __QASM(self,er):
		print("begin export the QASM code of the circuit...")
		if self.checkEnvironment():
			qubitNum = len(er.keys())
			code = open(self.urls+"/qasm.txt","w")
			codeHeader = 'OPENQASM 2.0;include "qelib1.inc";qreg q[' + str(qubitNum) + '];creg c[' + str(qubitNum) + '];'
			code.write(codeHeader)
			code.write("\n")
			#get the ids of the qubit
			qubitList = []
			for q in er.keys():
				qubitList.append(q)
			#get the max length of the execute path
			maxGate = 0
			for i in range(0,qubitNum):
				if maxGate < len(er[qubitList[i]]):
					maxGate = len(er[qubitList[i]])
			#draw the circuit 
			for m in range(0,maxGate):
				for n in range(0,qubitNum):
					content = er[qubitList[n]]
					length = len(content)
					#if there is no element to be draw, skip the loop
					if m > length-1:
						continue
					item = content[m]
					qubits = item.split(" ")[1].split(",")
					gate = item.split(" ")[0]
					if gate == 'NULL' or gate == 'qif':
						continue
					try:
						gate = qasmDic[gate]
					except KeyError as ke:
						info = helperFunction.get_curl_info()
						funName = info[0]
						line = info[1]
						interactCfg.writeErrorMsg("key " + str(ke) + " doesn't exist",funName,line)
					#if the gate is CNOT and the current qubit is the target, that is ,
					#the current qubit is in the 2th postion, then don't draw the gate
					if gate == "cx" and str(qubits[1]) == str(qubitList[n].ids):
						continue
					code.write(gate + " ")
					if gate == "measure":
						if len(qubits) != 1:
							try:
								raise CodeError("Can't measure more than one qubit simultaneously")
							except CodeError as ce:
								info = helperFunction.get_curl_info()
								funName = info[0]
								line = info[1]
								interactCfg.writeErrorMsg(ce.value,funName,line)
						code.write("q[" + qubits[0] + "] -> c[" + qubits[0] +"];")
						code.write("\n")
						continue
					for i in range(0,len(qubits)):
						code.write("q[" + qubits[i] + "]")
						if i != len(qubits)-1:
							code.write(",")
					code.write(";")
					code.write("\n")					
			#print("the code has been stored in " + self.urls.split("..")[1] + "/qasm.txt")
			print("the QASM code has been exported!\n")
			return True
		else:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("the instance is wrong, please check your code!",funName,line)

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
			print("QuanSim is measuring the qubit, please wait for a while...")
			#execute the measurement of the qubits
			for qubit in qubitList:
				if qubit in hasMeasure:
					continue
				hasMeasure.append(qubit)
				#judge whether act qif on this qubit; if so, pass this loop and continue the next one.
				hasQIF = False
				for gates in executeRecord[qubit]:
					if "qif" in gates:
						hasQIF = True
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
						for gates in executeRecord[item]:
							if "qif" in gates:
								hasQIF = True
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
			self.__printExecuteMsg(stateResult,endProbResult,gateNum,totalQubitNum) 
			############################exporting############################
			self.__exportCircuit(executeRecord)
			self.__QASM(executeRecord)
			self.__exportChart(stateResult,endProbResult,title)
			self.__exportOriData(stateResult,timesList)
			#post the qasm code to ibm API according to the users's input:Y/N
			ibmBool = input("Do you want to execute your circuit on IBMQX? [Y/N]")
			if ibmBool == 'Y' or ibmBool == 'y':
				#yes
				ibm = IBMQX()
				ibm.executeQASM()
			elif ibmBool == 'N' or ibmBool == 'n':
				#no
				pass
			else:
				print("Invalid input! Only 'Y' or 'N' is allowed! ")
			#call the destory function to clean the current instance
			self.__del__()
		else:
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("the instance is wrong, please check your code!",funName,line)


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
		#count the single-qubit and the double-qubit gate number of the circuit
		Single = 0
		Double = 0
		Other = 0
		for key in self.qubitExecuteList:
			for operator in self.qubitExecuteList[key]:
				gate = operator.split(" ")[0]
				#the gate NULL is to occupy the position
				if gate == "NULL":
					continue
				if gate == "X" or gate == "Y" or gate == "Z" or gate == "S" or gate == "T" or \
				gate == "Td" or gate == "Sd" or gate == "H" or gate == "I":
					Single += 1
				elif gate == "CNOT":
					Double += 1
				elif gate == "M":
					continue
				else:
					Other += 1
		#the number of the CNOT count twice when stored in the list, so we should divide 2
		#and the number must be even number
		if Double & 1 != 0:
			#the number is odd
			info = helperFunction.get_curl_info()
			funName = info[0]
			line = info[1]
			interactCfg.writeErrorMsg("we count the CNOT gate twice, the number of this gate must be even number; \
				but we get an odd number. Please check your code!",funName,line)
		Double = Double // 2 
		num = {'measureQubit':Measure,'single-qubit':Single,'double-qubit':Double,'other':Other}
		return num

	#print the executive message to cmd 
	def __printExecuteMsg(self,stateList,probList,gateNum,totalQubitNum):
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
		msg = "total qubits: "+ str(totalQubitNum) + "\n"
		msg += "the number of the measured qubits: "+ str(len(gateNum['measureQubit'])) + "\n"
		msg += "the number of single-qubit gate: " + str(gateNum['single-qubit']) + "\n"
		msg += "the number of double-qubit gate: " + str(gateNum['double-qubit']) + "\n"
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
		try:
			file = open(self.urls + "/result.log","a")
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

		
