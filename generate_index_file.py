import struct

file = open('files.index', 'wb')

# header
file.write(b'KS INDEX')
file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

# add classes 3979, 4397, 6605, 6624 with correct offsets
file.write(struct.pack('I', 3979) + struct.pack('I', 56))
file.write(struct.pack('I', 4397) + struct.pack('I', 80))
file.write(struct.pack('I', 6605) + struct.pack('I', 112))
file.write(struct.pack('I', 6624) + struct.pack('I', 144))
file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

# add file ids to the first class
# road, route
file.write(struct.pack('I', 7) + struct.pack('f', 0.7923))
file.write(struct.pack('I', 5) + struct.pack('f', 0.063))
file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

# street
file.write(struct.pack('I', 1) + struct.pack('f', 0.632))
file.write(struct.pack('I', 8) + struct.pack('f', 0.54012))
file.write(struct.pack('I', 9) + struct.pack('f', 0.35329))
file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

# tree
file.write(struct.pack('I', 4) + struct.pack('f', 0.75))
file.write(struct.pack('I', 5) + struct.pack('f', 0.37))
file.write(struct.pack('I', 6) + struct.pack('f', 0.21))
file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

# sand
file.write(struct.pack('I', 2) + struct.pack('f', 0.80172))
file.write(struct.pack('I', 3) + struct.pack('f', 0.345))
file.write(struct.pack('I', 7) + struct.pack('f', 0.1945))
file.write(b'\xff\xff\xff\xff\xff\xff\xff\xff')

file.close()