# Botones de Ventana - Dashboard de Estructura

## ✨ Mejora Implementada

### Botones de Control de Ventana

Se agregaron botones estándar de ventana al Dashboard de Estructura, similar a las ventanas de Windows.

---

## 🎨 Botones Agregados

### 1. **Botón de Minimizar (—)**
- **Símbolo:** — (línea horizontal)
- **Acción:** Minimiza la ventana a la barra de tareas
- **Tooltip:** "Minimizar"
- **Posición:** Antes del botón de maximizar

### 2. **Botón de Maximizar/Restaurar (□ / ❐)**
- **Símbolo Normal:** □ (cuadrado simple)
- **Símbolo Maximizado:** ❐ (cuadrado doble)
- **Acción:** Alterna entre ventana maximizada y tamaño normal
- **Tooltip:** "Maximizar" / "Restaurar"
- **Posición:** Entre minimizar y cerrar

### 3. **Botón de Cerrar (✖)**
- **Símbolo:** ✖ (X)
- **Acción:** Cierra la ventana del Dashboard
- **Tooltip:** "Cerrar"
- **Posición:** Último botón (derecha)
- **Color hover:** Rojo (#e81123) - estilo Windows

---

## 🎨 Estilos Visuales

### Diseño de Botones
```
Tamaño: 30x30 px
Fondo: Transparente
Color texto: #cccccc (gris claro)
Border: Ninguno
Font-size: 14-16pt
```

### Estados de Hover

#### Minimizar y Maximizar:
- **Hover:** Fondo gris oscuro (#3d3d3d)
- **Pressed:** Fondo gris más oscuro (#2d2d2d)
- **Border-radius:** 3px

#### Cerrar:
- **Hover:** Fondo rojo (#e81123) - estilo Windows
- **Pressed:** Fondo rojo oscuro (#c50d1d)
- **Border-radius:** 3px

---

## 🔧 Implementación Técnica

### Método `toggle_maximize()`

```python
def toggle_maximize(self):
    """Toggle between maximized and normal window state"""
    if self.isMaximized():
        # Restore to normal size
        self.showNormal()
        self.maximize_btn.setText("□")
        self.maximize_btn.setToolTip("Maximizar")
    else:
        # Maximize window
        self.showMaximized()
        self.maximize_btn.setText("❐")
        self.maximize_btn.setToolTip("Restaurar")
```

### Botones en el Header

```python
# Minimize button
minimize_btn = QPushButton("—")
minimize_btn.clicked.connect(self.showMinimized)

# Maximize/Restore button
self.maximize_btn = QPushButton("□")
self.maximize_btn.clicked.connect(self.toggle_maximize)

# Close button
close_btn = QPushButton("✖")
close_btn.clicked.connect(self.close)
```

---

## 📋 Orden Visual de Botones

```
[Título Dashboard]  [...otros botones...]  [—] [□] [✖]
                                            MIN MAX CLOSE
```

**Posición:** Esquina superior derecha del header

---

## ✅ Funcionalidades

### Botón Minimizar:
- ✅ Minimiza la ventana a la barra de tareas
- ✅ Click en icono de la barra restaura la ventana

### Botón Maximizar:
- ✅ Primera vez: Maximiza la ventana a pantalla completa
- ✅ Cambia ícono a "❐" (restaurar)
- ✅ Tooltip cambia a "Restaurar"
- ✅ Segunda vez: Restaura al tamaño original (1200x800)
- ✅ Cambia ícono de vuelta a "□" (maximizar)
- ✅ Tooltip cambia a "Maximizar"

### Botón Cerrar:
- ✅ Cierra la ventana del Dashboard
- ✅ Hover en rojo (estilo Windows)
- ✅ Regresa a la ventana principal del Widget Sidebar

---

## 🎯 Comportamiento Esperado

### Test 1: Minimizar
```bash
1. Abrir Dashboard de Estructura
2. Click en botón "—"
3. ✅ Ventana se minimiza a la barra de tareas
4. Click en icono del Dashboard en la barra
5. ✅ Ventana se restaura
```

### Test 2: Maximizar
```bash
1. Abrir Dashboard (tamaño normal: 1200x800)
2. Click en botón "□"
3. ✅ Ventana se maximiza a pantalla completa
4. ✅ Botón cambia a "❐"
5. Click en botón "❐"
6. ✅ Ventana vuelve al tamaño normal (1200x800)
7. ✅ Botón cambia a "□"
```

### Test 3: Cerrar
```bash
1. Abrir Dashboard
2. Hover sobre botón "✖"
3. ✅ Botón se pone rojo
4. Click en botón "✖"
5. ✅ Dashboard se cierra
6. ✅ Widget Sidebar principal sigue abierto
```

---

## 📁 Archivo Modificado

**Archivo:** `src/views/dashboard/structure_dashboard.py`

**Cambios:**
1. Método `create_header()` - Agregados 3 botones de ventana
2. Método `toggle_maximize()` - Nueva función para maximizar/restaurar

**Líneas modificadas:** ~100 líneas

---

## 🎨 Detalles de Diseño

### Paleta de Colores:

| Elemento | Color | Uso |
|----------|-------|-----|
| Texto botones | `#cccccc` | Color por defecto |
| Hover (min/max) | `#3d3d3d` | Fondo en hover |
| Pressed (min/max) | `#2d2d2d` | Fondo presionado |
| Hover (close) | `#e81123` | Fondo rojo Windows |
| Pressed (close) | `#c50d1d` | Rojo oscuro presionado |

### Símbolos Unicode:
- **Minimizar:** `—` (U+2014 EM DASH)
- **Maximizar:** `□` (U+25A1 WHITE SQUARE)
- **Restaurar:** `❐` (U+2750 UPPER RIGHT DROP-SHADOWED WHITE SQUARE)
- **Cerrar:** `✖` (U+2716 HEAVY MULTIPLICATION X)

---

## 🚀 Compatibilidad

- ✅ Windows 10/11
- ✅ PyQt6 6.7.0+
- ✅ Tema oscuro consistente con el resto de la app

---

## 📝 Notas Adicionales

1. **Tamaño de ventana por defecto:** 1200x800 px
2. **Posición inicial:** Centrada en pantalla
3. **Modal:** El Dashboard es modal (bloquea la ventana principal)
4. **Atajos de teclado:**
   - No hay atajo para minimizar (comportamiento estándar)
   - No hay atajo para maximizar (comportamiento estándar)
   - `Escape` cierra la ventana

---

## ✅ Estado

**Estado:** ✅ Completo
**Fecha:** 2025-10-30
**Versión:** Widget Sidebar 3.0.0

---

## 🎉 Resumen

Se agregaron exitosamente los botones de control de ventana estándar:

- ✅ **Botón Minimizar (—)** - Minimiza a la barra de tareas
- ✅ **Botón Maximizar/Restaurar (□/❐)** - Alterna tamaño de ventana
- ✅ **Botón Cerrar (✖)** - Cierra el Dashboard (hover rojo)

Los botones están estilizados con el tema oscuro de la aplicación y tienen efectos hover profesionales similar a Windows 11.

**Para probar:**
1. Cierra y reinicia la aplicación
2. Abre el Dashboard de Estructura
3. Prueba los nuevos botones en la esquina superior derecha
4. ¡Disfruta de la mejor experiencia de usuario! ✨
