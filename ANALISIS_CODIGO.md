# Análisis Completo del Código del Proyecto

## Resumen Ejecutivo

Este es un proyecto Django de gestión de presupuestos para construcción, con arquitectura multi-tenant. El sistema permite gestionar materiales, mano de obra, subcontratos, presupuestos, compras y empleados.

**Arquitectura General:**
- Django 5.2.3
- Multi-tenant basado en `Company`
- Sistema de permisos por secciones (Presupuestos, Sueldos, Compras)
- Base de datos SQLite (desarrollo)
- Sin frontend framework (templates Django puros)

---

## 1. PROBLEMAS DE ORGANIZACIÓN Y ESTRUCTURA

### 1.1 Importaciones circulares y dependencias incorrectas

**Problema:** En `presupuestos/models.py` se importa `CotizacionDolar` desde `recursos.models`, pero `CotizacionDolar` está definido en `general/models.py`.

```python
# presupuestos/models.py línea 6
from recursos.models import CotizacionDolar, Lote, Tarea
```

**Impacto:** Esto puede causar errores de importación y hace el código confuso.

**Solución:**
```python
# presupuestos/models.py
from general.models import Company, Obra, TipoDolar, CotizacionDolar
from recursos.models import Lote, Tarea
```

### 1.2 Estructura de directorios inconsistente

**Problema:** Existe un directorio `presupuesto/` (singular) y una app `presupuestos/` (plural). Esto puede causar confusión.

**Solución:** Mantener consistencia en nombres. El directorio del proyecto debería llamarse `presupuesto` (correcto) y la app `presupuestos` (correcto), pero documentar claramente la diferencia.

### 1.3 Falta de separación de responsabilidades

**Problema:** Las vistas tienen mucha lógica de negocio mezclada con lógica de presentación.

**Ejemplo:** `recursos/views.py` tiene funciones muy largas (1500+ líneas) que mezclan:
- Validación de formularios
- Lógica de negocio (copiar hojas, crear lotes)
- Renderizado de templates

**Solución:** Extraer lógica de negocio a servicios o managers:
```python
# recursos/services.py
class LoteService:
    @staticmethod
    def crear_lote_con_copia(nombre, company, origen_mat, origen_mo, ...):
        # Lógica de creación
        pass
```

### 1.4 App `empleados` vacía

**Problema:** La app `empleados` solo tiene vistas que renderizan templates vacíos. Los modelos están vacíos.

**Solución:** 
- Si no se va a usar, eliminarla
- Si se va a usar, implementar los modelos y lógica necesaria

---

## 2. CÓDIGO DUPLICADO

### 2.1 Duplicación en métodos de actualización de precios

**Problema:** Los métodos `actualizar_precios_por_porcentaje` están duplicados en `Material`, `ManoDeObra` y `Subcontrato`.

**Ubicación:**
- `recursos/models.py` líneas 77-89 (Material)
- `recursos/models.py` líneas 141-147 (ManoDeObra)
- `recursos/models.py` líneas 202-208 (Subcontrato)

**Solución:** Crear un mixin o clase base:
```python
class PrecioActualizableMixin:
    @classmethod
    def actualizar_precios_por_porcentaje(cls, queryset, porcentaje):
        if not isinstance(porcentaje, Decimal):
            porcentaje = Decimal(str(porcentaje))
        factor = Decimal("1") + (porcentaje / Decimal("100"))
        from django.db.models import F
        queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)
        return queryset.count()
```

### 2.2 Duplicación en funciones de copia de hojas

**Problema:** Funciones similares para copiar hojas de materiales, mano de obra y subcontratos.

**Ubicación:** `recursos/views.py` líneas 826-914

**Solución:** Crear una función genérica:
```python
def _copy_hoja_desde_origen(model_hoja, model_detalle, hoja_origen, nombre, company, campos_copia):
    hoja = model_hoja.objects.create(nombre=nombre, company=company)
    if hoja_origen:
        hoja.origen = hoja_origen
        hoja.save()
        for d in hoja_origen.detalles.all():
            model_detalle.objects.create(
                hoja=hoja,
                **{campo: getattr(d, campo) for campo in campos_copia}
            )
    return hoja
```

### 2.3 Duplicación en vistas de listado

**Problema:** Patrones repetitivos en vistas de listado (material_list, mano_de_obra_list, subcontrato_list).

**Solución:** Usar vistas basadas en clases o crear funciones helper:
```python
def list_view_with_hoja(request, model, hoja_model, detalle_model, template_name, ...):
    # Lógica común
    pass
```

### 2.4 Duplicación en métodos `precio_por_unidad_analisis`

**Problema:** El mismo método repetido en múltiples modelos.

**Solución:** Mover a un mixin o clase base.

---

## 3. MALAS PRÁCTICAS

### 3.1 Uso de `__import__` en lugar de imports normales

**Problema:** En `compras/views.py` línea 15:
```python
return d - __import__("datetime").timedelta(days=d.weekday())
```

**Solución:**
```python
from datetime import timedelta
return d - timedelta(days=d.weekday())
```

### 3.2 Manejo de excepciones demasiado genérico

**Problema:** En `general/middleware.py` líneas 81-82 y 128-129:
```python
except Exception:
    return False
```

**Solución:** Capturar excepciones específicas:
```python
except (Resolver404, NoReverseMatch):
    return False
```

### 3.3 Uso de `get_object_or_404` sin verificar company

**Problema:** En algunos lugares se usa `get_object_or_404` sin filtrar por company, aunque luego se verifica.

**Ejemplo:** `presupuestos/views.py` línea 287

**Solución:** Siempre filtrar por company:
```python
item = get_object_or_404(
    PresupuestoItem, 
    pk=item_pk, 
    presupuesto=presupuesto,
    presupuesto__company=request.company
)
```

### 3.4 Magic numbers y strings hardcodeados

**Problema:** Valores mágicos en el código:
- `[:200]` en `general/views.py` línea 681
- `"presupuestos", "sueldos", "compras"` hardcodeados en middleware

**Solución:** Usar constantes:
```python
# general/constants.py
MAX_COTIZACIONES_DISPLAY = 200
SECTION_CODES = ["presupuestos", "sueldos", "compras"]
```

### 3.5 Falta de validación en formularios

**Problema:** Algunos formularios no validan relaciones entre campos.

**Ejemplo:** `TareaForm` no valida que el subrubro pertenezca al rubro seleccionado.

**Solución:** Agregar validación:
```python
def clean(self):
    data = super().clean()
    rubro = data.get('rubro')
    subrubro = data.get('subrubro')
    if rubro and subrubro and subrubro.rubro != rubro:
        raise forms.ValidationError("El subrubro debe pertenecer al rubro seleccionado.")
    return data
```

### 3.6 Uso de `select_related` y `prefetch_related` inconsistente

**Problema:** Algunas queries usan optimizaciones, otras no. Esto puede causar problemas de rendimiento.

**Ejemplo:** En `presupuestos/views.py` línea 127, se hace un loop sin optimización:
```python
for item in items:
    total_usd = sum(...)
```

**Solución:** Usar `select_related` y `prefetch_related` consistentemente:
```python
items = presupuesto.items.select_related(
    'tarea', 'tarea__rubro', 'tarea__subrubro'
).prefetch_related(...)
```

---

## 4. POSIBLES BUGS

### 4.1 Race condition en signal

**Problema:** En `general/signals.py` líneas 19-24, hay una posible race condition:
```python
has_admin = CompanyMembership.objects.filter(
    company=company, is_admin=True
).exists()
if not has_admin:
    instance.is_admin = True
    instance.save(update_fields=["is_admin"])
```

**Solución:** Usar transacciones atómicas:
```python
from django.db import transaction

@transaction.atomic
def first_member_is_admin(...):
    # código
```

### 4.2 División por cero potencial

**Problema:** En varios lugares se divide por valores que podrían ser cero.

**Ejemplo:** `recursos/models.py` línea 729:
```python
if total and self.cantidad:
    return total / self.cantidad
```

**Solución:** Validar explícitamente:
```python
if total and self.cantidad and self.cantidad > 0:
    return total / self.cantidad
```

### 4.3 Falta de validación de cotización USD

**Problema:** En `presupuestos/models.py` línea 108, se usa `cotiz` sin validar que no sea None:
```python
return self.tarea.costo_materiales_mezcla_usd_usando_cotizacion(cotiz, self.cantidad)
```

Aunque el método puede manejar None, no está claro.

**Solución:** Validar explícitamente o documentar el comportamiento.

### 4.4 Inconsistencia en unique_together

**Problema:** `PresupuestoItem` tiene `unique_together = ("presupuesto", "tarea")` pero permite múltiples items con la misma tarea si se crean en diferentes momentos.

**Solución:** Ya está correcto, pero documentar el comportamiento.

### 4.5 Falta de validación de fechas

**Problema:** En `compras/views.py` línea 48, se usa `fecha__isoweek` que puede fallar si la fecha no es válida.

**Solución:** Validar antes de usar.

### 4.6 Bug en filtro de semanas

**Problema:** En `compras/views.py` línea 48, se filtra por `fecha__isoweek` pero `isoweek` no es un campo de Django.

**Solución:** Usar una función personalizada o calcular manualmente:
```python
from datetime import datetime
semana_num = datetime.strptime(f"{año}-W{semana_filtro}-1", "%Y-W%W-%w").date()
```

---

## 5. PROBLEMAS DE RENDIMIENTO

### 5.1 N+1 queries en loops

**Problema:** En varios lugares se hacen queries dentro de loops.

**Ejemplo:** `presupuestos/views.py` líneas 126-133:
```python
for rubro in rubros:
    items = presupuesto.items.filter(tarea__rubro=rubro)
    total_usd = sum(...)
```

**Solución:** Usar `prefetch_related` y agregaciones:
```python
from django.db.models import Sum, Prefetch

rubros = Rubro.objects.filter(...).prefetch_related(
    Prefetch('tareas__presupuesto_items', 
             queryset=PresupuestoItem.objects.filter(presupuesto=presupuesto))
)
```

### 5.2 Queries innecesarias en `_get_totales`

**Problema:** En `general/views.py` líneas 39-57, se hacen múltiples queries separadas.

**Solución:** Usar `aggregate` o hacer una sola query con `Count`:
```python
from django.db.models import Count

totales = {
    'rubros': Rubro.objects.filter(company=company).count(),
    # ... pero mejor usar una sola query con annotate si es posible
}
```

### 5.3 Falta de índices en campos frecuentemente consultados

**Problema:** Campos como `company`, `fecha`, `nombre` se consultan frecuentemente pero pueden no tener índices.

**Solución:** Agregar `db_index=True` o usar `Meta.indexes`:
```python
class Meta:
    indexes = [
        models.Index(fields=['company', 'fecha']),
        models.Index(fields=['company', 'nombre']),
    ]
```

### 5.4 Carga innecesaria de relaciones

**Problema:** En algunos lugares se carga todo el objeto cuando solo se necesita el ID.

**Solución:** Usar `values_list` o `only`:
```python
rubro_ids = presupuesto.lote.tareas.values_list("rubro_id", flat=True).distinct()
```

### 5.5 Falta de paginación

**Problema:** Listados sin paginación pueden cargar miles de registros.

**Ejemplo:** `general/views.py` línea 681 limita a 200, pero debería ser paginado.

**Solución:** Usar `Paginator` de Django:
```python
from django.core.paginator import Paginator

paginator = Paginator(cotizaciones, 50)
page = request.GET.get('page', 1)
cotizaciones = paginator.get_page(page)
```

---

## 6. PROBLEMAS DE SEGURIDAD

### 6.1 Secret key por defecto en desarrollo

**Problema:** En `presupuesto/settings.py` líneas 26-29, hay una secret key hardcodeada para desarrollo.

**Solución:** Ya está manejado con variables de entorno, pero asegurarse de que nunca se use en producción.

### 6.2 Falta de validación de permisos en algunas vistas

**Problema:** Algunas vistas verifican `request.company` pero no verifican permisos de sección.

**Ejemplo:** `empleados/views.py` no verifica acceso a sección "sueldos".

**Solución:** Agregar decoradores o verificación:
```python
@login_required
def sueldos(request):
    if not request.membership or not request.membership.has_section_access("sueldos"):
        return redirect("no_section_access")
    # ...
```

### 6.3 Posible SQL injection en queries dinámicas

**Problema:** Aunque Django ORM protege contra SQL injection, hay que asegurarse de que no se use SQL raw sin parámetros.

**Solución:** Revisar que no haya uso de `raw()` o `extra()` sin parámetros.

### 6.4 Falta de CSRF protection en algunas vistas

**Problema:** Todas las vistas que modifican datos deberían verificar CSRF.

**Solución:** Ya está manejado por middleware, pero verificar que todas las formas POST lo usen.

### 6.5 Exposición de información en errores

**Problema:** En producción, `DEBUG=False` debería ocultar detalles de errores.

**Solución:** Ya está configurado, pero asegurarse de tener logging adecuado.

---

## 7. FALTA DE TIPADO

### 7.1 Sin type hints

**Problema:** El código no usa type hints de Python, lo que dificulta el mantenimiento y la detección de errores.

**Solución:** Agregar type hints progresivamente:
```python
from typing import Optional, List
from django.http import HttpRequest, HttpResponse

def presupuesto_list(request: HttpRequest) -> HttpResponse:
    # ...
```

### 7.2 Falta de validación de tipos en métodos

**Problema:** Métodos que reciben parámetros sin validar tipos.

**Solución:** Usar type hints y validación:
```python
def get_cotizacion_usd(self) -> Optional[Decimal]:
    # ...
```

---

## 8. MANEJO DE ERRORES DEFICIENTE

### 8.1 Excepciones silenciadas

**Problema:** En varios lugares se capturan excepciones pero no se registran.

**Ejemplo:** `general/views.py` líneas 672-673:
```python
except (ValueError, InvalidOperation):
    pass
```

**Solución:** Registrar errores:
```python
import logging
logger = logging.getLogger(__name__)

except (ValueError, InvalidOperation) as e:
    logger.error(f"Error procesando cotización: {e}")
    pass
```

### 8.2 Falta de mensajes de error al usuario

**Problema:** Cuando falla una operación, el usuario no recibe feedback claro.

**Solución:** Usar `messages` framework de Django:
```python
from django.contrib import messages

try:
    # operación
except Exception as e:
    messages.error(request, "Error al procesar la solicitud.")
    logger.error(f"Error: {e}")
```

### 8.3 Validación de formularios sin mensajes claros

**Problema:** Algunos formularios no tienen mensajes de error descriptivos.

**Solución:** Agregar `error_messages` a los campos:
```python
cantidad = forms.DecimalField(
    error_messages={
        'required': 'La cantidad es obligatoria.',
        'invalid': 'Ingrese un número válido.',
    }
)
```

---

## 9. NOMBRES POCO CLAROS

### 9.1 Variables con nombres genéricos

**Problema:** Variables como `obj`, `item`, `d`, `c` no son descriptivas.

**Solución:** Usar nombres más descriptivos:
```python
# En lugar de:
obj = form.save(commit=False)

# Usar:
presupuesto = form.save(commit=False)
```

### 9.2 Funciones con nombres poco descriptivos

**Problema:** Funciones como `_get_totales`, `_categorias_por_tipo` no indican claramente qué hacen.

**Solución:** Usar nombres más descriptivos:
```python
def obtener_estadisticas_por_empresa(company):
    # ...
```

### 9.3 Campos de modelo ambiguos

**Problema:** Algunos campos tienen nombres que pueden ser confusos.

**Ejemplo:** `activo` en `Presupuesto` - ¿activo significa "en uso" o "no cancelado"?

**Solución:** Usar nombres más claros o documentar:
```python
activo = models.BooleanField(
    default=True,
    help_text="Indica si el presupuesto está activo (no cancelado)."
)
```

---

## 10. ACOPLAMIENTO EXCESIVO

### 10.1 Dependencias circulares entre apps

**Problema:** `presupuestos` depende de `recursos`, y `recursos` puede depender de `general`.

**Solución:** Reorganizar dependencias:
- `general`: modelos base, sin dependencias
- `recursos`: depende de `general`
- `presupuestos`: depende de `general` y `recursos`

### 10.2 Lógica de negocio en vistas

**Problema:** Las vistas tienen mucha lógica de negocio acoplada.

**Solución:** Extraer a servicios o casos de uso:
```python
# presupuestos/services.py
class PresupuestoService:
    @staticmethod
    def calcular_totales_por_rubro(presupuesto):
        # Lógica de negocio
        pass
```

### 10.3 Dependencia directa de request en formularios

**Problema:** Los formularios reciben `request` directamente, acoplando la capa de presentación.

**Solución:** Pasar solo los datos necesarios:
```python
def __init__(self, *args, company=None, **kwargs):
    # En lugar de request=request
```

---

## 11. CÓDIGO INNECESARIO O MUERTO

### 11.1 Apps sin implementar

**Problema:** App `empleados` tiene modelos y tests vacíos.

**Solución:** Eliminar o implementar.

### 11.2 Tests vacíos

**Problema:** Todos los archivos `tests.py` están vacíos.

**Solución:** Implementar tests básicos:
```python
from django.test import TestCase
from general.models import Company, Rubro

class RubroTestCase(TestCase):
    def test_crear_rubro(self):
        company = Company.objects.create(nombre="Test")
        rubro = Rubro.objects.create(nombre="Test", company=company)
        self.assertEqual(rubro.nombre, "Test")
```

### 11.3 Imports no utilizados

**Problema:** Puede haber imports no utilizados.

**Solución:** Usar herramientas como `flake8` o `pylint` para detectarlos.

### 11.4 Código comentado

**Problema:** Revisar si hay código comentado que debería eliminarse.

**Solución:** Eliminar código comentado o documentar por qué está comentado.

---

## 12. FALTA DE TESTS

### 12.1 Sin tests unitarios

**Problema:** No hay tests para modelos, vistas, formularios.

**Solución:** Implementar tests básicos:
- Tests de modelos (creación, validación)
- Tests de vistas (respuestas HTTP, contexto)
- Tests de formularios (validación)

### 12.2 Sin tests de integración

**Problema:** No hay tests que verifiquen flujos completos.

**Solución:** Implementar tests de integración:
```python
class PresupuestoIntegrationTest(TestCase):
    def test_crear_presupuesto_completo(self):
        # Crear company, obra, lote, tareas
        # Crear presupuesto
        # Verificar cálculos
        pass
```

### 12.3 Sin tests de permisos

**Problema:** No hay tests que verifiquen el sistema de permisos multi-tenant.

**Solución:** Implementar tests de permisos:
```python
class PermissionsTest(TestCase):
    def test_usuario_solo_ve_su_empresa(self):
        # ...
```

---

## PROPUESTAS DE MEJORA CONCRETAS

### Prioridad Alta

1. **Corregir importación circular** en `presupuestos/models.py`
2. **Agregar tests básicos** para modelos críticos
3. **Implementar paginación** en listados
4. **Agregar logging** para errores
5. **Corregir bug de `isoweek`** en `compras/views.py`

### Prioridad Media

6. **Extraer lógica de negocio** a servicios
7. **Eliminar código duplicado** (métodos de precios, copia de hojas)
8. **Agregar type hints** progresivamente
9. **Optimizar queries** (N+1, índices)
10. **Mejorar manejo de errores** con mensajes al usuario

### Prioridad Baja

11. **Refactorizar nombres** de variables y funciones
12. **Documentar** métodos complejos
13. **Agregar validaciones** adicionales en formularios
14. **Implementar o eliminar** app `empleados`
15. **Agregar constantes** para valores mágicos

---

## CONCLUSIÓN

El proyecto tiene una base sólida pero necesita mejoras en:
- **Organización**: Separar lógica de negocio de vistas
- **Rendimiento**: Optimizar queries y agregar paginación
- **Calidad**: Agregar tests y type hints
- **Mantenibilidad**: Eliminar duplicación y mejorar nombres

Las mejoras de prioridad alta deberían implementarse primero para evitar bugs y problemas de rendimiento en producción.
