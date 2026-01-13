# Bauhaus Moderno - Quick Start Guide

## 🚀 Começar Rápido

### 1. Usar um Componente

```python
from src.ui.bauhaus_components import BauhausButton

# Criar botão
btn = BauhausButton("Clique aqui")
layout.addWidget(btn)
```

### 2. Usar Tokens de Design

```python
from config.bauhaus_tokens import BAUHAUS_PALETTE, SPACING

# Acessar cores
primary_color = BAUHAUS_PALETTE["blue"]      # #005BFF
danger_color = BAUHAUS_PALETTE["red"]        # #E10600

# Acessar espaçamento
small_space = SPACING["sm"]   # 8px
large_space = SPACING["lg"]   # 24px
```

### 3. Criar um Card

```python
from src.ui.bauhaus_components import BauhausCard, BauhausPageTitle

card = BauhausCard()
title = BauhausPageTitle("Meu Card")

card.layout().addWidget(title)
```

### 4. Criar um Formulário

```python
from src.ui.bauhaus_components import BauhausFormField, BauhausButton

# Campo de texto
email_field = BauhausFormField("Email", input_type="text")

# Campo de seleção
type_field = BauhausFormField("Tipo", input_type="combo")
type_field.input.addItems(["Opção 1", "Opção 2"])

# Botão
btn = BauhausButton("Enviar")
```

## 📚 Componentes Disponíveis

### Botões
- `BauhausButton` - Primário (Azul)
- `BauhausSecondaryButton` - Secundário (Branco)
- `BauhausDangerButton` - Destrutivo (Vermelho)
- `BauhausHighlightButton` - Destaque (Amarelo)
- `BauhausGhostButton` - Ghost (Transparente)

### Inputs
- `BauhausLineEdit` - Texto
- `BauhausTextEdit` - Área de texto
- `BauhausComboBox` - Seleção
- `BauhausSpinBox` - Número inteiro
- `BauhausDoubleSpinBox` - Número decimal

### Containers
- `BauhausCard` - Card padrão
- `BauhausStatCard` - Card com estatísticas
- `BauhausContainer` - Layout vertical
- `BauhausHorizontalContainer` - Layout horizontal

### Labels
- `BauhausPageTitle` - Título de página
- `BauhausSectionTitle` - Título de seção
- `BauhausBadge` - Badge de status

### Utilitários
- `BauhausFormField` - Campo de formulário
- `BauhausDivider` - Divisor

## 🎨 Cores Principais

```
Primária:   #005BFF (Azul)
Secundária: #E10600 (Vermelho)
Destaque:   #FFD600 (Amarelo)
Sucesso:    #00A859 (Verde)
Fundo:      #F2F2F2 (Cinza Claro)
```

## 📏 Espaçamento

```
XS: 4px
SM: 8px
MD: 16px
LG: 24px
XL: 32px
```

## 🔲 Border Radius

```
Botões:  8px
Inputs:  10px
Cards:   16px
Modais:  20px
Avatares: 50%
```

## 📖 Documentação Completa

Para documentação detalhada, veja: `BAUHAUS_DESIGN_SYSTEM.md`

## ✅ Validação

Para testar o design system:

```bash
python3 test_bauhaus_simple.py
```

---

**Bauhaus Moderno** © 2024 - Aguia Project
