import numpy as np
a = np.array([[0,0,0],[0,0,0],[0,0,0]]) # initial difference
b = np.array([[1,2,1],[1,1,1],[1,0,1]])
c = np.array([[1,1,1],[1,1,1],[1,3,1]])

print("arrays:")
print(a)
print(b)
print(c)
print(a.shape)

print("max_arr")
max_arr = a # Inital differences, should be filled with zeroes
print(max_arr)
for arr in [b,c]:
    max_arr = np.maximum(max_arr,arr)
    print(max_arr)

