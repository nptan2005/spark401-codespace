import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from matplotlib import animation, rc

# Create a figure of size 8x6 inches, 80 dots per inch
fig = plt.figure(figsize=(12, 6), dpi=80)
plt.close()


axContour = fig.add_subplot(1, 2, 1)
axGraph = fig.add_subplot(1, 2, 2)

# Format coordinate spines of axGraph
axGraph.spines['right'].set_color('none')
axGraph.spines['top'].set_color('none')
axGraph.xaxis.set_ticks_position('bottom')
axGraph.spines['bottom'].set_position(('data', 0))
axGraph.yaxis.set_ticks_position('left')
axGraph.spines['left'].set_position(('data', 0))

# Config limit and ticks on each axis of axGraph
axGraph.set_xlim(-2, 2)
axGraph.set_ylim(-2, 2)
axGraph.set_xticks(np.linspace(-2,2,5,endpoint=True))
axGraph.set_yticks(np.linspace(-2,2,5,endpoint=True))

# Format coordinate spines of axGraph
axContour.spines['right'].set_color('none')
axContour.spines['top'].set_color('none')
axContour.xaxis.set_ticks_position('bottom')
axContour.spines['bottom'].set_position(('data', 0))
axContour.yaxis.set_ticks_position('left')
axContour.spines['left'].set_position(('data', 0))

# Config limit and ticks on each axis of axContour
axContour.set_xlim(-2, 2)
axContour.set_ylim(-2, 2)
axContour.set_xticks(np.linspace(-2,2,5,endpoint=True))
axContour.set_yticks(np.linspace(-2,2,5,endpoint=True))




def animate(i):
  # Each function is determined by a pair of a,b.
  # Generate a pair of a,b with given i
  a = 2-i/4
  b = -a+1

  # draw a single dot in axContour corresponding to 
  # generated pair of a,b
  axContour.plot([a], [b], 'go')

  # draw a corresponding graph of the 
  # function (determined by above pair a,b) in axGraph.
  # First, generage sample value of x
  # Second, calculate values of y corresponding values of x
  X = np.linspace(-2, 2, 256, endpoint=True)
  Y = a*X+b

  # Draw
  axGraph.plot(X, Y, color='green', linewidth=1.0, linestyle='-')
  return ()


def animationInit():
  # Generate sample of x, y in each corresponding range
  sampleX = np.linspace(-2, 2, 256, endpoint=True)
  sampleY = np.linspace(-2, 2, 256, endpoint=True)
  
  # using function np.meshgrid to generate samples of a, b
  A, B = np.meshgrid(sampleX, sampleY)

  # We wanna draw contour corresponding to x=1
  # on axContour. Well, let's assign
  # x=1 and calculate contour level - called z
  x = 1
  Z = A*x + B

  
  # using method contour of axContour to draw our contours
  CS = axContour.contour(A, B, Z, cmap=cm.rainbow)
  axContour.clabel(CS, inline=1, fontsize=10)
  return ()


# Let's generate an animation
anim = animation.FuncAnimation(
    fig=fig, 
    func=animate, 
    init_func=animationInit, 
    frames=18, 
    interval=100, 
    blit=True
)
rc('animation', html='jshtml')
anim


# replace anim by below code to save animation to file .mp4
# anim.save('animation.mp4')