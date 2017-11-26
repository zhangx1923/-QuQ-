import sys
sys.path.append('../userCode/')
sys.path.append('../tools/')
from interactCfg import readCfgEA
import warnings
#from Grover import grover

if __name__ == "__main__":
	#ignore the warning message
	warnings.filterwarnings("ignore")
	print('-' * 80)
	print('')
	print(' '*30 + "Welcome to QuanSim!" + " "*20)
	print('')
	print('-' * 80)
	# import_string = "from Grover import grover"
	# exec(import_string)
	# grover()
	funName = ""
	funFile = ""
	functionList = readCfgEA()
	way = -1
	#there are two ways to execute the code
	#1.give the function name as a parameter, the format of the parameter is xx()
	#2.input the number of the function you want to run 
	if len(sys.argv) == 2:
		way = 1
		#the first way
		funName = sys.argv[1]
		for function in functionList:
			if funName == function[1]:
				funFile = function[0]
		if funFile == "":
			print("Invalid parameter! The format of the function name must be xx()!")
			way = 2
	elif len(sys.argv) == 1:
		#the second way
		way = 2
	else:
		print("Invalid parameter! There can only be one parameter, and the format of it is 'xx()'!") 
		way = 2
	if way == 2:
		#the second way
		print(' '*26 + 'The following code is vaild:' + ' '*20)
		
		for i in range(1,len(functionList)+1):
			print(str(i) + ':' + functionList[i-1][1])
		ids = input("Please enter the number of the code you want to execute:")
		try:
			funName = functionList[int(ids)-1][1]
			funFile = functionList[int(ids)-1][0]
		except ValueError:
			print("ValueError: The input is not a number!")
			sys.exit(0)
		except KeyError:
			print("KeyError: The input number is invalid! ")
			sys.exit(0)
	print("The code you want to execute is :" + funFile + "." + funName)
	import_string = "from " + funFile + " import " + funName.split("(")[0]
	try:
		exec(import_string)
		exec(funName)
	except ImportError as ie:
		print("ImportError: " + str(ie))
		sys.exit(0)




