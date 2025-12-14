import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from matplotlib import animation, rc

# ==============================================================================
# Defines convenient functioins
# ==============================================================================

def formatCoordinateSpines(ax):
  ax.spines['right'].set_color('none')
  ax.spines['top'].set_color('none')
  ax.xaxis.set_ticks_position('bottom')
  ax.spines['bottom'].set_position(('data', 0))
  ax.yaxis.set_ticks_position('left')
  ax.spines['left'].set_position(('data', 0))


def formatCoordinateLimit(ax, x_range, y_range):
  ax.set_xlim(x_range[0], x_range[1])
  ax.set_ylim(x_range[0], x_range[1])
  ax.set_xticks(np.linspace(
      x_range[0],
      x_range[1],
      -x_range[0]+x_range[1]+1,
      endpoint=True
  ))
  ax.set_yticks(np.linspace(
      y_range[0],
      y_range[1],
      -y_range[0]+y_range[1]+1,
      endpoint=True
  ))


def drawGraphOfASingleFunction(ax, x_range, funcObj, color="red", linewidth=1.0, linestyle="-"):
  X = np.linspace(x_range[0], x_range[1], 256, endpoint=True)
  Y = funcObj.calculateY(X)
  ax.plot(X, Y, color, linewidth, linestyle)


def drawContourInFunctionSpace(ax, x_range, y_range, funcObj):
  sampleX = np.linspace(x_range[0], x_range[1], 256, endpoint=True)
  sampleY = np.linspace(y_range[0], y_range[1], 256, endpoint=True)
  A, B = np.meshgrid(sampleX, sampleY)
  Z = funcObj.calculateContourLevel(A, B)
  CS = axContour.contour(A, B, Z, cmap=cm.rainbow)
  ax.clabel(CS, inline=1, fontsize=10)


def drawDot(ax, horizontal, vertical, style):
  ax.plot([horizontal], [vertical], style)



# ==============================================================================
# End of utilities functions
# ==============================================================================


class LinearFunc:
  # this allow you to define a function object with 2 required methods:
  # - calculateY
  # - calculateContourLevel
  # These 2 methods will be invoked by functions: drawGraphOfASingleFunction, drawContourInFunctionSpace
  def __init__(self, A=None, X=None, B=None):
    self.X = X
    self.A = A
    self.B = B

  # yes, you define your own linear function f(x) right here
  def __equation(self, A, X, B):
    return A*X+B
  
  # Value of A, B are fixxed while calculating values of Y by X
  # Value of X is sampled by function np.linspace before
  def calculateY(self, X):
    return self.__equation(self.A, X, self.B)

  # Value of X is fixxed while calculating countour level.
  # Value of A, B are sampled by function np.linspace before
  def calculateContourLevel(self, A, B):
    return self.__equation(A, self.X, B)


x_range = [-2, 2]
y_range = [-2, 2]
a_range = [-2, 2]
b_range = [-2, 2]

# Create a figure of size 8x6 inches, 80 dots per inch
fig = plt.figure(figsize=(12, 6), dpi=80)
plt.close()

axContour = fig.add_subplot(1, 2, 1)
axGraph = fig.add_subplot(1, 2, 2)

formatCoordinateSpines(axGraph)
formatCoordinateSpines(axContour)
formatCoordinateLimit(axGraph, x_range, y_range)
formatCoordinateLimit(axContour, a_range, b_range)


def animationInit():
  # drawContourInFunctionSpace(axContour, x_range, y_range, LinearFunc(X=1))
  return ()


def animate(i):
  A = 2-i/4
  B = -A+1
  drawDot(axContour, A, B, "go")
  drawGraphOfASingleFunction(axGraph, x_range, LinearFunc(A=A, B=B), color="green")
  return ()


anim = animation.FuncAnimation(
    fig=fig, func=animate, init_func=animationInit, 
    frames=18, interval=100, blit=True)
rc('animation', html='jshtml')
anim

# replace anim by below code to save animation to file .mp4
# anim.save('animation.mp4')