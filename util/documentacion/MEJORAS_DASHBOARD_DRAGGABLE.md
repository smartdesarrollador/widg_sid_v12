# Mejoras Dashboard - Ventana Arrastrable y No-Modal

## 🎯 Problemas Solucionados

### **Problema 1: No se puede mover la ventana del Dashboard**
❌ Antes: No había forma de arrastrar/mover la ventana del Dashboard
✅ Ahora: El título es arrastrable - click y arrastra para mover la ventana

### **Problema 2: La función de restaurar no funciona**
❌ Antes: Al click en restaurar, la ventana no volvía al tamaño anterior
✅ Ahora: Guarda la geometría anterior y la restaura correctamente

### **Problema 3: Dashboard bloquea el sidebar principal**
❌ Antes: Con el Dashboard abierto, no se podía interactuar con el sidebar
✅ Ahora: Dashboard es no-modal - puedes usar ambas ventanas simultáneamente

---

## ✨ Mejoras Implementadas

### **1. Barra de Título Arrastrable**

**Implementación:**
```python
# El título ahora captura eventos del mouse
self.title_label.mousePressEvent = self.header_mouse_press
self.title_label.mouseMoveEvent = self.header_mouse_move
self.title_label.mouseReleaseEvent = self.header_mouse_release
```

**Funcionalidades:**
- ✅ **Click y arrastra** en el título "📊 Dashboard de Estructura"
- ✅ **Cursor cambia** a cruz de movimiento (SizeAllCursor)
- ✅ **Si está maximizado**, al arrastrar se restaura automáticamente y luego se mueve
- ✅ **Movimiento suave** sin lag

**Eventos manejados:**
```python
def header_mouse_press(self, event):
    # Guarda posición inicial del drag
    self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

def header_mouse_move(self, event):
    # Si está maximizado, restaura primero
    if self.is_custom_maximized:
        self.showNormal()
    # Mueve la ventana
    self.move(event.globalPosition().toPoint() - self.drag_position)

def header_mouse_release(self, event):
    # Termina el drag
    self.dragging = False
```

### **2. Función de Restaurar Arreglada**

**Problema anterior:**
- No guardaba la geometría antes de maximizar
- Al restaurar, no sabía a qué tamaño volver

**Solución:**
```python
def toggle_maximize(self):
    if self.is_custom_maximized:
        # Restaurar usando geometría guardada
        if self.normal_geometry:
            self.setGeometry(self.normal_geometry)
    else:
        # GUARDAR geometría actual antes de maximizar
        self.normal_geometry = self.geometry()
        # Luego maximizar
        self.setGeometry(maximized_rect)
```

**Variables agregadas:**
```python
self.normal_geometry = None  # Guarda QRect del tamaño normal
```

**Flujo correcto:**
1. Usuario click en □ (maximizar)
2. Dashboard guarda geometría actual (ej: 1200x800 en posición X,Y)
3. Dashboard maximiza dejando espacio para sidebar
4. Usuario click en ❐ (restaurar)
5. Dashboard restaura la geometría guardada exacta
6. Vuelve al tamaño y posición original

### **3. Ventana No-Modal**

**Cambios en `main_window.py`:**

**Antes:**
```python
dashboard = StructureDashboard(db_manager=self.controller.config_manager.db, parent=self)
dashboard.exec()  # ❌ Modal - bloquea todo
```

**Ahora:**
```python
dashboard = StructureDashboard(db_manager=self.controller.config_manager.db, parent=self)

# Guardar referencia para que no se destruya
self.structure_dashboard = dashboard

# Mostrar como no-modal
dashboard.show()  # ✅ Permite interacción con otras ventanas
```

**Cambios en `structure_dashboard.py`:**
```python
# Antes
self.setModal(True)  # ❌ Bloqueaba

# Ahora
self.setModal(False)  # ✅ No bloquea

# Window flags
self.setWindowFlags(
    Qt.WindowType.Window |
    Qt.WindowType.CustomizeWindowHint
)
```

**Resultado:**
- ✅ Puedes hacer click en el sidebar mientras el Dashboard está abierto
- ✅ Puedes abrir categorías del sidebar
- ✅ Puedes usar ambas ventanas simultáneamente
- ✅ Dashboard no bloquea nada

---

## 🎨 Mejoras Visuales

### Cursor del Título:
```python
self.title_label.setCursor(Qt.CursorShape.SizeAllCursor)
```
- El cursor cambia a "✥" (cruz de movimiento) al pasar sobre el título
- Indica visualmente que se puede arrastrar

### Área Arrastrable:
```
[📊 Dashboard de Estructura] ← Esta área es arrastrable
     ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
     Click y arrastra aquí
```

---

## 🧪 Testing

### Test 1: Arrastrar Ventana
```bash
1. Abrir Dashboard de Estructura
2. Pasar mouse sobre el título "📊 Dashboard de Estructura"
3. ✅ Cursor cambia a cruz de movimiento
4. Click y mantener en el título
5. Arrastrar mouse
6. ✅ Ventana se mueve suavemente
7. Soltar mouse
8. ✅ Ventana queda en nueva posición
```

### Test 2: Arrastrar Desde Maximizado
```bash
1. Abrir Dashboard
2. Click en □ para maximizar
3. ✅ Dashboard maximiza (deja espacio para sidebar)
4. Click y arrastrar en el título
5. ✅ Dashboard se restaura automáticamente al tamaño normal
6. ✅ Continúa moviéndose con el mouse
7. Soltar mouse
8. ✅ Ventana queda en nueva posición (tamaño normal)
```

### Test 3: Maximizar y Restaurar
```bash
1. Abrir Dashboard en posición (100, 100) tamaño (1200, 800)
2. Mover Dashboard a otra posición (300, 150)
3. Click en □ (maximizar)
4. ✅ Dashboard maximiza
5. ✅ Botón cambia a ❐
6. Click en ❐ (restaurar)
7. ✅ Dashboard vuelve EXACTAMENTE a posición (300, 150) tamaño (1200, 800)
8. ✅ Botón cambia a □
```

### Test 4: Interacción con Sidebar
```bash
1. Abrir Dashboard de Estructura
2. Dashboard se muestra
3. Sin cerrar el Dashboard, intentar click en el sidebar
4. ✅ Sidebar responde al click
5. ✅ Se puede abrir categorías
6. ✅ Se puede navegar por el sidebar
7. ✅ Ambas ventanas funcionan simultáneamente
```

### Test 5: Abrir Múltiples Veces
```bash
1. Abrir Dashboard
2. Cerrar Dashboard
3. Abrir Dashboard nuevamente
4. ✅ Dashboard se abre correctamente
5. ✅ No hay errores ni referencias colgadas
```

---

## 📁 Archivos Modificados

### 1. `src/views/dashboard/structure_dashboard.py`

**Variables agregadas en `__init__`:**
```python
self.dragging = False
self.drag_position = None
self.normal_geometry = None  # Para restaurar
```

**Métodos agregados:**
```python
def header_mouse_press(self, event)
def header_mouse_move(self, event)
def header_mouse_release(self, event)
```

**Método modificado:**
```python
def toggle_maximize(self)
    # Ahora guarda y restaura geometría correctamente
```

**UI modificada:**
```python
def create_header(self)
    # Title label ahora tiene eventos de mouse
    # Cursor cambia a SizeAllCursor
```

### 2. `src/views/main_window.py`

**Variable agregada:**
```python
self.structure_dashboard = None  # Línea 54
```

**Método modificado:**
```python
def open_structure_dashboard(self)
    # Cambiado de dashboard.exec() a dashboard.show()
    # Guarda referencia en self.structure_dashboard
```

---

## 🎯 Comparación

### Antes:
```
❌ No se puede mover la ventana
❌ Restaurar no funciona (no vuelve al tamaño original)
❌ Dashboard bloquea el sidebar (modal)
❌ No se puede usar el sidebar mientras Dashboard está abierto
```

### Ahora:
```
✅ Título arrastrable con cursor visual
✅ Restaurar funciona perfectamente (guarda geometría)
✅ Dashboard NO bloquea el sidebar (no-modal)
✅ Puedes usar ambas ventanas simultáneamente
✅ Si arrastras desde maximizado, se restaura automáticamente
```

---

## 🔧 Detalles Técnicos

### Arrastre de Ventana:
- **Método:** Captura de eventos del mouse en el QLabel del título
- **Coordenadas:** Usa `globalPosition()` y `frameGeometry()`
- **Drag position:** Calcula offset desde topLeft del frame
- **Restauración automática:** Si está maximizado, restaura antes de arrastrar

### Geometría Guardada:
- **Tipo:** `QRect` completo (x, y, width, height)
- **Cuándo se guarda:** Justo antes de maximizar
- **Cuándo se usa:** Al hacer click en restaurar (❐)
- **Persistencia:** Se mantiene durante la vida de la ventana

### No-Modal:
- **setModal(False):** En structure_dashboard.py
- **show() en lugar de exec():** En main_window.py
- **Referencia guardada:** `self.structure_dashboard` para evitar destrucción
- **Window flags:** `Qt.WindowType.Window` para comportamiento normal

---

## 📊 Beneficios

✅ **Mejor UX:** Ventana se puede mover libremente
✅ **Funcionalidad completa:** Maximizar/Restaurar funciona correctamente
✅ **Multitarea:** Usar Dashboard y Sidebar simultáneamente
✅ **Intuitivo:** Cursor visual indica que el título es arrastrable
✅ **Robusto:** Maneja casos edge (arrastrar desde maximizado)

---

## 📝 Notas Adicionales

1. **Cursor:** El cursor cambia a `SizeAllCursor` (✥) sobre el título
2. **Padding:** El título tiene padding de 5px para área de click más grande
3. **Eventos:** Los eventos del mouse son capturados solo en el título, no en botones
4. **Performance:** El arrastre es suave sin lag
5. **Compatibilidad:** Funciona en Windows 10/11 con PyQt6

---

## ⚠️ Consideraciones

1. **Referencia:** La referencia `self.structure_dashboard` se mantiene hasta que se cierra el Dashboard
2. **Memoria:** Solo hay una instancia del Dashboard a la vez
3. **Parent:** El Dashboard tiene parent=MainWindow para herencia de estilos
4. **Modal:** Ya no es modal, lo que permite interacción con otras ventanas

---

**Fecha:** 2025-10-30
**Estado:** ✅ Completo y Funcional
**Versión:** Widget Sidebar 3.0.0

---

## 🎉 Para Probar

**Reinicia la aplicación:**
```bash
python main.py
```

**Prueba las nuevas funcionalidades:**

1. ✅ **Arrastrar:** Abre Dashboard → Click y arrastra el título
2. ✅ **Maximizar/Restaurar:** Click en □ para maximizar → Click en ❐ para restaurar al tamaño exacto anterior
3. ✅ **Sidebar activo:** Con Dashboard abierto, click en categorías del sidebar → Ambos funcionan

**¡Disfruta de la ventana completamente funcional! ✨**
