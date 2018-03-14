#!/usr/bin/python3
#interact with the cfg file
import datetime
import json
import sys
import os
sys.path.append('../baseClass/')
cfgLocation = "../config/"

#write the error message to LOG when error occurs
def writeErrorMsg(msg,funName,line):
	print("Unfortunately, the following errors were happened in QuanSim when running the code:")
	funName = "Function Name: "+ str(funName) + "()"
	line = "Line: "+ str(line)
	print(funName)
	print(line)
	print(msg)
	
	#import the Circuit class
	from Circuit import Circuit
	circuit = Circuit.instance
	if circuit == None:
		print("there is no circuit instance in the code, please add at least one instance!")
	else:	
		file = open(circuit.urls + "/errorMsg.txt","a")
		time = datetime.datetime.now()
		errorStr = "Time:" + str(time) + "\r\n"
		errorStr += "Error Message: "
		errorStr += str(msg)
		errorStr += "\r\n"
		errorStr += funName
		errorStr += "\r\n"
		errorStr += line
		file.write(errorStr)
		file.close
	sys.exit(1)

#read the config file about the executeMode (EM for short)
def readCfgEM():
	try:
		EMcfg = cfgLocation + "executeMode.cfg"
		confFile = open(EMcfg,"r")
		content = confFile.readline()
		mode = json.loads(content)['executeMode']
	except IOError as io:
		writeErrorMsg(io)
	except KeyError as ke:
		writeErrorMsg("Key: "+ str(ke) + "doesn't exist in executeMode.cfg, please check the cfg file!")
	confFile.close()
	return mode

#read the config file about the output precision (P for short)
#the type of return-value is int
def readCfgP():
	try:
		EMcfg = cfgLocation + "executeMode.cfg"
		confFile = open(EMcfg,"r")
		content = confFile.readline()
		content = confFile.readline()
		pre = json.loads(content)['precision']
		pre = int(pre)
	except IOError as io:
		writeErrorMsg(io)
	except KeyError as ke:
		writeErrorMsg("Key: "+ str(ke) + "doesn't exist in executeMode.cfg, please check the cfg file!")
	except TypeError as te:
		writeErrorMsg(te)
	confFile.close()
	return pre			

#read the config file about the assignment error (ER for short)
def readCfgER(ids):
	#the error of readout error is the fidelity, and shouldn't be read directly
	#it's the cumulative results in average
	return 0.0

	# try:
	# 	ERcfg = cfgLocation + "errorRate.cfg"
	# 	confFile = open(ERcfg,"r")
	# 	content = confFile.readline()
	# 	errorList = json.loads(content)['assignmentError']
	# 	#our data is equal with IBMqx5, there are only 15qubits; so we only have 15 items 
	# 	#if current id is bigger then 15, compute ids%15
	# 	errorRate = float(errorList[str(ids%15)])
	# except IOError as io:
	# 	writeErrorMsg(io)
	# except KeyError as ke:
	# 	writeErrorMsg("Key: "+ str(ke) + "doesn't exist in errorRate.cfg, please check the cfg file!")
	# confFile.close()
	# return errorRate

#read the config file about the gate error (GE for short)
#if the para gateType == single, then get the single-qubit gate error according to the qid
#if the para gateType == multi, then get the multi-qubit gate error; 
#in the second case, all the qubit have the same error rate
def readCfgGE(gateType:str,qid = None):
	if gateType == 'single' and qid == None:
		writeErrorMsg("You want to get the single-qubit gate error, but don't give the id of the qubit!") 
	try:
		ERcfg = cfgLocation + "errorRate.cfg"
		confFile = open(ERcfg,"r")
		content = confFile.readlines()
		for line in content:
			js = json.loads(line)
			if gateType in js.keys():
				if gateType == "single":
					errorRate = float(js[gateType][str(qid%15)])
				elif gateType == "multi":
					errorRate = float(js[gateType])
				else:
					writeErrorMsg("There are only two kinds of gate errors: 'single' or 'multi'; but you gave another one!")
	except IOError as io:
		writeErrorMsg(io)
	except KeyError as ke:
		writeErrorMsg("Key: "+ str(ke) + "doesn't exist in errorRate.cfg, please check the cfg file!")
	confFile.close()
	return errorRate	

#read the config file about the personal message on IBMQX(PM for short)
def readCfgPM():
	result = {}
	try:
		message = cfgLocation + "IBMToken.cfg"
		confFile = open(message,"r")
		lines = confFile.readlines()
		for line in lines:			
			pm = json.loads(line)
			result = dict(result,**pm)
	except IOError as io:
		writeErrorMsg(io)
	except KeyError as ke:
		writeErrorMsg("Key: "+ str(ke) + "doesn't exist in IBMToken.cfg, please check the cfg file!")
	except TypeError as te:
		writeErrorMsg(te)
	confFile.close()
	return result	

#read the config file about the existing algorithm(EA for short)
def readCfgEA():
	try:
		EAcfg = cfgLocation + "function.cfg"
		confFile = open(EAcfg,"r")
		content = confFile.readlines()
		result = []
		for line in content:
			fileName = json.loads(line)['fileName']
			function = json.loads(line)['entryFunction']
			result.append([fileName,function])
	except IOError as io:
		writeErrorMsg(io)
	except KeyError as ke:
		writeErrorMsg("Key: "+ str(ke) + "doesn't exist in function.cfg, please check the cfg file!")
	confFile.close()
	return result	

