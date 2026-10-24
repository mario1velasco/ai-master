# Resumen: guía de uv (imágenes) y consulta de oncología (audios)

## Contexto
El material tiene tres fuentes, en este orden: dos imágenes con páginas de una guía titulada «Como usar UV en un proyecto» (`pagina_a.png` y `pagina_b.png`), un audio de unos 9 minutos (`reunion_1.aac`) y otro de algo más de 1 minuto (`reunion_2.aac`), estos dos últimos transcritos automáticamente. Las dos partes no tienen relación entre sí. Las transcripciones de audio tienen errores y no distinguen a los hablantes. Las dos imágenes llevan la cabecera «EBIS Business Techschool», que se repite en cada una y no es contenido.

## Parte 1. Guía «Como usar UV en un proyecto» (imágenes)

### Conceptos clave (imagen 1)
- El archivo `pyproject.toml` es «el estándar moderno en Python para centralizar toda la configuración de un proyecto» (metadatos, dependencias y herramientas de desarrollo), y reemplaza a archivos antiguos como `setup.py` o `requirements.txt`.
- **uv** aprovecha ese estándar y lo trata como su única «fuente de la verdad»: lee directamente el `pyproject.toml` para resolver y descargar el árbol de dependencias «a velocidades extremas», crear entornos virtuales aislados automáticamente y generar un archivo de bloqueo robusto (`uv.lock`).
- El resultado que se describe es un flujo de trabajo unificado, seguro y determinista, sin requerir múltiples herramientas ni configuraciones adicionales.

### Instalación de uv
- **Astral.sh** es la empresa detrás de uv y de Ruff (el popular linter/formateador). Su filosofía: construir herramientas para el ecosistema de Python utilizando Rust para que sean «ridículamente rápidas» (a menudo entre 10 y 100 veces más rápidas que las tradicionales, como pip o virtualenv). No solo busca velocidad, sino unificar el flujo de trabajo del desarrollador.
- Se recomienda instalarlo a nivel de sistema, para usarlo en cualquier directorio sin depender de un entorno de Python previo.

| Sistema | Comando |
|---|---|
| macOS y Linux | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Windows (PowerShell) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| macOS (vía Homebrew) | `brew install uv` |
| Cualquier OS (vía pip) | `pip install uv` |

- Sobre pip: Astral recomienda los instaladores independientes (standalone), pero si ya hay Python instalado y se prefiere la vía tradicional, se puede usar pip (o pipx para mayor limpieza).
- **Verificación:** al terminar puede hacer falta reiniciar el terminal o abrir una nueva pestaña; se ejecuta `uv --version`, que debería devolver la versión instalada, por ejemplo «uv 0.X.X».

### Pasos para trabajar en el proyecto (imagen 2)
1. **Entrar en el proyecto:** `cd ebis-twitter`.
2. **Instalar dependencias:** `uv sync`. Este comando lee *pyproject.toml*, crea el entorno virtual y descarga las dependencias.
3. **Arrancar el proyecto (FastAPI):** una vez usado el ecosistema UV en el proyecto, basta con ejecutar lo que se necesite haciendo uso de `uv run`. La imagen acaba aquí, antes del comando.

## Parte 2. Consulta de oncología (audios)

### Historia clínica
- Se revisa la historia de «anunciación» (así lo transcribe el texto). Tiene 72 años. Residencia: la transcripción dice «Pensilón». Tiene dos hijos, que viven en Madrid y en Santiago de Compostela. Trabajó como autónoma y está jubilada.
- Antecedentes familiares: se menciona a su padre, que murió; «no era tumor, ¿no? No, se le pararon las tripas».
- No es alérgica a ningún medicamento. Sobre el colesterol alto responde «No sé». La sigue neurología y «está tomando 20 gramos» (pasaje confuso). No está operada de nada.
- Fumó muy poco de joven.

### Cómo se llegó al diagnóstico (relato del familiar)
- Tenía un catarro que no se curaba, «como una moto que no arranca». Le dijeron que fuera a la médica de Simancas porque llevaba mucho tiempo así.
- La médica de Simancas la auscultó y la mandó a hacerse unas placas. En ellas se veía el pulmón «muy lleno de líquido».
- La derivaron al hospital: en urgencias sacaron líquido; la subieron a planta y le pusieron «la maleta» para seguir sacando líquido. Intervino la neumóloga.
- Le hicieron un TAC (transcrito «tag»). Intentaron una primera biopsia por dentro para llegar al tumor, pero estaba muy alejado por los conductos normales y no pudieron; le hicieron una biopsia por fuera y cogieron «un trozo bueno del tumor».
- Hace «25 días o así» la neumóloga los citó con los resultados: era cáncer de pulmón. Les dijo que los derivaba y que les llegaría una cita de 7 a 10 días con la oncóloga.
- La familia dice que no les han explicado los resultados del TAC ni lo que cogieron: les dijeron que hicieran las preguntas «para el próximo día».

### Explicación del diagnóstico
- Quien dirige la consulta dice que no hace falta apuntar nada porque lo dará todo por escrito.
- Hay una **lesión en el pulmón** y el **derrame** (el líquido que pincharon). Ese líquido se mandó a analizar y salió **positivo**: había células tumorales dentro.
- Hay además **nódulos satélite**, «chiquititos» y contralaterales, en el otro pulmón, y los **ganglios** de la zona parecían aumentados de tamaño. Todo está a nivel torácico; «no había nada más fuera».
- **No hay opción de operar.** Cuando el tumor sale de su sitio original y va al pulmón contralateral, y hay derrame en el mismo pulmón, se dejarían células tumorales; al estar las células dentro del líquido no se puede quitar el pulmón entero («es inviable»), ni este pulmón y parte del otro, porque no podría respirar.
- **Prueba pendiente:** falta el TAC de la cabeza, que no se ha hecho ni citado. Probablemente se hará una resonancia, que se ve un poco mejor, porque estos tumores «tienen predisposición para irse para arriba»; se hace para descartar.

### Plan de tratamiento
- Como se descarta la intervención, la idea es un tratamiento **por la vena** de dos cosas: una **quimioterapia** y una **inmunoterapia**. El objetivo es reducir la enfermedad o al menos frenarla, para que no dé más problemas ni se vaya a otra zona.
- La paciente es un caso «un poquito particular»: no ha sido fumadora, o lo ha sido de forma muy ocasional. Por eso se analizan posibles mutaciones que expliquen el tumor, ya que generalmente estos tumores salen en personas fumadoras.
- Tiene una **mutación** «un poquito especial», para la que **no hay en España un medicamento aprobado**; se suele poner en **segunda línea** (primero quimioterapia y después ese fármaco). Si con la quimio y la inmunoterapia no fuese bien, se valoraría si hay algún ensayo; eso sería un tratamiento «a posteriori».
- La mutación se le deja apuntada; el texto dice «es una mutación de señas de un gen» (primera transcripción) y «se enojece un genio» (segunda): confuso, no se nombra el gen.
- Sobre la intención: el texto dice que es parar la enfermedad y, a continuación, «es un tratamiento curativo en ese sentido es un tratamiento de control de freno de la enfermedad». La transcripción afirma las dos cosas.
- La quimioterapia y la inmunoterapia «son fármacos» que se ponen por la vena. Aquí termina el primer audio.

### Segundo audio
Repite casi literalmente el pasaje final del primero (mutación sin aprobación en España, segunda línea, ensayo, intención del tratamiento). Variantes de la transcripción: «No del primer ámbito» y «se enojece un genio». No aporta información nueva.

## Datos concretos

| Dato | Valor |
|---|---|
| Edad de la paciente | 72 años |
| Hijos | dos (Madrid y Santiago de Compostela) |
| Hace cuánto dieron el diagnóstico | «25 días o así» |
| Cita con la oncóloga prometida | de 7 a 10 días |
| Tratamiento | quimioterapia más inmunoterapia, por la vena |
| Prueba pendiente | TAC de la cabeza (probablemente resonancia) |
| Velocidad de las herramientas de Astral | «a menudo entre 10 y 100 veces más rápidas» que pip o virtualenv |
| Archivo de bloqueo de uv | `uv.lock` |

## Lo que el material no aclara
- La imagen 2 acaba antes del comando de `uv run`; ese comando figura en una imagen que no se aportó.
- Quién es cada hablante en los audios y quién dirige la consulta.
- Residencia exacta de la paciente («Pensilón»), los «20 gramos» y el gen de la mutación.
- La contradicción entre «tratamiento curativo» y «tratamiento de control» en la misma frase.
