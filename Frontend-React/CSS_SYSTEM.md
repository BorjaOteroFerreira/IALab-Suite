# Sistema de Diseño Moderno - IALab Suite

## Arquitectura CSS

### Archivos Principales

1. **`index.css`** - Sistema base con variables CSS y tokens de diseño
2. **`theme.css`** - Configuración de temas y utilidades avanzadas
3. **`components.css`** - Componentes reutilizables y utilidades
4. **`animations.css`** - Sistema de animaciones modernas
5. **`fonts.css`** - Configuración tipográfica
6. **`App.css`** - Layout principal de la aplicación

### Archivos de Componentes

- **`ChatContainer.css`** - Estilos del contenedor de chat
- **`MessageInput.css`** - Input de mensajes moderno
- **`ChatSidebar.css`** - Sidebar del chat
- **`ConfigSidebar.css`** - Panel de configuración
- **`LoadingIndicator.css`** - Indicadores de carga
- **`ErrorMessage.css`** - Mensajes de error
- **`YouTubeEmbed.css`** - Componentes multimedia (renombrado a media)

## Tokens de Diseño

### Colores
```css
--primary: #6366f1;           /* Índigo principal */
--primary-light: #818cf8;     /* Índigo claro */
--primary-dark: #4f46e5;      /* Índigo oscuro */
--accent: #a855f7;            /* Púrpura de acento */
--accent-light: #c084fc;      /* Púrpura claro */
--success: #22c55e;           /* Verde éxito */
--warning: #fb923c;           /* Naranja advertencia */
--error: #ef4444;             /* Rojo error */
```

### Espaciado
```css
--spacing-xs: 0.25rem;    /* 4px */
--spacing-sm: 0.5rem;     /* 8px */
--spacing-md: 1rem;       /* 16px */
--spacing-lg: 1.5rem;     /* 24px */
--spacing-xl: 2rem;       /* 32px */
--spacing-2xl: 3rem;      /* 48px */
--spacing-3xl: 4rem;      /* 64px */
```

### Tipografía
```css
--font-size-xs: 0.75rem;   /* 12px */
--font-size-sm: 0.875rem;  /* 14px */
--font-size-base: 1rem;    /* 16px */
--font-size-lg: 1.125rem;  /* 18px */
--font-size-xl: 1.25rem;   /* 20px */
--font-size-2xl: 1.5rem;   /* 24px */
--font-size-3xl: 1.875rem; /* 30px */
--font-size-4xl: 2.25rem;  /* 36px */
```

### Radios de Borde
```css
--radius-none: 0;
--radius-xs: 0.125rem;    /* 2px */
--radius-sm: 0.25rem;     /* 4px */
--radius-md: 0.375rem;    /* 6px */
--radius-lg: 0.5rem;      /* 8px */
--radius-xl: 0.75rem;     /* 12px */
--radius-2xl: 1rem;       /* 16px */
--radius-3xl: 1.5rem;     /* 24px */
--radius-full: 9999px;    /* Círculo completo */
```

### Sombras
```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
--shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

## Características Principales

### 🎨 Glassmorphism
- Efectos de cristal con `backdrop-filter: blur()`
- Transparencias sutiles
- Bordes luminosos

### 🎯 Accesibilidad
- Soporte para `prefers-reduced-motion`
- Soporte para `prefers-contrast: high`
- Estados de foco visibles
- Contraste adecuado

### 📱 Responsive Design
- Mobile-first approach
- Breakpoints semánticos
- Componentes adaptables

### ⚡ Performance
- Uso de `will-change` para optimización
- Animaciones con `transform` y `opacity`
- Lazy loading de efectos

### 🌙 Tema Oscuro
- Variables CSS para temas
- Soporte automático con `prefers-color-scheme`
- Transiciones suaves entre temas

## Componentes Reutilizables

### Botones
```css
.btn-primary      /* Botón principal */
.btn-secondary    /* Botón secundario */
.btn-outline      /* Botón con borde */
.btn-ghost        /* Botón transparente */
.btn-gradient     /* Botón con gradiente */
```

### Badges
```css
.badge-primary    /* Badge principal */
.badge-success    /* Badge de éxito */
.badge-warning    /* Badge de advertencia */
.badge-error      /* Badge de error */
```

### Avatares
```css
.avatar-sm        /* Avatar pequeño */
.avatar-md        /* Avatar mediano */
.avatar-lg        /* Avatar grande */
.avatar-xl        /* Avatar extra grande */
```

### Estados
```css
.loading-shimmer  /* Efecto de carga */
.skeleton         /* Placeholder animado */
.hover-lift       /* Elevación al hover */
.hover-scale      /* Escala al hover */
.hover-glow       /* Brillo al hover */
```

## Animaciones

### Transiciones
```css
--transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
--transition-base: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);
```

### Efectos
- `fadeIn` - Aparición gradual
- `slideInLeft/Right` - Deslizamiento lateral
- `bounceIn` - Entrada con rebote
- `scaleIn` - Entrada con escala
- `pulse` - Pulsación

## Mejores Prácticas

1. **Consistencia**: Usa siempre los tokens de diseño
2. **Performance**: Prefiere `transform` y `opacity` para animaciones
3. **Accesibilidad**: Incluye estados de foco y soporte para preferencias
4. **Responsive**: Diseña mobile-first
5. **Mantenibilidad**: Usa variables CSS para valores reutilizables

## Estructura de Archivos

```
src/
├── index.css          # Sistema base
├── theme.css          # Configuración de temas
├── components.css     # Componentes reutilizables
├── animations.css     # Animaciones
├── fonts.css          # Tipografía
├── App.css           # Layout principal
└── components/
    ├── ChatContainer.css
    ├── MessageInput.css
    ├── ChatSidebar.css
    ├── ConfigSidebar.css
    ├── LoadingIndicator.css
    ├── ErrorMessage.css
    └── YouTubeEmbed.css
```

## Compatibilidad

- ✅ Chrome 88+
- ✅ Firefox 87+
- ✅ Safari 14+
- ✅ Edge 88+
- ✅ iOS Safari 14+
- ✅ Android Chrome 88+

## Contribuciones

Al agregar nuevos estilos:
1. Usa las variables CSS existentes
2. Mantén la consistencia con el sistema
3. Incluye estados responsive
4. Agrega soporte para accesibilidad
5. Documenta nuevos componentes
