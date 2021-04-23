import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

x = np.array([-0.25, -0.625, -0.125, -1.25, -1.125, -1.25,
     0.875, 1.0, 1.0, 0.5, 1.0, 0.625, -0.25])
y = np.array([1.25, 1.375, 1.5, 1.625, 1.75, 1.875, 1.875,
     1.75, 1.625, 1.5, 1.375, 1.25, 1.25])

# Pad the x and y series so it "wraps around".
# Note that if x and y are numpy arrays, you'll need to
# use np.r_ or np.concatenate instead of addition!
orig_len = len(x)
x = np.concatenate([x[-3:-1], x, x[1:3]])
y = np.concatenate([y[-3:-1], y, y[1:3]])

t = np.arange(len(x))
ti = np.linspace(2, orig_len + 1, 10 * orig_len)

xi = interp1d(t, x, kind='cubic')(ti)
yi = interp1d(t, y, kind='cubic')(ti)

fig, ax = plt.subplots()
ax.plot(xi, yi)
ax.plot(x, y)
ax.margins(0.05)
plt.show()