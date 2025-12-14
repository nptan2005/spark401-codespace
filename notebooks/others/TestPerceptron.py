import Perceptron as p
import numpy as np

# Generate data set

from sklearn.model_selection import train_test_split

N = None
means = [[2, 2], [4, 4]]
cov = [[1, 0], [0, 1]]

N = 500
C = 2

X_0 = np.random.multivariate_normal(means[0], cov, N)
X_1 = np.random.multivariate_normal(means[1], cov, N)

X = np.concatenate((X_0, X_1), axis = 0)
y = np.array([[-1]*N,[1]*N]).reshape(C*N,)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20)


w_dot, error_history = p.train_verbose(X_train, y_train, epochs = 20, learning_rate=0.1)

print(w_dot)
print(error_history)
# TODO: calculate y_pred based on learned w_dot
X_test_dot = p.generate_X_dot(X_test)
y_pred = p.predict(X_test_dot,w_dot)
# print(w_dot.shape)
# print(X_test.shape)
from sklearn.metrics import accuracy_score
print("Accuracy: %.2f %%" %(100*accuracy_score(y_test, y_pred)))

#-------------
# print (X_test[0])

import matplotlib.pyplot as plt

plt.scatter(X_test[:,0], X_test[:,1], s=10, c=y_test)


plt.show()

plt.scatter(X_test[:,0], X_test[:,1], s=10, c=y_pred)

plt.show()

# print(error_history[0])

# h= np.linspace(0,5,epochs, True)
# v= h *error_history[0] + w_dot[0]

# print(h)

epochs_arr = range(len(error_history))

# plt.plot(h, v, linewidth=3, color='red')
# plt.show()

plt.plot(epochs_arr,error_history,linewidth=3, color='red')

plt.show()