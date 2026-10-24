"""
Implementación de Scaled Dot-Product Attention desde cero
Este código muestra exactamente cómo funciona matemáticamente
"""

import numpy as np
import matplotlib.pyplot as plt

# ============================================================================
# PASO 1: Implementación Manual (solo NumPy)
# ============================================================================

def scaled_dot_product_attention_manual(Q, K, V):
    """
    Implementación manual de Scaled Dot-Product Attention
    
    Args:
        Q: Query matrix (n_queries, d_k)
        K: Key matrix (n_keys, d_k)
        V: Value matrix (n_keys, d_v)
    
    Returns:
        output: Resultado de la atención (n_queries, d_v)
        attention_weights: Pesos de atención (n_queries, n_keys)
    """
    
    # Paso 1: Calcular el producto punto QK^T
    print("\n=== PASO 1: Producto Punto (QK^T) ===")
    scores = np.dot(Q, K.T)  # (n_queries, n_keys)
    print(f"Forma de scores: {scores.shape}")
    print(f"Scores (antes de escalar):\n{scores}\n")
    
    # Paso 2: Escalar por sqrt(d_k)
    print("=== PASO 2: Escalado (/ √d_k) ===")
    d_k = Q.shape[-1]  # Dimensión de las keys
    sqrt_d_k = np.sqrt(d_k)
    print(f"d_k = {d_k}")
    print(f"√d_k = {sqrt_d_k}")
    
    scaled_scores = scores / sqrt_d_k
    print(f"Scores (después de escalar):\n{scaled_scores}\n")
    
    # Paso 3: Aplicar softmax
    print("=== PASO 3: Softmax ===")
    
    # Truco numérico: restar el máximo para evitar overflow
    scaled_scores_shifted = scaled_scores - np.max(scaled_scores, axis=-1, keepdims=True)
    
    # Calcular exponencial
    exp_scores = np.exp(scaled_scores_shifted)
    print(f"Exponencial de scores:\n{exp_scores}\n")
    
    # Normalizar para obtener probabilidades
    attention_weights = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)
    print(f"Pesos de atención (después de softmax):\n{attention_weights}")
    print(f"Suma de pesos por fila (debe ser 1.0):\n{np.sum(attention_weights, axis=-1)}\n")
    
    # Paso 4: Multiplicar por V (Values)
    print("=== PASO 4: Multiplicar por Values (V) ===")
    output = np.dot(attention_weights, V)
    print(f"Salida de atención:\n{output}\n")
    
    return output, attention_weights


def scaled_dot_product_attention_vectorized(Q, K, V):
    """
    Versión vectorizada (más eficiente) - solo la función final
    """
    d_k = Q.shape[-1]
    scores = np.dot(Q, K.T) / np.sqrt(d_k)
    
    # Softmax con truco numérico
    scores_shifted = scores - np.max(scores, axis=-1, keepdims=True)
    attention_weights = np.exp(scores_shifted) / np.sum(np.exp(scores_shifted), axis=-1, keepdims=True)
    
    output = np.dot(attention_weights, V)
    return output, attention_weights


# ============================================================================
# EJEMPLO 1: Atención Simple (Una palabra con todas las demás)
# ============================================================================

print("\n" + "="*70)
print("EJEMPLO 1: ATENCIÓN SIMPLE")
print("="*70)

# Imagina que tienes una frase con 4 palabras
# y cada palabra tiene una representación de 3 dimensiones

Q = np.array([[1.0, 0.5, -0.3]])  # "es" - Query (1 palabra)
K = np.array([
    [0.2, 0.1, -0.4],   # "El"
    [0.9, 0.2, 0.5],    # "gato"
    [0.3, -0.5, 0.2],   # "está"
    [0.6, 0.4, 0.7]     # "cómoda"
])  # Keys (4 palabras)

V = np.array([
    [0.1, 0.2, 0.3],     # Value de "El"
    [0.8, 0.4, 0.6],     # Value de "gato"
    [0.3, 0.1, 0.2],     # Value de "está"
    [0.7, 0.5, 0.9]      # Value de "cómoda"
])  # Values (4 palabras)

output, attention_weights = scaled_dot_product_attention_manual(Q, K, V)

print("=== INTERPRETACIÓN ===")
print("Atención por palabra:")
palabras = ["El", "gato", "está", "cómoda"]
for i, palabra in enumerate(palabras):
    print(f"  {palabra:10} → {attention_weights[0, i]:.1%}")


# ============================================================================
# EJEMPLO 2: Multi-Head Attention (Simulación)
# ============================================================================

print("\n" + "="*70)
print("EJEMPLO 2: MULTI-HEAD ATTENTION (2 heads)")
print("="*70)

# Simulemos 2 cabezas de atención
np.random.seed(42)

# Dimensiones
seq_length = 4  # Número de palabras
d_model = 64    # Dimensión total (como en el paper)
num_heads = 2   # Número de cabezas
d_k = d_model // num_heads  # 32

print(f"\nConfiguración:")
print(f"  Número de palabras: {seq_length}")
print(f"  Dimensión total (d_model): {d_model}")
print(f"  Número de cabezas: {num_heads}")
print(f"  Dimensión por cabeza (d_k): {d_k}")

# Simular embeddings de entrada (ya procesados)
X = np.random.randn(seq_length, d_model) * 0.1  # 4 palabras, 64 dimensiones

print(f"\nEmbeddings de entrada (primeras 5 valores de cada palabra):")
palabras = ["El", "gato", "está", "cómoda"]
for i, palabra in enumerate(palabras):
    print(f"  {palabra:10} → {X[i, :5]}")

# Proyecciones lineales para cada cabeza
# En un modelo real, estas serían pesos aprendibles
W_q1 = np.random.randn(d_model, d_k)  # 64x32
W_k1 = np.random.randn(d_model, d_k)
W_v1 = np.random.randn(d_model, d_k)

W_q2 = np.random.randn(d_model, d_k)  # 64x32
W_k2 = np.random.randn(d_model, d_k)
W_v2 = np.random.randn(d_model, d_k)

# HEAD 1
print("\n--- HEAD 1 ---")
Q1 = np.dot(X, W_q1)
K1 = np.dot(X, W_k1)
V1 = np.dot(X, W_v1)
head1_output, head1_weights = scaled_dot_product_attention_vectorized(Q1, K1, V1)
print(f"Output shape: {head1_output.shape}")

# HEAD 2
print("\n--- HEAD 2 ---")
Q2 = np.dot(X, W_q2)
K2 = np.dot(X, W_k2)
V2 = np.dot(X, W_v2)
head2_output, head2_weights = scaled_dot_product_attention_vectorized(Q2, K2, V2)
print(f"Output shape: {head2_output.shape}")

# Concatenar outputs
multi_head_output = np.concatenate([head1_output, head2_output], axis=-1)
print(f"\nOutput concatenado: {multi_head_output.shape}")  # Debe ser (4, 64)

# Proyección final
W_o = np.random.randn(d_model, d_model)
final_output = np.dot(multi_head_output, W_o)
print(f"Output final: {final_output.shape}")

print("\n=== ATENCIÓN EN HEAD 1 ===")
print("Pesos de atención:")
for i, palabra in enumerate(palabras):
    print(f"  {palabra:10} → {head1_weights[0, :]}")  # Primera palabra


# ============================================================================
# EJEMPLO 3: Visualización de Atención
# ============================================================================

print("\n" + "="*70)
print("EJEMPLO 3: VISUALIZACIÓN DE ATENCIÓN")
print("="*70)

# Crear una matriz de atención más clara
np.random.seed(123)
seq_length = 6
d_k = 8

# Embeddings
embeddings = np.random.randn(seq_length, 64)
W_q = np.random.randn(64, d_k)
W_k = np.random.randn(64, d_k)
W_v = np.random.randn(64, d_k)

Q = np.dot(embeddings, W_q)
K = np.dot(embeddings, W_k)
V = np.dot(embeddings, W_v)

_, attention_matrix = scaled_dot_product_attention_vectorized(Q, K, V)

palabras_test = ["The", "cat", "is", "sleeping", "on", "mat"]

print(f"\nMatriz de atención (cada fila suma a 1.0):")
print(f"\nPalabra → Atención a:")
for i, palabra in enumerate(palabras_test):
    print(f"{palabra:10} → {attention_matrix[i, :]}")

# Palabra con mayor atención hacia cada otra palabra
print(f"\nPalabra más atendida por cada palabra:")
for i, palabra in enumerate(palabras_test):
    most_attended = np.argmax(attention_matrix[i])
    print(f"{palabra:10} → presta atención a {palabras_test[most_attended]:10} ({attention_matrix[i, most_attended]:.1%})")


# ============================================================================
# GRÁFICO: Visualizar Patrones de Atención
# ============================================================================

print("\n\nCreando visualización...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Gráfico 1: Heatmap de atención
ax1 = axes[0]
im1 = ax1.imshow(attention_matrix, cmap='viridis', aspect='auto')
ax1.set_xticks(range(seq_length))
ax1.set_yticks(range(seq_length))
ax1.set_xticklabels(palabras_test)
ax1.set_yticklabels(palabras_test)
ax1.set_xlabel('Keys (A qué se atiende)')
ax1.set_ylabel('Queries (Qué atiende)')
ax1.set_title('Matriz de Atención (Scaled Dot-Product)')
plt.colorbar(im1, ax=ax1, label='Peso de Atención')

# Gráfico 2: Barras de atención para una palabra específica
ax2 = axes[1]
palabra_idx = 1  # "cat"
atenciones = attention_matrix[palabra_idx]
colores = ['red' if i == palabra_idx else 'blue' for i in range(seq_length)]
ax2.bar(palabras_test, atenciones, color=colores, alpha=0.7)
ax2.set_ylabel('Peso de Atención')
ax2.set_title(f'Atención de "{palabras_test[palabra_idx]}" a todas las palabras')
ax2.set_ylim([0, max(atenciones) * 1.2])

# Añadir valores en las barras
for i, (palabra, atenc) in enumerate(zip(palabras_test, atenciones)):
    ax2.text(i, atenc + 0.01, f'{atenc:.2f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('/home/claude/attention_visualization.png', dpi=150, bbox_inches='tight')
print("✓ Gráfico guardado en: /home/claude/attention_visualization.png")
plt.close()

print("\n" + "="*70)
print("¡LISTO! Ahora entiendes cómo funciona Scaled Dot-Product Attention")
print("="*70)
