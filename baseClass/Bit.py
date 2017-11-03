#!/usr/bin/python3
#the Bit class represent the standard classical bit

class Bit:
	def __init__(self,value = 0,ids = None):
		if value != 0 and value != 1:
			raise ValueError('Bit must be 0 or 1')
		self.value = value
		if ids == None:
			self.ids
		else:
			self.ids = ids

	#overwrite the add operator of bits
	def __add__(self,other):
		return (str(self.value) + str(other.value))
	#please note that the first argument must Bit and the second argument must be str
	def __add__(self,other:str):
		return (str(self.value) + other)
