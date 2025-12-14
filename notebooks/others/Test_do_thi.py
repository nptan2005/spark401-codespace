from matplotlib import pyplot as plt
import numpy as np

xm = np.arange(-2, 11, 0.025)
ym = np.arange(-3, 10, 0.025)
xx, yy = np.meshgrid(xm, ym)

print(np.ones((1, xx.size)).shape)
xx1 = xx.ravel().reshape(1, xx.size)
yy1 = yy.ravel().reshape(1, yy.size)

# print(xx.shape, yy.shape)
XX = np.concatenate((np.ones((1, xx.size)), xx1, yy1), axis = 0)

YY = logreg.predict(XX.T)

print(YY.shape)

YY = YY.reshape(520,520)

plt.scatter(X_test[:,1], X_test[:,2], c=y_pred, s=10)

plt.contourf(xm,ym,YY, alpha = 0.1)
plt.show()