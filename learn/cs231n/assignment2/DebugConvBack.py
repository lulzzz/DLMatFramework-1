

import numpy as np
import scipy.io
import matplotlib.pyplot as plt
from cs231n.classifiers.cnn import *
from cs231n.data_utils import get_CIFAR10_data
from cs231n.gradient_check import eval_numerical_gradient_array, eval_numerical_gradient
from cs231n.layers import *
from cs231n.fast_layers import *
from cs231n.solver import Solver


def rel_error(x, y):
  """ returns relative error """
  return np.max(np.abs(x - y) / (np.maximum(1e-8, np.abs(x) + np.abs(y))))


# # Convolution: Naive backward pass
# Implement the backward pass for the convolution operation in the function `conv_backward_naive` in the file `cs231n/layers.py`. Again, you don't need to worry too much about computational efficiency.
# 
# When you are done, run the following to check your backward pass with a numeric gradient check.

# In[14]:

# Load from matfile the parameters
dictMat = scipy.io.loadmat('../../../test/layers/conv_backward_cs231n.mat')
x = dictMat['x']
w = dictMat['w']
b = dictMat['b']
dout = dictMat['dout']

conv_param = {'stride': 1, 'pad': 1}

dx_num = eval_numerical_gradient_array(lambda x: conv_forward_naive(x, w, b, conv_param)[0], x, dout)
dw_num = eval_numerical_gradient_array(lambda w: conv_forward_naive(x, w, b, conv_param)[0], w, dout)
db_num = eval_numerical_gradient_array(lambda b: conv_forward_naive(x, w, b, conv_param)[0], b, dout)

# Test the conv with im2col version of forward/backward propagation
out, cache = conv_forward_im2col(x, w, b, conv_param)
dx, dw, db = conv_backward_im2col(dout, cache)

# Your errors should be around 1e-9'
print ('Testing conv_backward_naive function')
print ('dx error: ', rel_error(dx, dx_num))
print ('dw error: ', rel_error(dw, dw_num))
print ('db error: ', rel_error(db, db_num))

# Some tests with im2col (Preparing the image x to be convolved with a 3,3 kernel with stride:1 pad:1
H = 5
W = 5
filter_height = 3
filter_width = 3
pad = 1
stride = 1

# Calculate spatial output sizes
out_height = (H + 2 * pad - filter_height) / stride + 1
out_width = (W + 2 * pad - filter_width) / stride + 1

print('\n\noriginal x: ', x.shape)
x_cols = im2col_cython(x, filter_height, filter_width, pad, stride)
print('im2col result: ', x_cols.shape)
print('Conv out height: %d width: %d' % (out_height, out_width))

# Save vectors to matlab for tests
import scipy.io

dictSaveMat={}
dictSaveMat['x']=x.astype('float')
dictSaveMat['x_cols']=x_cols.astype('float')
dictSaveMat['pad']=pad
dictSaveMat['stride']=stride
dictSaveMat['filter_height']=filter_height
dictSaveMat['filter_width']=filter_width
scipy.io.savemat('im2col_with_batch_cs231n',dictSaveMat)

dictMat = scipy.io.loadmat('SimpleInput.mat')
x_simple = dictMat['x_simple']
x_simple = x_simple.transpose(3,2,0,1)
x_simple = x_simple.astype('float')
x_simple = x_simple.reshape(2, 3, 4, 4)
x_cols_simple = im2col_cython(x_simple, 2, 2, 0, 1)
1+1