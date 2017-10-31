#!/usr/bin/python3
#the Bit class represent the standard classical bit
#in python3, the a int occupies 28 bits.

class Bit:
	def __init__(self,value = 0):
		if value != 0 and value != 1:
			raise ValueError('Bit must be 0 or 1')
		self.value = value

	#overwrite the add operator of bits
	def __add__(self,other):
		return (str(self.value) + str(other.value))
	#please note that the first argument must Bit and the second argument must be str
	def __add__(self,other:str):
		return (str(self.value) + other)
