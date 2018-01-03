#!/usr/bin/python3
#public function is written in this file
import sys
sys.path.append('../baseClass/')

from Bit import Bit

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
	from Qubit import Qubit,Qubits
	precision = readCfgP()
	preStr = '{:.' + str(precision) + 'f}'
	types = type(data)
	if types == Bit:
		print("{\"Type:" + "Bit;")
		print("  Value:" + str(data.value) + ";")
		if 'c' in data.ids:
			print("  Original qubit:" + "None" + ";")
		else:
			print("  Original qubit:" + str(data.ids) + ";")
		print("  ID:" + str(data.ids) +" \"}" )

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


#get the info about the function name and the line number
def get_curl_info():
	try:
		raise Exception
	except:
		f = sys.exc_info()[2].tb_frame.f_back
	return [f.f_code.co_name, f.f_lineno]

#sort the qubitList according to the qubit.ids
def quickSortQubit(ql,low,high):
	i = low
	j = high
	if i >= j:
		return ql
	key = ql[low]
	while i < j:
		while i < j and ql[j].ids <= key.ids:
			j = j-1
		ql[i] = ql[j]
		while i < j and ql[i].ids >= key.ids:
			i = i+1
		ql[j] = ql[i]
	ql[i] = key
	quickSortQubit(ql,low,i-1)
	quickSortQubit(ql,j+1,high)
	return ql
	return True

#judge whether d2 in d1
def dictInDict(d1,d2):
	bools = False
	for k in d2:
		if k in d1 and d2[k] == d1[k]:
			bools = True
		else:
			bools = False
	return bools

#construct the partitioned matrix
def constructPM(m1,m2):
	#use the m1 and m2 as the diagonal element 
	m1_rows = len(m1)
	m1_cols = len(m1[0])
	m2_rows = len(m2)
	m2_cols = len(m2[0])
	mNew = []
	mNew_cols = m1_cols * m2_cols
	mNew_rows = m1_rows * m2_rows
	for i in range(0,m1_rows):
		for l in range(0,m2_rows):
			tmp = []
			for j in range(0,m1_cols):
				for k in range(0,m2_cols):
					tmp.append(m1[i][j] * m2[l][k])
			mNew.append(tmp)
	return mNew

#sort the list1 according to the list2
def adjustOrder(list1:list,list2:list):
	for i in range(1,len(list2)):
		tmp = i-1
		while tmp >=0:
			if list2[tmp] > list2[i]:
				list2[i],list2[tmp] = list2[tmp],list2[i]
				list1[i],list1[tmp] = list1[tmp],list1[i]
				i = tmp
			tmp -= 1
	return True

#judge whether there is repeating element in the list.
#If two elements have the same address, then we say that the two elements are repeating elements.
#if there is repeating elements, then return True; else return False
def repeatElement(lt:list):
	for i in range(0,len(lt)):
		for j in range(i+1,len(lt)):
			if id(lt[i]) == id(lt[j]):
				return True
	return False