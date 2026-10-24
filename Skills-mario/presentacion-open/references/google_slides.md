# Solicitudes de Google Slides

Esta skill genera y edita archivos PowerPoint `.pptx` locales. `python-pptx` no proporciona autenticación, acceso a Google Drive ni conversión/importación controlada en Google Slides.

- Si el usuario solo necesita un archivo que pueda importar, entrega el `.pptx` y aclara que debe importarlo en Google Slides; la conversión puede cambiar tipografía, gráficos, recortes, notas o animaciones.
- No afirmes que el deck fue subido, convertido o validado en Google Slides desde estos scripts.
- Si el entorno ofrece un conector explícito de Google Slides y el usuario pide operar directamente en ese servicio, usa el flujo autorizado de ese conector. Esta skill abierta sigue sirviendo para redactar, maquetar y validar el PPTX local.
- Mantén el `.pptx` original como artefacto de respaldo y revisa visualmente la presentación ya importada cuando la fidelidad de Google Slides sea requisito de entrega.
