import sys

# Ruta de tu proyecto en PythonAnywhere
path = '/home/Gabrielbricefer/cancionero_iglesia'
if path not in sys.path:
    sys.path.append(path)

from app import app as application