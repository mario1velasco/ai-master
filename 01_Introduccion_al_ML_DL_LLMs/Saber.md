one hot encoding

byte pair encoding (BPE)

Cross-entropy

aplanamiento

Modelos secuenciales (Viejos antes de 2017)
RNN 
LSTM

BackPropagation !!


Convoluccion
Una convolución es una operación matemática que aplica un filtro pequeño (kernel) a través de una imagen (o dato) para extraer características locales (patrones, bordes, texturas).

Diferencia: MLP vs CNN 
Ahora que entiendes convolución, la diferencia es clara:
AspectoMLPCNNConexionesCada neurona conectada a TODAS las anterioresCada neurona conectada a región LOCALParámetrosMuchos (W×H×H)Pocos (kernel pequeño)Invariancia espacialNo entiende distanciaEntiende posiciónIdeal paraDatos sin estructura espacialImágenes, series de tiempoEjemploDatos tabulares, texto planoVisión por computadora



Embedding
Un embedding es una representación numérica (vector) de un texto que captura su significado semántico. Transforma palabras o documentos en números que una máquina puede comparar.


PCA
Proyectar a 2 dimensiones

Single head of Attention (Criatura azul)
* Calcula embedding E1, E2 ... Multiplica la matriz embeding * token. Ei = Matriz Embding * Token
* Matriz Query (12288 x 128) Qi = Wq (Matriz determinada, ya se sabe) * Ei -> Es el que hace la pregunta. Algun adjetivo delante de mi?
* Matriz Clave (12288 x 128) Ki = Wj (Matriz determinada, ya se sabe) * Ei -> Es el que responde. Yo soy adjetivo!
    Lo que hace Qi y Ki se crean vectores y los que esten en la misma direccion y mas juntos pues son los que tienen mas relación. Los Ki se alinean con la constulta Qi.
    Se multiplican Qi y Ki y se ve en cada casilla que tan juntos estan
    Luegos cuando tienes calculada la columna se hace softmax para que la suma de 1
* Enmascaramiento: Las palabras posteriores no pueden interferir en las anteriores porque podrian revelar la respuesta.
    Las casillas anteriores se ponen a -infnito para que el softmax de 1. Se hace esto para que el GPT no haga adivinanzas de las palabras de antes de la frase
* Matriz de valores Wv (12288 x 12288). Vi = Wv (Matriz determinada, ya se sabe) * Ei
    Formada por 2 matrices. Value↓ (128x12288) y Value→ (12288x128) 
    Actualizar los embeddigns pasan informacion las palabras relevantes a la que esta calculando. El adjetivo que esta cerca del nombre queremos que apunten modifique al nombre para que apunte al embedding que representan juntos (criatura de mueva criatura azul)
* Ahora tenemos AEi = (Softmax(Qi * Ki))*Vi --> A criatura se le suma peluda y azul
* Al final re finamos: E'i = Ei + AEi  Sumamos el embedding al AEi para conseguir un embedding' E'



Mask Multi Head Attention
Mask porque solo podemos saber las palabras anteriores. Le entrenamos con las palabras anteriores. Truncamos el token futuro
Se corren en paralelo cada Head. Tiene 96 Heads (Cabezales de atencion). Tiene 96 distintos Wq Wj Wv
Cada capa es una matriz de GPT con valores 10000x10000 ya creados Q K V
GPT tiene 96 capas, que hace cada capa?
Al final despues de pasar por todas la capas se coje el ultimo vector de la matriz resultante se multiplica ppor Wu se hace softmax y te sale que palabra es
Luego tiene capas

Que tiene predefinido GPT3:
* Embedding Matrix -> Matriz de 50257 tokens. Lo que vale cada token (12,288 coordenadas). Hace el encaje inicial. La dimension siempre la misma para cada token
    Con esta puedes hacer E(padre) - E(Madre) + E(hijo) = E(hija). NO aportas entorno
* Tamaño de contexto: Lo que puede predecir a la vez. Una matriz de 2048 columnas por 12288 dimensiones
* Unembedding matrix (Wu): 50257 filas que representa cada token y 12288 columnas cada fila. 
    Coges la ultima columna y multiplicas por Wu para saber la "probabilidad" del token que tiene que salir ()= y luego hasces softmax (0-1 y suma total = 1) y te da que palabra deberia de aparecer
* 



Determinista y no determinista. Los LLMs son no deterinistas (son aleatorios). Normalmente ML son deterministas.
Greedy decoding (Determinista) / Sampling (No determinista)
Se da el no deterministo con:
* Temperatura: Factor multiplicardor al softmax va de 0 a 1.5. 
        Greeedy: temperatura = 0
* Top-K. Los mas probables resto 0 
* Top-P. Todos lo que tengan mejor prob
* Normal temp=0.7, top_p=0.9 y top-k nada


Prompt: Mensajes con tres role. System (Prompt) / User (Lo que escribes) / Assistant (el historial)
Zero-shot vs Few-shot: Añades ejemplos
Chain of thought. 

Fine-tuning. Entrenar un modelo (chino normalmente) para que se aprenda mi negocio