"""
IMPLEMENTACIÓN COMPLETA DEL TRANSFORMER EN NUMPY
Versión educativa paso a paso

Este código muestra EXACTAMENTE cómo funciona un Transformer real
sin dependencias externas complicadas.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

print("\n" + "="*80)
print("TUTORIAL COMPLETO: IMPLEMENTACIÓN DEL TRANSFORMER EN NUMPY")
print("="*80)

# ============================================================================
# UTILIDADES: Softmax y otros
# ============================================================================

def softmax(x, axis=-1):
    """Softmax con estabilidad numérica"""
    x_shifted = x - np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x_shifted)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def layer_norm(x, gamma=None, beta=None, eps=1e-6):
    """Layer Normalization"""
    mean = np.mean(x, axis=-1, keepdims=True)
    var = np.var(x, axis=-1, keepdims=True)
    x_norm = (x - mean) / np.sqrt(var + eps)
    if gamma is not None and beta is not None:
        return gamma * x_norm + beta
    return x_norm


# ============================================================================
# PARTE 1: SCALED DOT-PRODUCT ATTENTION
# ============================================================================

class ScaledDotProductAttention:
    """
    Implementación de Scaled Dot-Product Attention
    
    Fórmula: Attention(Q, K, V) = softmax(QK^T / √d_k) V
    """
    
    def __init__(self):
        self.attention_weights = None
    
    def forward(self, Q, K, V, mask=None):
        """
        Q: (seq_len, d_k)
        K: (seq_len, d_k)
        V: (seq_len, d_v)
        
        Returns: output (seq_len, d_v), attention_weights (seq_len, seq_len)
        """
        
        print("\n[Scaled Dot-Product Attention]")
        
        # Paso 1: Calcular scores = QK^T / √d_k
        d_k = Q.shape[-1]
        scores = np.dot(Q, K.T) / np.sqrt(d_k)
        
        print(f"  Scores shape: {scores.shape}")
        print(f"  Scores (primeros valores):\n{scores}")
        
        # Paso 2: Aplicar mask si existe (para evitar ver posiciones futuras)
        if mask is not None:
            scores = scores + (mask * -1e9)
        
        # Paso 3: Softmax
        attention_weights = softmax(scores, axis=-1)
        self.attention_weights = attention_weights
        
        print(f"  Attention weights (distribución de probabilidad):\n{attention_weights}")
        print(f"  Suma de cada fila (debe ser ~1.0): {attention_weights.sum(axis=-1)}")
        
        # Paso 4: Multiplicar por V
        output = np.dot(attention_weights, V)
        
        print(f"  Output shape: {output.shape}")
        
        return output, attention_weights


# ============================================================================
# PARTE 2: MULTI-HEAD ATTENTION
# ============================================================================

class MultiHeadAttention:
    """
    Multi-Head Attention: h cabezas en paralelo
    """
    
    def __init__(self, d_model, num_heads, seed=42):
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        np.random.seed(seed)
        
        # Matrices de proyección para cada cabeza
        self.W_q = [np.random.randn(d_model, self.d_k) * 0.1 for _ in range(num_heads)]
        self.W_k = [np.random.randn(d_model, self.d_k) * 0.1 for _ in range(num_heads)]
        self.W_v = [np.random.randn(d_model, self.d_k) * 0.1 for _ in range(num_heads)]
        
        # Matriz de proyección final
        self.W_o = np.random.randn(d_model, d_model) * 0.1
        
        # Mecanismo de atención
        self.attention = ScaledDotProductAttention()
        self.head_outputs = []
    
    def forward(self, x, mask=None):
        """
        x: (seq_len, d_model)
        
        Returns: output (seq_len, d_model)
        """
        
        print("\n[Multi-Head Attention]")
        print(f"  d_model: {self.d_model}, num_heads: {self.num_heads}, d_k: {self.d_k}")
        
        self.head_outputs = []
        
        # Para cada cabeza
        for head_idx in range(self.num_heads):
            print(f"\n  --- HEAD {head_idx + 1} ---")
            
            # Proyectar
            Q = np.dot(x, self.W_q[head_idx])  # (seq_len, d_k)
            K = np.dot(x, self.W_k[head_idx])
            V = np.dot(x, self.W_v[head_idx])
            
            # Atención
            head_output, _ = self.attention.forward(Q, K, V, mask)
            self.head_outputs.append(head_output)
            
            print(f"  Head output shape: {head_output.shape}")
        
        # Concatenar outputs
        concatenated = np.concatenate(self.head_outputs, axis=-1)  # (seq_len, d_model)
        
        print(f"\n  Concatenated shape: {concatenated.shape}")
        
        # Proyección final
        output = np.dot(concatenated, self.W_o)  # (seq_len, d_model)
        
        print(f"  Final output shape: {output.shape}")
        
        return output


# ============================================================================
# PARTE 3: FEED-FORWARD NETWORK
# ============================================================================

class FeedForwardNetwork:
    """
    FFN(x) = max(0, xW1 + b1)W2 + b2
    """
    
    def __init__(self, d_model, d_ff, seed=42):
        np.random.seed(seed)
        self.W1 = np.random.randn(d_model, d_ff) * 0.1
        self.b1 = np.zeros(d_ff)
        self.W2 = np.random.randn(d_ff, d_model) * 0.1
        self.b2 = np.zeros(d_model)
    
    def forward(self, x):
        """
        x: (seq_len, d_model)
        Returns: (seq_len, d_model)
        """
        
        print("\n[Feed-Forward Network]")
        
        # Capa 1 + ReLU
        hidden = np.dot(x, self.W1) + self.b1
        print(f"  After linear 1: {hidden.shape}")
        
        hidden = np.maximum(0, hidden)  # ReLU
        print(f"  After ReLU: {hidden.shape}")
        
        # Capa 2
        output = np.dot(hidden, self.W2) + self.b2
        print(f"  Output: {output.shape}")
        
        return output


# ============================================================================
# PARTE 4: ENCODER LAYER
# ============================================================================

class EncoderLayer:
    """
    Uno de los 6 layers del encoder
    
    Estructura:
    1. Self-Attention + Add & Norm (residual)
    2. Feed-Forward + Add & Norm (residual)
    """
    
    def __init__(self, d_model, num_heads, d_ff, seed=42):
        self.mha = MultiHeadAttention(d_model, num_heads, seed)
        self.ffn = FeedForwardNetwork(d_model, d_ff, seed)
    
    def forward(self, x, mask=None):
        """
        x: (seq_len, d_model)
        """
        
        print("\n[Encoder Layer]")
        
        # Sub-layer 1: Attention + Residual + Norm
        print("\n--- Sub-layer 1: Self-Attention ---")
        attn_output = self.mha.forward(x, mask)
        
        # Add: x + attn_output (residual connection)
        x_after_attn = x + attn_output
        # Norm: layer normalization
        x = layer_norm(x_after_attn)
        print(f"  After Add & Norm: {x.shape}")
        
        # Sub-layer 2: Feed-Forward + Residual + Norm
        print("\n--- Sub-layer 2: Feed-Forward ---")
        ffn_output = self.ffn.forward(x)
        
        # Add + Norm
        x_after_ffn = x + ffn_output
        x = layer_norm(x_after_ffn)
        print(f"  After Add & Norm: {x.shape}")
        
        return x


# ============================================================================
# PARTE 5: POSITIONAL ENCODING
# ============================================================================

class PositionalEncoding:
    """
    Positional Encoding con senos y cosenos
    """
    
    def __init__(self, d_model, max_seq_length=512):
        self.d_model = d_model
        self.pe = np.zeros((max_seq_length, d_model))
        
        positions = np.arange(max_seq_length)[:, np.newaxis]
        dimensions = np.arange(d_model)[np.newaxis, :]
        
        # Calcular la división
        # div_term = 10000^(2i/d_model)
        div_term = np.exp(
            (dimensions[0] // 2) * 2 * np.log(10000) / d_model
        )
        
        # Senos en posiciones pares
        self.pe[:, 0::2] = np.sin(positions / 10000 ** (np.arange(0, d_model, 2) / d_model))
        
        # Cosenos en posiciones impares
        if d_model % 2 == 1:
            self.pe[:, 1::2] = np.cos(positions / 10000 ** (np.arange(1, d_model-1, 2) / d_model))
        else:
            self.pe[:, 1::2] = np.cos(positions / 10000 ** (np.arange(1, d_model, 2) / d_model))
    
    def forward(self, x):
        """
        x: (seq_len, d_model)
        Returns: x + positional_encoding
        """
        return x + self.pe[:x.shape[0], :]


# ============================================================================
# PARTE 6: TRANSFORMER COMPLETO
# ============================================================================

class SimpleTransformer:
    """
    Un Transformer simplificado para entender el flujo
    """
    
    def __init__(self, d_model, num_heads, d_ff, num_layers=2):
        self.pos_encoding = PositionalEncoding(d_model)
        self.encoder_layers = [
            EncoderLayer(d_model, num_heads, d_ff, seed=42+i)
            for i in range(num_layers)
        ]
    
    def forward(self, x, mask=None):
        """
        x: (seq_len, d_model)
        """
        
        print("\n[Transformer Forward Pass]")
        
        # Paso 1: Positional Encoding
        print("\n--- Positional Encoding ---")
        x = self.pos_encoding.forward(x)
        print(f"  After PE: {x.shape}")
        
        # Paso 2: Encoder layers
        for i, layer in enumerate(self.encoder_layers):
            print(f"\n--- Encoder Layer {i+1}/{len(self.encoder_layers)} ---")
            x = layer.forward(x, mask)
        
        return x


# ============================================================================
# DEMOSTRACIÓN: EJEMPLO COMPLETO
# ============================================================================

print("\n" + "="*80)
print("EJEMPLO 1: FLUJO COMPLETO")
print("="*80)

# Parámetros pequeños para debug
d_model = 16
num_heads = 2
d_ff = 32
seq_length = 4
num_layers = 1

print(f"\nConfiguración:")
print(f"  d_model: {d_model}")
print(f"  num_heads: {num_heads}")
print(f"  d_ff: {d_ff}")
print(f"  seq_length: {seq_length}")
print(f"  num_layers: {num_layers}")

# Entrada (palabras codificadas)
print(f"\nCreando entrada de tamaño ({seq_length}, {d_model})")
np.random.seed(42)
x = np.random.randn(seq_length, d_model) * 0.1

print(f"Entrada:")
print(x)

# Transformer
transformer = SimpleTransformer(d_model, num_heads, d_ff, num_layers)
output = transformer.forward(x)

print(f"\n" + "="*80)
print("SALIDA FINAL")
print("="*80)
print(f"Output shape: {output.shape}")
print(f"Output (primeras 5 dimensiones):\n{output[:, :5]}")


# ============================================================================
# EJEMPLO 2: VISUALIZAR PATRONES DE ATENCIÓN
# ============================================================================

print("\n" + "="*80)
print("EJEMPLO 2: VISUALIZAR PATRONES DE ATENCIÓN")
print("="*80)

# Crear un ejemplo más interesante
np.random.seed(123)
seq_length = 6
d_model = 8
num_heads = 2

# Embeddings de ejemplo
x_viz = np.random.randn(seq_length, d_model) * 0.1

# Multi-head attention
mha_viz = MultiHeadAttention(d_model, num_heads, seed=123)
output_viz = mha_viz.forward(x_viz)

# Obtener pesos de una cabeza
print("\nPesos de atención de cada cabeza:")
for head_idx in range(num_heads):
    print(f"\nHead {head_idx + 1}:")
    print(mha_viz.head_outputs[head_idx].shape)

# Visualizar
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

palabras = ["The", "cat", "is", "sleeping", "on", "mat"]

# Para visualizar, necesitamos las matrices de atención
# Las reconstruimos
attention_layer = ScaledDotProductAttention()

# Head 1
Q1 = np.dot(x_viz, mha_viz.W_q[0])
K1 = np.dot(x_viz, mha_viz.W_k[0])
V1 = np.dot(x_viz, mha_viz.W_v[0])
_, attn_weights_1 = attention_layer.forward(Q1, K1, V1)

# Gráfico 1
ax1 = axes[0]
im1 = ax1.imshow(attn_weights_1, cmap='viridis', aspect='auto')
ax1.set_xticks(range(len(palabras)))
ax1.set_yticks(range(len(palabras)))
ax1.set_xticklabels(palabras, rotation=45)
ax1.set_yticklabels(palabras)
ax1.set_xlabel('Keys (A qué se atiende)')
ax1.set_ylabel('Queries (Qué atiende)')
ax1.set_title('Head 1 - Matriz de Atención')
plt.colorbar(im1, ax=ax1)

# Head 2
Q2 = np.dot(x_viz, mha_viz.W_q[1])
K2 = np.dot(x_viz, mha_viz.W_k[1])
V2 = np.dot(x_viz, mha_viz.W_v[1])
_, attn_weights_2 = attention_layer.forward(Q2, K2, V2)

ax2 = axes[1]
im2 = ax2.imshow(attn_weights_2, cmap='viridis', aspect='auto')
ax2.set_xticks(range(len(palabras)))
ax2.set_yticks(range(len(palabras)))
ax2.set_xticklabels(palabras, rotation=45)
ax2.set_yticklabels(palabras)
ax2.set_xlabel('Keys (A qué se atiende)')
ax2.set_ylabel('Queries (Qué atiende)')
ax2.set_title('Head 2 - Matriz de Atención')
plt.colorbar(im2, ax=ax2)

plt.tight_layout()
plt.savefig('/home/claude/transformer_attention_heads.png', dpi=150, bbox_inches='tight')
print("\n✓ Visualización guardada: transformer_attention_heads.png")
plt.close()


# ============================================================================
# EJEMPLO 3: COMPARAR PARÁMETROS CON EL PAPER
# ============================================================================

print("\n" + "="*80)
print("COMPARACIÓN: PARÁMETROS DEL TRANSFORMER")
print("="*80)

def count_transformer_params(d_model, num_heads, d_ff, num_layers, vocab_size):
    """Contar parámetros totales del Transformer"""
    
    # Embedding
    embedding_params = vocab_size * d_model
    
    # Positional Encoding (sin parámetros)
    pe_params = 0
    
    # Por layer
    params_per_layer = 0
    
    # Multi-head attention
    mha_params = (
        3 * d_model * d_model +  # W_q, W_k, W_v
        d_model * d_model        # W_o
    )
    
    # Feed-forward
    ffn_params = (
        d_model * d_ff +         # W1
        d_ff +                   # b1
        d_ff * d_model +         # W2
        d_model                  # b2
    )
    
    # Layer norm
    ln_params = 2 * d_model * 2  # 2 layer norms, cada una con gamma y beta
    
    params_per_layer = mha_params + ffn_params + ln_params
    
    total_encoder = params_per_layer * num_layers
    total = embedding_params + total_encoder
    
    return {
        'embedding': embedding_params,
        'per_layer': params_per_layer,
        'total_encoder': total_encoder,
        'total': total
    }

# Configuración del paper original
print("\nTransformer Base (del paper de 2017):")
config_base = count_transformer_params(512, 8, 2048, 6, 37000)
for key, val in config_base.items():
    print(f"  {key:20}: {val:>15,}")

print("\nNuestro ejemplo simplificado:")
config_simple = count_transformer_params(16, 2, 32, 1, 1000)
for key, val in config_simple.items():
    print(f"  {key:20}: {val:>15,}")


# ============================================================================
# RESUMEN EDUCATIVO
# ============================================================================

print("\n" + "="*80)
print("RESUMEN: CÓMO FUNCIONA EL TRANSFORMER")
print("="*80)

summary_text = """
1. EMBEDDINGS & POSITIONAL ENCODING
   - Las palabras se convierten en vectores (embeddings)
   - Se suma información de posición (senos/cosenos)

2. ENCODER (6 layers idénticos)
   Cada layer tiene:
   
   a) SELF-ATTENTION (Multi-Head)
      - Cada palabra "mira" todas las demás
      - 8 cabezas miran diferentes aspectos
      - Resultado: vector que combina información relevante
      - Conexión residual: x + attention(x)
      - Normalización: layer_norm(x)
   
   b) FEED-FORWARD
      - Red neuronal simple (2 capas)
      - Procesa cada posición independientemente
      - Conexión residual: x + ffn(x)
      - Normalización: layer_norm(x)

3. DECODER (similar, pero:)
   - Attention es "masked" (no ve palabras futuras)
   - Hay atención cruzada (encoder-decoder)

4. OUTPUT
   - Capa lineal + softmax
   - Predicción de siguiente palabra

FLUJO MATEMÁTICO:
Input → Embedding → PE → Encoder (x6) → Output Layer → Predicción

SCALED DOT-PRODUCT ATTENTION:
Attention(Q, K, V) = softmax( Q·K^T / √d_k ) · V

Esto es:
1. Comparar Q con todos los K (producto punto)
2. Escalar para estabilidad
3. Convertir a probabilidades (softmax)
4. Ponderar los V por esas probabilidades

MULTI-HEAD ATTENTION (8 cabezas):
- Hacer lo anterior 8 veces en paralelo
- Cada una con proyecciones diferentes
- Concatenar resultados
- Proyección final

RESULTADO:
El modelo puede aprender qué palabras son importantes para cada posición.
Esto lo hace mucho mejor que RNNs que procesan secuencialmente.

IMPACTO:
- 2017: Paper publicado
- 2018: BERT, GPT
- 2020: GPT-3
- 2022: ChatGPT
- Hoy: Todos los modelos modernos usan Transformer
"""

print(summary_text)

print("\n" + "="*80)
print("✓ TUTORIAL COMPLETADO")
print("="*80)
