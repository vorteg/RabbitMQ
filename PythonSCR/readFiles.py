import os
from os.path import isfile, join

path= r'/home/vic/Documents/RabbitMQ/PythonSCR/Jsons'

content = os.listdir(path)


files = [name for name in content if isfile(join(path, name))]

print('files:')
print(files)
