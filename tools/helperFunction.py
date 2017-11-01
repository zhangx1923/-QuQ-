#!/usr/bin/python3
#public function is written in this file
import sys
sys.path.append('../baseClass/')

from Bit import Bit
from Qubit import *
#from Circuit import *
from interactCfg import *

#return a str according to the number of qubits and the postion of 1
#For example: getCorrespondStr(3,0) = 00000001; (3,1) = 00000010 
def getCorrespondStr(number,position):
	strs = bin(int(position)).split('b')[1]
	while len(strs) < number:
		strs = '0' + strs
	return strs

#suggest use this function to print message
#it can decide the style of output according to the type of the input
def QSprint(data):
	precision = readCfgP()
	preStr = '{:.' + str(precision) + 'f}'
	types = type(data)
	if types == Bit:
		print("{\"Type:" + "Bit;")
		print("  Value:" + str(data.value) + " \"}")

	if types == Qubit:
		print("{\"Type:" + "Qubit;")
		#the amplitude is complex will disturb the format
		amplitude = data.getAmp()
		coefficient0 = amplitude[0]
		coefficient1 = amplitude[1]
		if coefficient0.imag == 0:
			coefficient0 = coefficient0.real
		if coefficient1.imag == 0:
			coefficient1 = coefficient1.real
		value = preStr.format(coefficient0) + "|0> + " + preStr.format(coefficient1) + "|1>"
		print("  Value:" + value + ";")
		print("  ID:" + str(data.ids) +" \"}" )
		
	if types == Qubits:
		print("{\"Type:" + "Qubits;")
		print("  The Number of Qubits:" + str(data.number))
		qubitStr = ""
		for i in range(0,data.number):
			qubitStr += "Q" + str(data[i].ids) + ";"
		print("  They are:" + qubitStr )
		value = ""
		length = 2**data.number
		amplitude = data.getAmp()
		for j in range(0,length):
			real = amplitude[j].real
			imag = amplitude[j].imag
			if real == 0 and imag == 0:
				continue
			elif imag == 0 and real != 0:
				value += preStr.format(real) + "|" + getCorrespondStr(data.number,j) + ">"
			elif imag != 0 and real == 0:
				value += preStr.format(imag) + "|" + getCorrespondStr(data.number,j) + ">"
			else:
				value += "(" + preStr.format(real) + "+" + preStr.format(imag) + "j)" + "|" + getCorrespondStr(data.number,j) + ">"
			if j != (length-1):
				value += "+" 
		print("  Value:" + value +" \"}")
