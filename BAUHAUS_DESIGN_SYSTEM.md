# Bauhaus Moderno - Design System

## 🎨 Visão Geral

O **Bauhaus Moderno** é um sistema de design geométrico, funcional e moderno desenvolvido especificamente para o Aguia. Ele aplica os princípios da Bauhaus original com uma abordagem contemporânea para SaaS, garantindo uma interface limpa, intuitiva e profissional.

## 📋 Fundamentos

### 1. Filosofia Visual

- **Geométrico**: Formas limpas e precisas
- **Funcional**: Cada elemento tem um propósito claro
- **Moderno**: Estética contemporânea e minimalista
- **Corporativo**: Profissionalismo e confiança

### 2. Princípios de Design

- ✓ Sem poluição visual
- ✓ Cores bem definidas
- ✓ Efeitos úteis e propositais
- ✓ Geometria clara
- ✓ Ritmo visual consistente
- ✓ Contraste adequado
- ✓ Hierarquia clara

## 🎯 Paleta de Cores

### Cores Estruturais

| Cor | Hex | Uso |
|-----|-----|-----|
| Preto Estrutural | `#0E0E0E` | Fundo de sidebar, texto principal |
| Branco | `#FFFFFF` | Fundo de cards, inputs |
| Cinza Claro | `#F2F2F2` | Fundo de página, headers |
| Cinza Médio | `#D6D6D6` | Bordas, divisores |
| Cinza Escuro | `#3A3A3A` | Texto secundário |

### Cores Bauhaus

| Cor | Hex | Uso |
|-----|-----|-----|
| Azul Bauhaus | `#005BFF` | Botões primários, links, destaques |
| Vermelho Bauhaus | `#E10600` | Botões destrutivos, alertas críticos |
| Amarelo Bauhaus | `#FFD600` | Botões de destaque, avisos |

## 🔲 Raio de Borda (Border Radius)

| Elemento | Radius | Nota |
|----------|--------|------|
| Botões | 8px | Levemente arredondado |
| Inputs | 10px | Um pouco mais arredondado |
| Cards | 16px | Moderadamente arredondado |
| Modais | 20px | Bem arredondado |
| Avatares | 50% | Circular |

**Regra de Ouro**: Nada totalmente quadrado, nada exageradamente arredondado.

## 📏 Grid e Espaçamento

Sistema base: **4px / 8px / 16px / 24px / 32px**

| Tamanho | Valor | Uso |
|---------|-------|-----|
| XS | 4px | Espaçamentos mínimos |
| SM | 8px | Espaçamentos pequenos |
| MD | 16px | Espaçamento padrão |
| LG | 24px | Espaçamento grande |
| XL | 32px | Espaçamentos maiores |

**Regra**: Nunca usar valores quebrados (ex: 5px, 13px, 18px).

## 🔘 Componentes

### Botões

#### Botão Primário
- **Fundo**: `#005BFF` (Azul)
- **Texto**: `#FFFFFF` (Branco)
- **Hover**: `#0047CC`
- **Ativo**: `#003399`
- **Radius**: 8px
- **Altura**: 44px

```python
from src.ui.bauhaus_components import BauhausButton

btn = BauhausButton("Clique aqui")
```

#### Botão Secundário
- **Fundo**: `#FFFFFF` (Branco)
- **Texto**: `#0E0E0E` (Preto)
- **Borda**: 2px solid `#0E0E0E`
- **Hover**: Fundo `#F2F2F2`
- **Radius**: 8px

```python
from src.ui.bauhaus_components import BauhausSecondaryButton

btn = BauhausSecondaryButton("Cancelar")
```

#### Botão Destrutivo
- **Fundo**: `#E10600` (Vermelho)
- **Texto**: `#FFFFFF` (Branco)
- **Hover**: `#B80000`
- **Radius**: 8px

```python
from src.ui.bauhaus_components import BauhausDangerButton

btn = BauhausDangerButton("Deletar")
```

#### Botão de Destaque
- **Fundo**: `#FFD600` (Amarelo)
- **Texto**: `#0E0E0E` (Preto)
- **Hover**: `#E6C000`
- **Radius**: 8px

```python
from src.ui.bauhaus_components import BauhausHighlightButton

btn = BauhausHighlightButton("Importante")
```

### Inputs

- **Fundo**: `#FFFFFF`
- **Texto**: `#0E0E0E`
- **Borda**: 2px solid `#D6D6D6`
- **Radius**: 10px
- **Altura**: 44px
- **Padding**: 12px 14px

#### Focus State
- **Borda**: 2px solid `#005BFF`
- **Sombra**: 0 0 0 3px rgba(0, 91, 255, 0.15)

```python
from src.ui.bauhaus_components import BauhausLineEdit

input_field = BauhausLineEdit("Digite aqui...")
```

### Cards

- **Fundo**: `#FFFFFF`
- **Borda**: 1px solid `#D6D6D6`
- **Radius**: 16px
- **Padding**: 24px
- **Gap entre cards**: 24px
- **Sombra**: Nenhuma (Bauhaus é plano e limpo)

```python
from src.ui.bauhaus_components import BauhausCard

card = BauhausCard()
card.add_widget(some_widget)
```

### Badges (Status)

| Tipo | Fundo | Texto | Radius |
|------|-------|-------|--------|
| Sucesso | `#00A859` | `#FFFFFF` | 999px |
| Erro | `#E10600` | `#FFFFFF` | 999px |
| Alerta | `#FFD600` | `#0E0E0E` | 999px |
| Info | `#005BFF` | `#FFFFFF` | 999px |

```python
from src.ui.bauhaus_components import BauhausBadge

badge = BauhausBadge("Ativo", badge_type="success")
```

### Tabs

#### Inativa
- **Texto**: `#3A3A3A` (Cinza Escuro)

#### Ativa
- **Texto**: `#0E0E0E` (Preto)
- **Borda Inferior**: 3px solid `#005BFF`

**Nota**: Nada de fundo colorido — só linha.

### Modais

- **Fundo**: `#FFFFFF`
- **Radius**: 20px
- **Padding**: 32px
- **Overlay**: rgba(0, 0, 0, 0.6)

### Navbar / Sidebar

- **Fundo**: `#0E0E0E` (Preto)
- **Texto**: `#FFFFFF` (Branco)
- **Item Ativo**: `#005BFF` (Azul)
- **Hover**: `#1A1A1A`

### Tabelas

#### Header
- **Fundo**: `#F2F2F2`
- **Texto**: `#0E0E0E`

#### Linhas
- **Borda**: 1px solid `#D6D6D6`

#### Linha Ativa
- **Fundo**: rgba(0, 91, 255, 0.05)

## 📦 Usando o Design System

### Importar Tokens

```python
from config.bauhaus_tokens import (
    BAUHAUS_PALETTE,
    BORDER_RADIUS,
    SPACING,
    TYPOGRAPHY
)
```

### Usar Componentes

```python
from src.ui.bauhaus_components import (
    BauhausButton,
    BauhausLineEdit,
    BauhausCard,
    BauhausPageTitle,
    BauhausBadge
)

# Criar título
title = BauhausPageTitle("Minha Página")

# Criar card
card = BauhausCard()

# Criar input
input_field = BauhausLineEdit("Digite seu email")

# Criar botão
btn = BauhausButton("Enviar")

# Criar badge
badge = BauhausBadge("Ativo", badge_type="success")
```

### Aplicar Tema

O tema Bauhaus é automaticamente aplicado na inicialização da aplicação através do `main_window.py`.

```python
from config.bauhaus_theme import get_bauhaus_stylesheet

stylesheet = get_bauhaus_stylesheet()
self.setStyleSheet(stylesheet)
```

## 🎬 Animações e Transições

- **Hover**: Mudança de cor suave (sem transição CSS, apenas mudança de estado)
- **Focus**: Borda azul com sombra sutil
- **Pressed**: Cor mais escura do que hover

## 📱 Responsividade

O design system mantém proporções consistentes em diferentes tamanhos de tela:

- **Desktop**: Layout completo com sidebar
- **Tablet**: Sidebar colapsável
- **Mobile**: Menu hambúrguer (se aplicável)

## 🔧 Customização

### Alterar Cores Globais

Editar `config/bauhaus_tokens.py`:

```python
BAUHAUS_PALETTE = {
    "blue": "#005BFF",  # Alterar cor primária
    # ...
}
```

### Criar Novo Componente

```python
from PySide6.QtWidgets import QPushButton
from config.bauhaus_tokens import BUTTONS

class MyCustomButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("MyCustomButton")
        self.setMinimumHeight(44)
```

## 📚 Referências

- **Bauhaus Original**: Movimento artístico do século XX
- **Design Moderno**: Minimalismo e funcionalismo
- **SaaS Design**: Padrões de interface para aplicações web/desktop

## 🚀 Próximos Passos

- [ ] Criar temas de cores alternativas (Dark Mode)
- [ ] Adicionar mais componentes (Sliders, Toggles, etc)
- [ ] Documentar padrões de layout
- [ ] Criar guia de acessibilidade

---

**Bauhaus Moderno** © 2024 - Aguia Project
