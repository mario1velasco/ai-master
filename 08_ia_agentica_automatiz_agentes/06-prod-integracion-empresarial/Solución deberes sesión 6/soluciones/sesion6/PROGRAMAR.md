# Solución · Programar el informe diario

## 1. Crear el webhook entrante de Slack

Sigue la guía oficial (*Sending messages using incoming webhooks*):
https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/

Copia la URL que te genera y añádela a tu `.env`:

```
INFORME_WEBHOOK_URL=https://hooks.slack.com/services/...
```

Prueba manual (con el servidor de la sesión 6 arrancado y algún ticket enviado):

```bash
python -m soluciones.sesion6.informe_con_canal
```

## 2. Programarlo cada día laborable a las 8:00

**Linux o macOS (cron).** Ejecuta `crontab -e` y añade:

```
0 8 * * 1-5 cd /ruta/a/tema8-agentes && .venv/bin/python -m soluciones.sesion6.informe_con_canal >> datos/informes/cron.log 2>&1
```

**Windows (Programador de tareas).** Desde una terminal:

```
schtasks /Create /TN "InformeLumenShop" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 08:00 /TR "cmd /c cd /d C:\ruta\a\tema8-agentes && .venv\Scripts\python.exe -m soluciones.sesion6.informe_con_canal"
```

**n8n.** Un nodo *Schedule Trigger* con la expresión cron `0 8 * * 1-5`
(documentación: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/)
seguido de un nodo *Execute Command* con el mismo comando que en cron. Si n8n no
corre en la misma máquina que el repositorio, expón el informe como un endpoint
HTTP y llámalo con un nodo *HTTP Request*.

## Por qué la URL va en el .env

Cualquiera que tenga la URL de un webhook entrante puede publicar en el canal. Si
la escribes en el comando, queda a la vista en el historial de la terminal y en
la configuración de la tarea programada.
