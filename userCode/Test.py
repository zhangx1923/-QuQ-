from header import *

def u():
	c = Circuit(True)
	q0 = Qubit()
	q1 = Qubit()
	q2 = Qubit()
	q3 = Qubit()
	Rx(PI/4,q3)
	Rx(PI/4,q3)
	Rx(PI/4,q3)
	Rx(PI/4,q3)
	# with DMif([q0,q1],[1,0]) as dmo:
	# 	dmo.H(q2)
	# 	dmo.CNOT(q2,q3)
	# with Qif([q0,q1],[1,0]) as isTrue:
	# 	if isTrue:
	# 		H(q2)
	# 		CNOT(q2,q3)
	#M(q2)
	M(q3)
	c.execute(1024)
	# bt = c.beginTime
	# bm = c.beginMemory
	# sums = 1
	# for i in range(1,2001):
	# 	sums *= i
	# 	time.sleep(0.001)
	# c.execute(1)
	# et = c.endTime
	# em = c.endMemory
	# print("消耗时间：%d S"%(et-bt).total_seconds())
	# print("占用内存：%d bit"%(em-bm))
	#c.execute(1)
	# q = Qubit()
	# qList = []
	# for i in range(0,2):
	# 	qList.append(Qubit())
	# #Rx(PI,qList[0])
	# #Rx(PI,qList[0])
	# #X(q)
	# #QSprint(qList[0])
	# #X(q)
	# #Toffoli(q,qList[0],qList[1])
	# #CNOT(qList[0],qList[1])
	# with Mif([qList[0],qList[1]],[0,0]) as mo:
	# 	mo.X(q)
	# 	#mo.H(qList[1])
	# 	#mo.CNOT(q,qList[1])
	# 	# mo.CNOT(qList[2],qList[1])
	# q1 = Qubit()
	# q2 = Qubit()
	# Rx(PI,q2)
	# #print(c.qubitExecuteListOD)
	# #Rx(PI/2,q)
	# with DMif([q1,q2],[0,1]) as dmo:
	# 	dmo.H(q)
	# 	#dmo.H(qList[1])
	# 	#q = dmo.Ry(PI,q)[-1]
	# 	#q = dmo.Rz(-PI/2,q)[-1]
	# # with DMif([qList[0],qList[1]],[1,0]) as dmo:
	# # 	dmo.H(q)
	# #M(qList[1])
	# #QSprint(q)
	# #QSprint(q.entanglement)
	# #M(q)
	# #QSprint(q)
	# M(q)
	# #M(qList[0])
	#c.execute(1024)