# CLAUDE.md — `app/` (frontend de UMBRA)

Interfaz web de **UMBRA**, la biblioteca de investigación de la sesión 7 ([`../CLAUDE.md`](../CLAUDE.md) para el
contexto y las precauciones de coste). Es una **SPA de React 19 + Vite 6** en JavaScript (sin TypeScript, sin
tests, sin router, sin librería de estado) que habla con el backend FastAPI de
[`../src/umbra/api/server.py`](../src/umbra/api/server.py) mediante `fetch` a `/api/...`.

> **Las claves (OpenAI, Pinecone) viven solo en Python.** El navegador nunca las recibe: solo envía pregunta,
> modo e historial acotado. No añadir ninguna clave, `.env` ni llamada directa a proveedores en este código.

## Entorno

- Requiere **Node.js 20.19+ o 22.12+** y `npm`. No usa el `.venv` de Python.
- `node_modules/` **no existe** ahora; hay `package-lock.json` (conservarlo: es parte de la entrega).
- Dependencias: `react`, `react-dom` `^19`, `lucide-react` `^0.468` (iconos); dev: `vite` `^6.1`,
  `@vitejs/plugin-react` `^4.3`.

```bash
npm install
npm run build      # genera app/dist  (lo que sirve FastAPI en http://127.0.0.1:8007)
npm run dev        # Vite en http://127.0.0.1:5173; /api se redirige a http://127.0.0.1:8007
npm run preview
```

`npm install` descarga paquetes de Internet y `npm run build` modifica `dist/`: **no ejecutarlos sin que el
usuario lo pida**. Para desarrollar hay que arrancar además el backend (ver `../CLAUDE.md`).

## Estructura

| Ruta | Qué es |
|---|---|
| `index.html` | Entrada de Vite (`lang="es"`, título "UMBRA — Biblioteca de investigación", `#root`). |
| `vite.config.js` | Plugin de React y `server.proxy['/api'] → http://127.0.0.1:8007`. |
| `src/main.jsx` | Monta `<App/>` en `StrictMode` e importa `styles.css`. |
| `src/api.js` | `api(path, options)`: `fetch('/api'+path)` con JSON; si `!ok` lanza `Error(detail)` con el mensaje del backend (o uno genérico). |
| `src/App.jsx` | Cabecera, `<Catalog/>` + `<Conversation/>`, y la **sala de lectura** (`<dialog>`) para ver un documento. Llama a `GET /health` al montar. |
| `src/components/Catalog.jsx` | Catálogo (izquierda): búsqueda **literal local** y 3 temas (Neurología, Inmunología, Salud pública). `GET /catalog?q=`. |
| `src/components/Conversation.jsx` | El librero (derecha): selector de modo, historial, composer, `POST /chat`. |
| `src/components/Response.jsx` | Pinta una respuesta: convierte `[D#]` en botones de cita, lista de fuentes y traza. |
| `src/styles.css` | Todo el CSS en 3 líneas minificadas (tema oscuro "biblioteca"); `@import` de Google Fonts. |
| `public/library.png` | Imagen de fondo (≈ 2 MB); se copia a `dist/`. |
| `dist/` | **Build compilado y versionado** (`index.html`, `assets/index-*.js/css`, `library.png`). Lo sirve el backend con `StaticFiles`. |

## Contrato con la API

| Llamada | Uso en la interfaz |
|---|---|
| `GET /api/health` | Aviso de configuración (`configured`, `message`). Si falla: "Inicia el servidor local…". |
| `GET /api/catalog?q=` | Lista de artículos `{id, title, text}` (≤ 12). `q` ≤ 150 caracteres. |
| `GET /api/documents/{id}` | Texto completo para la sala de lectura. |
| `POST /api/chat` | Cuerpo `{question ≤2000, mode: "standard" \| "tools", history: [{role, content ≤4000}] ≤8}`; respuesta = `Answer` (`text`, `sources[]`, `trace[]`, `usage`, `latency_ms`, `cached`, `warnings[]`). |

Cualquier cambio en el backend (`domain/models.py::Answer`, endpoints o límites) debe reflejarse aquí y en
`Response.jsx`/`Conversation.jsx`, y **recompilar `dist/`**.

## Comportamiento de la interfaz (decisiones que hay que respetar)

- **Modo de conversación:** `standard` (RAG estándar) o `tools` (búsqueda como herramienta). Cambia el flujo, no
  la base documental ni el generador. El selector se desactiva mientras hay una petición en curso.
- **Historial:** se envían los **últimos 8 mensajes** (`messages.slice(-8)`) con el texto truncado a 4.000
  caracteres. La conversación vive **solo en el estado de React** (se pierde al recargar); no hay persistencia.
- **Errores:** si `/chat` falla se **muestra el error, se elimina el mensaje del usuario y se restaura el texto**
  en el cuadro para reintentar. **Nunca se sustituye por una respuesta inventada.** Un 429 significa "otra consulta
  en curso" o cuota del proveedor.
- **Citas:** `Response.jsx` divide el texto con `/(\[D\d+\])/` y convierte cada etiqueta que exista en `sources`
  en un botón que abre la fuente. Solo reconoce **etiquetas sueltas** (`[D1] [D2]`); `[D1, D2]` se ve como texto.
- **Fuentes y traza:** `<details>` con las fuentes (`label`, `title`) y "Ver recorrido de búsqueda" (consulta
  original o "propuesta por el LLM", candidatos densos/léxicos/fusionados, latencia, llamadas y tokens; si
  `cached`, lo indica).
- **Sala de lectura:** `<dialog>` con texto de TREC-COVID, aviso de que puede ser un resumen y no evidencia
  clínica actual, y enlace **externo** que busca el **título** en Google Scholar (no afirma disponer de DOI).
- **Accesibilidad:** roles/`aria-live`/`aria-busy`, etiquetas `aria-label`, foco visible y `prefers-reduced-motion`;
  mantenerlos al modificar.
- **Textos y aviso legal en español**; "Evidencia histórica, no consejo médico. Las consultas usan APIs externas."

## Convenciones y gotchas

- **JSX con estilo compacto** (una línea por bloque, componentes funcionales con hooks, comillas simples); seguir
  el estilo existente al editar en vez de reformatear.
- `styles.css` importa **Google Fonts** (Cormorant Garamond, Inter): el navegador hace una petición externa. Si se
  quiere evitar, hay que alojar las fuentes localmente.
- `dist/` está versionado y **puede quedar desfasado** respecto a `src/`: tras tocar `src/`, recompilar.
- La app no es un servicio público: sin autenticación ni límites por usuario. El backend solo permite **una
  solicitud de chat activa a la vez** y CORS solo para `127.0.0.1:5173`/`localhost:5173`.
