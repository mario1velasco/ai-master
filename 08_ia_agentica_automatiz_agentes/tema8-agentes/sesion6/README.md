# Sesión 6 · Agentes en producción e integración empresarial

## Demos

| Archivo | Qué muestra |
|---|---|
| `agente_tickets.py` | El agente que integramos: herramientas de lectura, reembolso con permisos limitados en el código y aprobación humana |
| `servidor_webhook.py` | Tres formas de llamarlo desde otros sistemas: webhook asíncrono, API síncrona y consulta de tickets, más el panel de aprobaciones |
| `enviar_ticket.py` | Simula el helpdesk, el chat de la web y al supervisor |
| `informe_programado.py` | Un agente que se ejecuta solo cada mañana, escribe el informe de soporte y lo publica en un canal |

Flujo empresarial (dos terminales):

```bash
# Terminal 1
uvicorn sesion6.servidor_webhook:app --reload
# Terminal 2
python -m sesion6.enviar_ticket normal
python -m sesion6.enviar_ticket reembolso
python -m sesion6.enviar_ticket aprobar T-2
python -m sesion6.enviar_ticket consulta "¿Tenéis protector solar?"
```

Informe programado (con el servidor arrancado y algún ticket enviado):

```bash
python -m sesion6.informe_programado
python -m sesion6.informe_programado --enviar-a https://hooks.slack.com/services/...
```

Para que se ejecute solo, prográmalo con cron, el Programador de tareas de Windows
o un flujo de n8n (Schedule Trigger + Execute Command). Los comandos exactos están
al principio de `informe_programado.py`.

La calidad, los guardarraíles y la defensa frente a manipulaciones se tratan en
profundidad en el tema siguiente.

## Deberes finales

**Ejercicio guiado · Programa el informe y publícalo en un canal.**
1. Crea un webhook entrante de Slack siguiendo la guía oficial:
   https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/
   (si no usas Slack, sirve cualquier canal con webhooks entrantes, como Teams).
2. Haz que el informe lea la URL del canal de una variable `INFORME_WEBHOOK_URL`
   del archivo `.env`, en lugar de escribirla en el comando.
3. Prográmalo cada día laborable a las 8:00 con cron, con el Programador de tareas
   de Windows o con un nodo Schedule Trigger de n8n:
   https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/

**Nivel base · Tu propio caso.** Adapta el agente a un proceso de tu empresa o
negocio: sustituye `comun/tienda.py` por datos de tu dominio, define tus
herramientas clasificadas por riesgo y decide qué acciones requieren aprobación
humana. Este deber no tiene solución única.

**Reto · Intégralo en un flujo.** Conecta tu agente a un proceso real o simulado
de tu empresa: un disparador (webhook, formulario, correo o tarea programada), un
punto de aprobación humana en las acciones de escritura y un plan para cuando el
agente falle. Si usas n8n, Make o Power Automate, el agente puede ser un paso más
del flujo llamando a su API.
