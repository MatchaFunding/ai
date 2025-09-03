IA – Setup local con Python, venv y FastAPI
==================================================

## Entorno Local

Windows (PowerShell):
```
  # Crear y activar venv:
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
```
Windows (cmd):
```
  py -3.11 -m venv .venv
  .venv\Scripts\activate.bat
```
Windows (Git Bash):
```
  py -3.11 -m venv .venv
  source .venv/Scripts/activate
```


## Instalar dependencias

(Con el entorno virtual ACTIVO)
```
  pip install --upgrade pip
  pip install -r requirements.txt
```
Si se necesita agregar un paquete nuevo:
```
  pip install <paquete>
  pip freeze > requirements.txt   # Guarda la versión exacta para el equipo
```

## Levantar el servidor de desarrollo
```
  uvicorn app.main:app --reload --port 8080
```

## Estructura del proyecto 
```
  ia_service/
    app/
      api/
      core/
      models/
      services/
      utils/
      main.py
    tests/
    requirements.txt
    README.txt
```

## Sobre los tests
Con el entorno virtual activado:
```
pytest -q
```


## Notas útiles

- Para desactivar el entorno virtual:
```
  deactivate
```



## Levantar docker con QDrant

'''
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
'''