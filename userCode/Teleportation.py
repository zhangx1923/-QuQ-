from header import *
#the flow of this algorithm is designed as follow:
#1.prepare the Bell state
#2.implement the algorithm according to Nielsen and L.Chuang 
def teleportation():
	c = Circuit()
	#store the unknow quantum state, the aim of this algorithm is teleporting the state of AliceQ to BobQ
	AliceQ = Qubit()
	#the two qubit is entanglement with each other
	AliceQ2 = Qubit()
	BobQ = Qubit()
	H(AliceQ2)
	CNOT(AliceQ2,BobQ)
	CNOT(AliceQ,AliceQ2)
	H(AliceQ)
	CNOT(AliceQ2,BobQ)
	#######Control-Z#########
	H(BobQ)
	CNOT(AliceQ,BobQ)
	H(BobQ)
	#########################
	BobQ = M(BobQ)
	c.execute(1024)