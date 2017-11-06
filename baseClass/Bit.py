#!/usr/bin/python3
#the Bit class represent the standard classical bit

class Bit:
	idList = []
	def __init__(self,value = 0,ids = None):
		if value != 0 and value != 1:
			raise ValueError('Bit must be 0 or 1')
		self.value = value
		if ids == None:
			if len(Bit.idList) == 0:
				ids = 0
			else:
				ids = max(Bit.idList) + 1
		#the index of the current bit, the range is from 0 to n
		if ids in Bit.idList:
			try:
				raise IDRepeatError()
			except IDRepeatError as ir:
				interactCfg.writeErrorMsg(ir)
		self.ids = ids
		Bit.idList.append(ids)		

	#overwrite the add operator of bits
	def __add__(self,other):
		return (str(self.value) + str(other.value))
	#please note that the first argument must Bit and the second argument must be str
	def __add__(self,other:str):
		return (str(self.value) + other)
