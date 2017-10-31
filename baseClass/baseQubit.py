#!/usr/bin/python3
import math
class BaseQubit:
	def __init__(self):
		self.matrix = []
		self.amplitude = []

	def setAmp(self):
		matrix = self.getMatrix()
		self.amplitude = [0] * len(matrix)
		for i in range(0,len(matrix)):
			self.amplitude[i] = matrix[i][0]

	#this function will be called when act a gate on the qubit
	def setMatrix(self,newMatrix:list):
		self.matrix = newMatrix
		self.setAmp()
	
	def getMatrix(self):
		return self.matrix
	def getAmp(self):
		return self.amplitude

	def normalize(self):
		newMatrix = self.getMatrix()
		sums = 0
		for item in newMatrix:
			sums += (item[0] * item[0].conjugate())
		#the imag of the sums must be zero
		denominator = math.sqrt(sums.real)
		for i in range(0,len(newMatrix)):
			newMatrix[i][0] = newMatrix[i][0] / denominator
		#set the result to the amplitude and the matrix of the current instance 
		self.setMatrix(newMatrix)

	#overwrite the multiply to express the tensor product  
	def __mul__(self,other):
		newMatrix = []
		selfMatrix = self.getMatrix()
		otherMatrix = other.getMatrix()
		for i in range(0,len(selfMatrix)):
			for j in range(0,len(otherMatrix)):
				item = []
				item.append(selfMatrix[i][0] * otherMatrix[j][0])
				newMatrix.append(item)
		return newMatrix


		