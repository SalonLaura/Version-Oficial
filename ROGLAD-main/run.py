"""import os
activate = "c:/Users/Economico/Desktop/Bussiness/env/Scripts/Activate.ps1"
os.system(activate)
runserver = "python manage.py runserver"
os.system(runserver)
"""

import subprocess

# Define el comando para ejecutar el servidor de Django
comando = f"python ./manage.py runserver 0.0.0.0:8000"

## Ejecuta el comando en la terminal
subprocess.call(comando, shell=True)