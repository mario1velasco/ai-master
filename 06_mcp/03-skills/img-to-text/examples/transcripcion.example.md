<!-- imagen 1: pagina_2.png -->

EBIS Business Techschool

#### Alternativas de instalación

- **macOS (vía Homebrew):** Si prefieres gestionar tus paquetes con Brew:

  Shell

  ```
  brew install uv
  ```

- **Vía pip (Cualquier OS):** Aunque Astral recomienda los instaladores independientes (standalone), si ya tienes Python instalado y prefieres la vía tradicional, puedes usar pip (o pipx para mayor limpieza):

  Shell

  ```
  pip install uv
  ```

#### Verifica tu instalación

Una vez que termine (es posible que necesites reiniciar tu terminal o abrir una nueva pestaña), verifica que uv está listo para usarse ejecutando:

Shell

```
uv --version
```

(Debería devolverte la versión instalada, por ejemplo: uv 0.X.X).

## 1. Entrar en el proyecto

None

```
cd ebis-twitter
```

## 2. Instalar dependencias

None

```
uv sync
```

Este comando lee *pyproject.toml*, crea el entorno virtual y descarga las dependencias.

## 3. Arrancar el proyecto (FastAPI)

Una vez usas en el proyecto el ecosistema UV, basta con ejecutar cualquier cosa que necesites haciendo uso de `uv run`:
