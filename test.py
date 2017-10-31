import sys
import numpy as np
class A:
	def __init__(self):
		self.a = 1

class B(A):
	def __init__(self):
		A.__init__(self)
		self.b = 10
b = B()
print(b.a)
a1 = 4.121111
b1 = 4.131111
print(a1*b1)
c = [1,2]
c1 = [[1],[2]]
print(sys.getsizeof(c))
print(sys.getsizeof(c1))
tmp = [[1,2,3],[4,5,6],[7,8,9]];
a = np.matrix(tmp)
print(type(a))

print(a)
print(a*a)
x = 0-0j
print(x.imag)