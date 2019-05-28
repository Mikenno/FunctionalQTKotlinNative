import os

import math
import matplotlib.pyplot as plt

lengths = []

for path, dirs, files in os.walk("out"):
    for file in files:
        if file.__contains__(".kt"):
            fullpath = os.path.join(path, file)
            with open(fullpath, 'r') as f:
                for i, l in enumerate(f):
                    pass
                lengths.append(i+1)
print(lengths)
print("Count: " + str(len(lengths)))
print("Average: " + str(sum(lengths)/len(lengths)))

plt.hist(lengths, 50, density=True, facecolor='g', alpha=0.75)
plt.show()
