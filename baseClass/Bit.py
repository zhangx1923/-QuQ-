#!/usr/bin/python3
#the Bit class represent the standard classical bit
#get the info about the function name and the line number
def get_curl_info():
	try:
		raise Exception
	except:
		f = sys.exc_info()[2].tb_frame.f_back
	return [f.f_code.co_name, f.f_lineno]

class Bit:
	idList = []
	def __init__(self,value = None,ids = None):
		if value == None:
			value = 0
		self.value = value
		if ids == None:
			if len(Bit.idList) == 0:
				ids = 0
			else:
				ids = max(Bit.idList) + 1
			self.ids = 'c' + str(ids)
		else:
			self.ids = 'q' + str(ids)
		#the index of the current bit, the range is from 0 to n
		if ids in Bit.idList:
			try:
				raise IDRepeatError()
			except IDRepeatError as ir:
				info = get_curl_info()
				funName = info[0]
				line = info[1]
				interactCfg.writeErrorMsg(ir,funName,line)
		Bit.idList.append(ids)		

	#overwrite the add operator of bits
	def __add__(self,other):
		return (str(self.value) + str(other.value))
	#please note that the first argument must Bit and the second argument must be str
	def __add__(self,other:str):
		return (str(self.value) + other)