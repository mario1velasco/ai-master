"""
Implementación completa de Scaled Dot-Product Attention y Multi-Head Attention
usando PyTorch (el framework usado en los modelos reales)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math

# ============================================================================
# CLASE 1: Scaled Dot-Product Attention (La Base)
# ============================================================================

class ScaledDotProductAttention(nn.Module):
    """
    Implementación de Scaled Dot-Product Attention
    
    Fórmula: Attention(Q, K, V) = softmax(QK^T / √d_k) V
    """
    
    def __init__(self, dropout_rate=0.0):
        super().__init__()
        self.dropout = nn.Dropout(dropout_rate)
    
    def forward(self, query, key, value, mask=None):
        """
        Args:
            query: (batch_size, seq_len, d_k)
            key:   (batch_size, seq_len, d_k)
            value: (batch_size, seq_len, d_v)
            mask:  (batch_size, 1, 1, seq_len) - Opcional, para mascarar posiciones
        
        Returns:
            output: (batch_size, seq_len, d_v)
            attention_weights: (batch_size, seq_len, seq_len)
        """
        
        # Paso 1: Calcular scores = QK^T / √d_k
        d_k = query.shape[-1]
        scores = torch.matmul(query, key.transpose(-2, -1))
        scores = scores / math.sqrt(d_k)
        
        print(f"\n[Scaled Dot-Product Attention]")
        print(f"  Shape scores (QK^T): {scores.shape}")
        print(f"  d_k: {d_k}, √d_k: {math.sqrt(d_k):.4f}")
        
        # Paso 2: Aplicar mask si existe (para evitar que vea palabras del futuro)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))
        
        # Paso 3: Aplicar softmax
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        print(f"  Attention weights shape: {attention_weights.shape}")
        print(f"  Suma de pesos (debe ser ~1.0): {attention_weights.sum(dim=-1)[0, 0]:.4f}")
        
        # Paso 4: Multiplicar por V
        output = torch.matmul(attention_weights, value)
        
        return output, attention_weights


# ============================================================================
# CLASE 2: Multi-Head Attention
# ============================================================================

class MultiHeadAttention(nn.Module):
    """
    Multi-Head Attention: h cabezas de atención en paralelo
    
    Proceso:
    1. Proyectar Q, K, V h veces con proyecciones diferentes
    2. Calcular atención en paralelo para cada cabeza
    3. Concatenar resultados
    4. Proyectar final
    """
    
    def __init__(self, d_model, num_heads, dropout_rate=0.1):
        super().__init__()
        
        self.d_model = d_model
        self.num_heads = num_heads
        
        # d_model debe ser divisible por num_heads
        assert d_model % num_heads == 0, f"d_model ({d_model}) debe ser divisible por num_heads ({num_heads})"
        
        self.d_k = d_model // num_heads  # Dimensión por cabeza
        self.d_v = d_model // num_heads
        
        # Proyecciones lineales para Q, K, V
        self.W_q = nn.Linear(d_model, d_model)  # (d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        
        # Proyección final
        self.W_o = nn.Linear(d_model, d_model)
        
        # Mecanismo de atención
        self.attention = ScaledDotProductAttention(dropout_rate)
    
    def forward(self, query, key, value, mask=None):
        """
        Args:
            query: (batch_size, seq_len, d_model)
            key:   (batch_size, seq_len, d_model)
            value: (batch_size, seq_len, d_model)
            mask:  Opcional
        
        Returns:
            output: (batch_size, seq_len, d_model)
        """
        batch_size = query.shape[0]
        seq_len = query.shape[1]
        
        print(f"\n[Multi-Head Attention]")
        print(f"  Batch size: {batch_size}, Seq len: {seq_len}")
        print(f"  d_model: {self.d_model}, num_heads: {self.num_heads}")
        print(f"  d_k (dimensión por cabeza): {self.d_k}")
        
        # Paso 1: Proyectar Q, K, V
        Q = self.W_q(query)  # (batch, seq_len, d_model)
        K = self.W_k(key)
        V = self.W_v(value)
        
        # Paso 2: Dividir en múltiples cabezas
        # (batch, seq_len, d_model) → (batch, seq_len, num_heads, d_k)
        # → (batch, num_heads, seq_len, d_k)
        Q = Q.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.d_v).transpose(1, 2)
        
        print(f"  Q shape después de reshape: {Q.shape}")
        
        # Paso 3: Aplicar atención a cada cabeza en paralelo
        attn_output, attn_weights = self.attention(Q, K, V, mask)
        # attn_output: (batch, num_heads, seq_len, d_v)
        
        print(f"  Attention output shape: {attn_output.shape}")
        
        # Paso 4: Concatenar cabezas
        # (batch, num_heads, seq_len, d_v) → (batch, seq_len, num_heads, d_v)
        # → (batch, seq_len, d_model)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.d_model)
        
        print(f"  After concatenation: {attn_output.shape}")
        
        # Paso 5: Proyección final
        output = self.W_o(attn_output)
        
        print(f"  Output final: {output.shape}")
        
        return output, attn_weights


# ============================================================================
# CLASE 3: Feed-Forward Network (Sublayer del Transformer)
# ============================================================================

class FeedForwardNetwork(nn.Module):
    """
    Fully connected feed-forward network
    
    FFN(x) = max(0, xW1 + b1)W2 + b2
    """
    
    def __init__(self, d_model, d_ff, dropout_rate=0.1):
        super().__init__()
        
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout_rate)
    
    def forward(self, x):
        """
        Args:
            x: (batch_size, seq_len, d_model)
        
        Returns:
            (batch_size, seq_len, d_model)
        """
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


# ============================================================================
# CLASE 4: Encoder Layer Completo
# ============================================================================

class EncoderLayer(nn.Module):
    """
    Un layer del encoder del Transformer
    
    Estructura:
    1. Multi-Head Attention
    2. Add & Norm (residual connection + layer normalization)
    3. Feed-Forward Network
    4. Add & Norm
    """
    
    def __init__(self, d_model, num_heads, d_ff, dropout_rate=0.1):
        super().__init__()
        
        # Sub-layer 1: Multi-Head Attention
        self.self_attention = MultiHeadAttention(d_model, num_heads, dropout_rate)
        self.norm1 = nn.LayerNorm(d_model)
        
        # Sub-layer 2: Feed-Forward
        self.feed_forward = FeedForwardNetwork(d_model, d_ff, dropout_rate)
        self.norm2 = nn.LayerNorm(d_model)
        
        self.dropout = nn.Dropout(dropout_rate)
    
    def forward(self, x, mask=None):
        """
        Args:
            x: (batch_size, seq_len, d_model)
        
        Returns:
            (batch_size, seq_len, d_model)
        """
        # Sub-layer 1: Self-Attention + Add & Norm
        attn_output, _ = self.self_attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))  # Residual connection
        
        # Sub-layer 2: Feed-Forward + Add & Norm
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))  # Residual connection
        
        return x


# ============================================================================
# CLASE 5: Posición Encoding
# ============================================================================

class PositionalEncoding(nn.Module):
    """
    Positional Encoding usando senos y cosenos
    
    PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
    """
    
    def __init__(self, d_model, max_seq_length=512):
        super().__init__()
        
        # Crear la matriz de positional encoding
        pe = torch.zeros(max_seq_length, d_model)
        position = torch.arange(0, max_seq_length, dtype=torch.float).unsqueeze(1)
        
        # div_term = 10000^(2i/d_model)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float) * 
            -(math.log(10000.0) / d_model)
        )
        
        # Aplicar seno a posiciones pares
        pe[:, 0::2] = torch.sin(position * div_term)
        
        # Aplicar coseno a posiciones impares
        if d_model % 2 == 1:
            pe[:, 1::2] = torch.cos(position * div_term[:-1])
        else:
            pe[:, 1::2] = torch.cos(position * div_term)
        
        # Registrar como buffer (no es un parámetro entrenable)
        self.register_buffer('pe', pe.unsqueeze(0))  # (1, max_seq_length, d_model)
    
    def forward(self, x):
        """
        Args:
            x: (batch_size, seq_len, d_model)
        
        Returns:
            x + positional encoding
        """
        return x + self.pe[:, :x.size(1), :]


# ============================================================================
# DEMOSTRACIÓN: Usar todas las clases
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("IMPLEMENTACIÓN COMPLETA DEL TRANSFORMER EN PYTORCH")
    print("=" * 80)
    
    # Parámetros (como en el paper)
    d_model = 64      # Dimensión del modelo (original: 512)
    num_heads = 4     # Número de cabezas (original: 8)
    d_ff = 256        # Dimensión feed-forward (original: 2048)
    seq_length = 6    # Longitud de la secuencia
    batch_size = 2    # Número de ejemplos en el batch
    
    print(f"\nConfiguración:")
    print(f"  d_model: {d_model}")
    print(f"  num_heads: {num_heads}")
    print(f"  d_ff: {d_ff}")
    print(f"  seq_length: {seq_length}")
    print(f"  batch_size: {batch_size}")
    
    # ========================================================================
    # EJEMPLO 1: Solo Attention
    # ========================================================================
    print("\n" + "=" * 80)
    print("EJEMPLO 1: MULTI-HEAD ATTENTION")
    print("=" * 80)
    
    # Input
    x = torch.randn(batch_size, seq_length, d_model)
    print(f"\nInput shape: {x.shape}")
    
    # Multi-Head Attention
    mha = MultiHeadAttention(d_model, num_heads)
    output, weights = mha(x, x, x)
    
    print(f"\nOutput shape: {output.shape}")
    print(f"Attention weights shape: {weights.shape}")
    
    # ========================================================================
    # EJEMPLO 2: Encoder Layer Completo
    # ========================================================================
    print("\n" + "=" * 80)
    print("EJEMPLO 2: ENCODER LAYER COMPLETO")
    print("=" * 80)
    
    encoder_layer = EncoderLayer(d_model, num_heads, d_ff)
    
    print(f"\nEncoder Layer:")
    output = encoder_layer(x)
    print(f"Output shape: {output.shape}")
    
    # ========================================================================
    # EJEMPLO 3: Positional Encoding
    # ========================================================================
    print("\n" + "=" * 80)
    print("EJEMPLO 3: POSITIONAL ENCODING")
    print("=" * 80)
    
    pos_encoding = PositionalEncoding(d_model, max_seq_length=512)
    x_with_pos = pos_encoding(x)
    
    print(f"\nInput shape: {x.shape}")
    print(f"With positional encoding shape: {x_with_pos.shape}")
    
    # Visualizar positional encoding
    pe_matrix = pos_encoding.pe[0, :seq_length, :].detach()
    print(f"\nPositional encoding (primeras 5 dimensiones, todas las posiciones):")
    print(pe_matrix[:, :5])
    
    # ========================================================================
    # EJEMPLO 4: Full Stack - Simular traducción
    # ========================================================================
    print("\n" + "=" * 80)
    print("EJEMPLO 4: FLUJO COMPLETO")
    print("=" * 80)
    
    class SimpleTranslator(nn.Module):
        def __init__(self, d_model, num_heads, d_ff, num_layers=2):
            super().__init__()
            self.embedding = nn.Embedding(1000, d_model)  # Vocabulario de 1000 palabras
            self.pos_encoding = PositionalEncoding(d_model)
            self.encoder_layers = nn.ModuleList([
                EncoderLayer(d_model, num_heads, d_ff) 
                for _ in range(num_layers)
            ])
            self.output_layer = nn.Linear(d_model, 1000)  # De vuelta a vocabulario
        
        def forward(self, x):
            # Embeddings
            x = self.embedding(x)
            
            # Positional encoding
            x = self.pos_encoding(x)
            
            # Encoder layers
            for encoder in self.encoder_layers:
                x = encoder(x)
            
            # Output
            x = self.output_layer(x)
            return x
    
    # Input: secuencias de IDs de palabras
    input_ids = torch.randint(0, 1000, (batch_size, seq_length))
    
    model = SimpleTranslator(d_model, num_heads, d_ff, num_layers=2)
    logits = model(input_ids)
    
    print(f"\nInput IDs shape: {input_ids.shape}")
    print(f"Output logits shape: {logits.shape}")
    print(f"Predictions shape: {logits.argmax(dim=-1).shape}")
    
    # ========================================================================
    # EJEMPLO 5: Contar parámetros
    # ========================================================================
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS DEL MODELO")
    print("=" * 80)
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"\nTotal parámetros: {total_params:,}")
    print(f"Parámetros entrenable: {trainable_params:,}")
    
    # Desglose por componentes
    print(f"\nDesglose de parámetros:")
    for name, param in model.named_parameters():
        print(f"  {name:30} {param.numel():>10,}")
    
    # ========================================================================
    # RESUMEN
    # ========================================================================
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print("""
    Este código muestra cómo funciona el Transformer:
    
    1. MultiHeadAttention: 
       - Proyecta Q, K, V
       - Calcula atención en paralelo para cada cabeza
       - Concatena y proyecta el resultado final
    
    2. EncoderLayer:
       - Aplica atención + residual + layer norm
       - Aplica feed-forward + residual + layer norm
    
    3. PositionalEncoding:
       - Añade información de posición usando senos/cosenos
    
    4. El flujo completo:
       Embeddings → Positional Encoding → Encoder Layers → Output
    
    Este es EXACTAMENTE el mecanismo que usa ChatGPT, Claude, etc.
    """)
