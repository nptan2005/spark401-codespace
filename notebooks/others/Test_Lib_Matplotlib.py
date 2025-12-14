import numpy as np
import matplotlib.pyplot as plt

# plt.plot(2, 3,'bo')
# plt.plot(2, 3,'r+')
# plt.plot(2, 3, 'go--', linewidth=2, markersize=12)
# plt.plot(2, 3, color='green', marker='o', linestyle='dashed',linewidth=2, markersize=12)
plt.plot([1,2,3], [1,2,3], 'go-', label='line 1', linewidth=2)
plt.plot([1,2,3], [1,4,9], 'rs',  label='line 2')
plt.show()  

