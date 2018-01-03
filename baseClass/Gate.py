#!/usr/bin/python3
from baseGate import *

def X(q:Qubit):
	X = [[0,1],[1,0]]
	gate = Gate([q],X,"X")
	return gate.singleOperator()

def Y(q:Qubit):
	Y = [[0,-1j],[1j,0]]
	gate = Gate([q],Y,"Y")
	return gate.singleOperator()

def Z(q:Qubit):
	Z = [[1,0],[0,-1]]
	gate = Gate([q],Z,"Z")
	return gate.singleOperator()

def I(q:Qubit):
	I = [[1,0],[0,1]]
	gate = Gate([q],I,"I")
	return gate.singleOperator()


def H(q:Qubit):
	H = [[1/math.sqrt(2),1/math.sqrt(2)],[1/math.sqrt(2),-1/math.sqrt(2)]]
	gate = Gate([q],H,"H")
	return gate.singleOperator()

def S(q:Qubit):
	S = [[1,0],[0,1j]]
	gate = Gate([q],S,"S")
	return gate.singleOperator()

def Sd(q:Qubit):
	Sd = [[1,0],[0,-1j]]
	gate = Gate([q],Sd,"Sd")
	return gate.singleOperator()


def T(q:Qubit):
	T = [[1,0],[0,(1+1j)/math.sqrt(2)]]
	gate = Gate([q],T,"T")
	return gate.singleOperator()

def Td(q:Qubit):
	Td = [[1,0],[0,(1-1j)/math.sqrt(2)]]
	gate = Gate([q],Td,"Td")
	return gate.singleOperator()

#return a Qubits, which has two entanglement qubit
#the two qubit can be independent qubits, or one of them are a part of engtanlement 
#the first qubit is the control-qubit, the second qubit is the target-qubit
def CNOT(q1:Qubit,q2:Qubit):
	CNOT = [[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]]
	gate = Gate([q1,q2],CNOT,"CNOT")
	return gate.CNOTOperator()


#execute the measurement, the types of the first argument must be Qubit; the second argument is optional,
#if the auQubit is "False", then the result of the measurement won't be appeared in the end result 
def M(q:Qubit,auQubit = False):
	I = [[1,0],[0,1]]
	gate = Gate([q],I,"M")
	return gate.MOperator(auQubit)

#Toffoli gate, three input and three output
def Toffoli(q1:Qubit,q2:Qubit,q3:Qubit):
	H(q3)
	CNOT(q2,q3)
	Td(q3)
	CNOT(q1,q3)
	T(q3)
	CNOT(q2,q3)
	Td(q3)
	CNOT(q1,q3)
	Td(q2)
	T(q3)
	CNOT(q1,q2)
	H(q3)
	Td(q2)
	CNOT(q1,q2)
	T(q1)
	S(q2)
	return True
