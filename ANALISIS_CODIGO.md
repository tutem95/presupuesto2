# Analisis Completo del Codigo - Proyecto Presupuesto

## 1. Resumen de Arquitectura

Proyecto Django 5.2 multi-tenant para gestion de presupuestos de obra (sector construccion, Argentina). Usa SQLite, templates server-side con CSS custom, y un sistema de empresas/secciones para control de acceso.

### Apps

| App | Responsabilidad | Estado |
|---|---|---|
| `general` | Modelos base (Company, Rubro, Unidad, Proveedor, etc.), catlogos, middleware multi-tenant, signals, management commands | Funcional, muy grande |
| `recursos` | Materiales, Mano de Obra, Subcontratos, Hojas de precios, Mezclas, Lotes, Tareas | Funcional, vistas muy extensas |
| `presupuestos` | Presupuestos armados a partir de tareas/lotes | Funcional |
| `compras` | Semanas de pagos, compras por obra | Funcional |
| `empleados` | Placeholder: 3 vistas que renderizan templates vacios | No implementada |
| `usuarios` | Login, seleccion de empresa, control de acceso | Funcional |
| `presupuesto` (proyecto) | Settings, URLs raiz, wsgi/asgi | Estandar |

---

## 2. Problemas Detectados

### 2.1 CRITICO: Ausencia Total de Tests

**Todas** las apps tienen archivos `tests.py` vacios (solo el comentario de Django por defecto). En un sistema financiero/presupuestario esto es un riesgo grave:

- Logica de calculo de precios sin verificacion (precio unitario, conversion USD, porcentajes)
- Middleware multi-tenant sin tests (podria exponer datos entre empresas)
- Signals (primer miembro = admin) sin tests
- Management commands sin tests
- Formularios con logica de validacion sin tests

**Archivos afectados:** `general/tests.py`, `recursos/tests.py`, `presupuestos/tests.py`, `compras/tests.py`, `empleados/tests.py`, `usuarios/tests.py`

---

### 2.2 CRITICO: Problema N+1 de Queries Masivo

Los modelos de `recursos` tienen multiples metodos que ejecutan queries dentro de bucles, generando problemas N+1 severos:

**`Tarea.precio_total()`** - itera sobre `recursos` y cada recurso llama a `costo_total()` que hace hasta 3 queries individuales (una por cada tipo de hoja de precios):

```python
# recursos/models.py linea 766-791
def costo_total(self):
    lote = self.tarea.lote  # Query si no esta prefetched
    if self.material_id:
        hp = self._get_hoja_precio_material(lote)  # Query individual
        ...
    if self.mano_de_obra_id:
        hp = HojaPrecioManoDeObra.objects.get(...)  # Query individual
        ...
    if self.subcontrato_id:
        hp = HojaPrecioSubcontrato.objects.get(...)  # Query individual
        ...
```

**`MezclaMaterial.costo_en_hoja()`** y `precio_unidad_desde_hoja()` - cada uno hace una query `HojaPrecioMaterial.objects.get(...)` individualmente. Cuando una mezcla tiene 10 materiales, son 10 queries solo para calcular el precio.

**`Presupuesto.total_usd()`** - itera items, cada item calcula totales que a su vez iteran recursos que hacen queries individuales. Un presupuesto con 50 tareas y 5 recursos cada una genera **cientos** de queries.

**`presupuesto_rubros` view** - para cada rubro, calcula totales iterando items que a su vez iteran recursos con queries individuales. Complejidad O(rubros * items * recursos * queries).

---

### 2.3 CRITICO: Codigo Duplicado Masivo

#### 2.3.1 Views CRUD identicas en `general/views.py`

Las vistas de list/add/edit/delete para Rubro, Unidad, Equipo, TipoMaterial, CategoriaMaterial, Subrubro, RefEquipo, Proveedor, Obra, TipoDolar son **estructuralmente identicas** (790+ lineas). Cada entidad tiene exactamente el mismo patron:

```
list  -> filter(company=company)
add   -> POST: form.save(commit=False); obj.company=company; redirect
edit  -> get_object_or_404; POST: form.save(); redirect
delete -> get_object_or_404; POST: obj.delete(); redirect
```

Esto son ~550 lineas de codigo que podrian reducirse a ~50 con un mixin o una vista generica.

#### 2.3.2 `actualizar_precios_por_porcentaje` repetido 3 veces

El metodo `actualizar_precios_por_porcentaje` esta copiado identico en `Material`, `ManoDeObra` y `Subcontrato`:

```python
@classmethod
def actualizar_precios_por_porcentaje(cls, queryset, porcentaje):
    if not isinstance(porcentaje, Decimal):
        porcentaje = Decimal(str(porcentaje))
    factor = Decimal("1") + (porcentaje / Decimal("100"))
    from django.db.models import F
    queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)
    return queryset.count()
```

#### 2.3.3 `precio_por_unidad_analisis` repetido 5+ veces

El calculo `cantidad_por_unidad_venta * precio_unidad_venta` esta duplicado en:
- `Material.precio_por_unidad_analisis()`
- `ManoDeObra.precio_por_unidad_analisis()`
- `Subcontrato.precio_por_unidad_analisis()`
- `HojaPrecioMaterial.precio_por_unidad_analisis()`
- `HojaPrecioSubcontrato.precio_por_unidad_analisis()`
- `HojaPrecioManoDeObra.precio_por_unidad_analisis()`

#### 2.3.4 Views de bulk_update casi identicas

`material_bulk_update`, `mano_de_obra_bulk_update`, `subcontrato_bulk_update` tienen la misma estructura con variaciones minimas.

#### 2.3.5 Views de hojas de precios (list, detalle, detalle_edit, detalle_delete) triplicadas

El patron de `hoja_precios_list`, `hoja_mano_de_obra_list`, `hoja_subcontrato_list` es identico. Lo mismo para `_detalle`, `_detalle_edit`, `_detalle_delete`.

#### 2.3.6 Funciones `_copy_hoja_*` casi identicas

`_copy_hoja_materiales_desde_origen`, `_copy_hoja_mo_desde_origen`, `_copy_hoja_subcontratos_desde_origen` siguen el mismo patron.

#### 2.3.7 Management commands con patron duplicado

Los 4 commands (`load_proveedores`, `load_tipos_categorias`, `load_equipos_ref`, `load_rubros_subrubros`) repiten:
- Lectura de JSON
- Busqueda de company iterando todos los objetos
- Creacion con get_or_create

---

### 2.4 SEGURIDAD

#### 2.4.1 Eliminacion via GET permitida

Varias vistas de delete no verifican que sea POST para redireccionar. Por ejemplo:

```python
# recursos/views.py linea 1232-1234
def tarea_recurso_delete(request, lote_pk, tarea_pk, recurso_pk):
    ...
    if request.method == "POST":
        recurso.delete()
        return redirect(...)
    return redirect(...)  # En GET simplemente redirige pero no protege
```

Esto no es un bug directo (el delete solo pasa con POST), pero las vistas `hoja_detalle_delete`, `hoja_mano_de_obra_detalle_delete`, `hoja_subcontrato_detalle_delete`, `mezcla_material_delete`, y `tarea_recurso_delete` no muestran confirmacion en GET, simplemente redirigen. Esto significa que no hay pagina de confirmacion para estas acciones.

#### 2.4.2 Settings de seguridad HTTPS comentados

```python
# presupuesto/settings.py lineas 175-177
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
```

Estos deberian estar activos en produccion. Dejar `SESSION_COOKIE_SECURE = False` permite que las cookies de sesion viajen por HTTP.

#### 2.4.3 Busqueda de Company ineficiente y no segura en commands

```python
# Todos los management commands hacen esto:
company = None
for c in Company.objects.all():
    if c.nombre.strip().lower() == company_name.lower():
        company = c
        break
```

Esto carga TODAS las empresas en memoria. Deberia usar `Company.objects.filter(nombre__iexact=company_name).first()`.

#### 2.4.4 No hay verificacion de acceso por seccion en Compras/Empleados

El middleware verifica la seccion "presupuestos" por path prefixes, pero las secciones "compras" y "sueldos" tienen un comentario:

```python
# middleware.py linea 147
# sueldos y compras se verifican cuando existan esas URLs
```

Esto significa que **cualquier usuario con membership** puede acceder a `/compras/` y `/empleados/` sin tener la seccion asignada.

#### 2.4.5 Falta `@require_POST` en vistas de toggle/delete

`presupuesto_toggle_activo` modifica datos pero no usa `@require_POST` ni verifica POST antes de hacer el toggle (linea 81: verifica POST, pero un GET no devuelve error, simplemente redirige).

`presupuesto_item_delete` no muestra confirmacion, simplemente elimina en POST y redirige en GET.

#### 2.4.6 Imports dentro de funciones

```python
# general/views.py linea 658-659
from datetime import datetime
# recursos/views.py linea 1061
from general.models import TipoDolar
# recursos/models.py linea 84
from django.db.models import F
```

Imports lazy dentro de funciones son un anti-pattern. Deberian estar al inicio del archivo.

---

### 2.5 BUGS POTENCIALES

#### 2.5.1 Race condition en `first_member_is_admin` signal

```python
# general/signals.py
def first_member_is_admin(sender, instance, created, **kwargs):
    if not created:
        return
    has_admin = CompanyMembership.objects.filter(company=company, is_admin=True).exists()
    if not has_admin:
        instance.is_admin = True
        instance.save(update_fields=["is_admin"])
```

Si dos usuarios se crean simultaneamente para una empresa nueva, ambos podrian ver `has_admin=False` y ambos se marcarian como admin. Deberia usarse `select_for_update()` o una constraint a nivel de DB.

#### 2.5.2 `_get_week_start` usa import inline hacky

```python
# compras/views.py linea 14
def _get_week_start(d):
    return d - __import__("datetime").timedelta(days=d.weekday())
```

Usar `__import__` directamente es un anti-pattern. Deberia importar `timedelta` al inicio del archivo.

#### 2.5.3 `fecha__isoweek` no existe en Django ORM

```python
# compras/views.py linea 48
semanas_qs = semanas_qs.filter(fecha__isoweek=semana_filtro)
```

Django no tiene un lookup `isoweek` para DateField. Esto **lanzara una excepcion** en runtime. El lookup correcto seria `fecha__week`.

#### 2.5.4 Variable shadowing en `compras_list`

```python
# compras/views.py lineas 25-38
año = request.GET.get("año")  # string o None
...
if año:
    try:
        año = int(año)  # ahora es int
```

El parametro `año` se reasigna de string a int, lo cual es confuso y puede causar bugs si se reutiliza despues.

#### 2.5.5 Errores silenciados con `except: pass`

```python
# recursos/admin.py linea 37-38
def mostrar_precio_analisis(self, obj):
    try:
        return f"{obj.precio_por_unidad_analisis():,.2f}"
    except:
        return "-"
```

`except:` sin tipo especifico captura **todo**, incluyendo `KeyboardInterrupt` y `SystemExit`. Deberia ser al menos `except Exception:`.

#### 2.5.6 Decimal comparison con 0 en vez de Decimal("0")

```python
# recursos/models.py linea 797
if total == 0:  # compara Decimal con int
```

Funciona por la coercion de Python, pero es una mala practica. Deberia ser `total == Decimal("0")` o `not total`.

#### 2.5.7 `actualizar_precios_por_porcentaje` retorna count despues del update

```python
# recursos/models.py lineas 86-89
queryset.update(precio_unidad_venta=F("precio_unidad_venta") * factor)
return queryset.count()  # Esto hace una SEGUNDA query innecesaria
```

`queryset.update()` ya retorna el numero de filas actualizadas. El `count()` posterior es redundante.

---

### 2.6 RENDIMIENTO

#### 2.6.1 `_get_totales` ejecuta 16 queries COUNT independientes

```python
# general/views.py linea 39-57
def _get_totales(company):
    return {
        "ref_equipos": RefEquipo.objects.filter(company=company).count(),
        "rubros": Rubro.objects.filter(company=company).count(),
        # ... 14 mas
    }
```

Son 16 COUNT queries. Podrian reducirse con una sola query raw o con annotations.

#### 2.6.2 Creacion de hojas/lotes sin bulk_create en funciones _copy_*

Las funciones `_copy_hoja_materiales_desde_origen`, `_copy_hoja_mo_desde_origen`, etc. crean objetos uno a uno dentro de un bucle:

```python
for d in hoja_origen.detalles.select_related("material").all():
    HojaPrecioMaterial.objects.create(...)  # Una INSERT por iteracion
```

Mientras que las funciones `hoja_precios_list`, `hoja_mano_de_obra_list`, etc. usan `bulk_create`. Inconsistencia.

#### 2.6.3 SQLite en produccion

El settings usa SQLite por defecto. Para un sistema multi-tenant con multiples usuarios concurrentes, SQLite tiene limitaciones severas de escritura concurrente.

#### 2.6.4 No hay paginacion

Las listas de materiales, mano de obra, subcontratos, tareas, etc. cargan **todos** los registros. No hay paginacion. Con cientos o miles de materiales, esto sera lento.

#### 2.6.5 `Mezcla.precio_por_unidad_mezcla()` ejecuta N queries

```python
for det in self.detalles.select_related("material", "material__unidad_de_venta").all():
    total += det.costo_en_hoja()  # Cada uno hace otra query a HojaPrecioMaterial
```

---

### 2.7 ORGANIZACION Y ESTRUCTURA

#### 2.7.1 `recursos/views.py` es demasiado grande: ~1580 lineas

Este archivo contiene logica para:
- Materiales (list, edit, delete, bulk_update)
- Hojas de precios de materiales
- Mano de obra (list, edit, delete, bulk_update)
- Hojas de mano de obra
- Subcontratos (list, edit, delete, bulk_update)
- Hojas de subcontratos
- Mezclas
- Lotes
- Tareas y TareaRecurso
- 6 funciones helper privadas de copia

Deberia dividirse en multiples modulos (ej: `recursos/views/materiales.py`, `recursos/views/lotes.py`, etc.).

#### 2.7.2 `general/views.py` tiene ~786 lineas de CRUD repetitivo

Todo el CRUD de catalogos podria extraerse a un mixin generico o usar class-based views.

#### 2.7.3 `recursos/models.py` tiene ~818 lineas con 14 modelos

Modelos muy acoplados entre si. Deberia dividirse logicamente.

#### 2.7.4 La app `empleados` esta vacia

Tiene 3 vistas que renderizan templates estaticos, un `models.py` vacio, y esta registrada en INSTALLED_APPS. Si no se va a implementar pronto, deberia eliminarse o marcarse claramente como placeholder.

#### 2.7.5 Nombre de proyecto confuso

El proyecto Django se llama `presupuesto` (singular) pero la app principal se llama `presupuestos` (plural). Esto genera confusion, especialmente en imports como `from presupuestos.models import Presupuesto` vs la carpeta `presupuesto/settings.py`.

---

### 2.8 ACOPLAMIENTO EXCESIVO

#### 2.8.1 `general/views.py` importa modelos de `recursos`

```python
from recursos.models import Lote, ManoDeObra, Material, Mezcla, Subcontrato, Tarea
```

La app `general` deberia ser la base que otras apps importan, no al reves. Que `general` dependa de `recursos` crea una dependencia circular conceptual.

#### 2.8.2 `presupuestos/models.py` importa `CotizacionDolar` desde `recursos.models`

```python
from recursos.models import CotizacionDolar, Lote, Tarea
```

`CotizacionDolar` esta definido en `general.models`, pero `presupuestos` lo importa desde `recursos.models` donde fue re-importado. Esto es incorrecto y confuso (aunque funciona por el sistema de imports de Python).

**Correccion:** Deberia importar directamente de `general.models`.

#### 2.8.3 Modelo `TareaRecurso` usa 4 FKs opcionales como "union type"

```python
class TareaRecurso(models.Model):
    material = models.ForeignKey(..., null=True, blank=True)
    mano_de_obra = models.ForeignKey(..., null=True, blank=True)
    subcontrato = models.ForeignKey(..., null=True, blank=True)
    mezcla = models.ForeignKey(..., null=True, blank=True)
```

Esto es un anti-pattern llamado "polymorphic FK". No hay constraint que garantice que exactamente una de las 4 FKs tenga valor. Se podria usar `django-polymorphic`, `GenericForeignKey`, o un patron de herencia.

---

### 2.9 MANEJO DE ERRORES DEFICIENTE

#### 2.9.1 Errores de conversion de Decimal silenciados

```python
# general/views.py lineas 664-672
try:
    valor = Decimal(val.strip().replace(",", "."))
    CotizacionDolar.objects.update_or_create(...)
except (ValueError, InvalidOperation):
    pass  # Error silenciado: el usuario no sabe que el valor no se guardo
```

#### 2.9.2 Middleware silencia excepciones de resolucion de URL

```python
# general/middleware.py linea 128
except Exception:
    pass
```

Si `resolve()` falla por cualquier razon, el middleware simplemente lo ignora. Deberia al menos loggearlo.

#### 2.9.3 No hay mensajes de feedback al usuario

Las vistas no usan `django.contrib.messages` para informar al usuario de acciones exitosas o errores. Cuando se crea, edita o elimina un recurso, simplemente se redirige sin feedback.

#### 2.9.4 Forms de hojas de precios no validan nombre unico

Las vistas `hoja_precios_list`, `hoja_mano_de_obra_list`, `hoja_subcontrato_list` crean hojas directamente desde `request.POST["nombre"]` sin validar unicidad. Si el nombre ya existe, Django lanzara un `IntegrityError` no capturado.

---

### 2.10 FALTA DE TIPADO

Python permite type hints desde 3.5+. Este proyecto no usa ninguno:

- Funciones sin anotaciones de tipos
- No hay `py.typed` ni `mypy.ini`
- No hay `django-stubs` en requirements

---

### 2.11 CODIGO MUERTO O INNECESARIO

#### 2.11.1 App `empleados` completamente vacia

3 vistas que renderizan templates placeholder, sin modelos ni logica.

#### 2.11.2 Import no usado en `recursos/models.py`

```python
from general.models import (
    ...
    CotizacionDolar,  # Solo se usa en Lote.get_cotizacion_usd via query directa
    ...
)
```

Algunos imports podrian no ser necesarios como importaciones directas.

#### 2.11.3 `usuarios/models.py` esta vacio

Solo tiene el comentario de Django.

#### 2.11.4 Variable `Min` importada pero no usada

```python
# general/views.py linea 678
from django.db.models import Min  # No se usa en ningun lugar
```

#### 2.11.5 Parametro `request` almacenado pero no usado en formularios

Muchos formularios guardan `self._request = request` pero nunca usan `_request`:

```python
class RubroForm(forms.ModelForm):
    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._request = request  # Nunca se usa
```

Esto aplica a: `RubroForm`, `UnidadForm`, `TipoMaterialForm`, `EquipoForm`, `ProveedorForm`, `TipoDolarForm`.

---

### 2.12 NOMBRES POCO CLAROS

- `RefEquipo`: nombre ambiguo. Podria llamarse `SubEquipo` o `CategoriaEquipo` para ser consistente con el patron `Rubro > Subrubro`.
- `_get_totales()`: demasiado generico. `_get_catalog_counts()` seria mas claro.
- `tarea` campo en `ManoDeObra`: confuso porque `Tarea` es tambien un modelo. Deberia llamarse `descripcion` o `actividad`.
- `items` en `PresupuestoItem`: el related_name `items` es muy generico.
- `presupuesto` como nombre de proyecto y `presupuestos` como app es confuso.
- `HojaPrecios` vs `HojaPreciosManoDeObra` vs `HojaPreciosSubcontrato`: la pluralizacion es inconsistente (`HojaPrecios` vs `HojaPreciosManoDeObra`).

---

## 3. Mejoras Propuestas (Priorizadas)

### PRIORIDAD ALTA

1. **Escribir tests unitarios y de integracion**
   - Tests para logica de calculo de precios (unitarios, totales, conversion USD)
   - Tests para el middleware multi-tenant (aislamiento de datos entre empresas)
   - Tests para signals
   - Tests de integracion para flujos completos (crear lote > crear tarea > agregar recursos > calcular presupuesto)

2. **Corregir el bug de `fecha__isoweek`** en `compras/views.py:48` - cambiar a `fecha__week`

3. **Agregar verificacion de secciones para Compras y Empleados** en el middleware

4. **Resolver el problema N+1 de queries** usando:
   - `prefetch_related` con `Prefetch` objects personalizados
   - Precalcular precios en las hojas en vez de calcularlo on-the-fly
   - Caching de cotizaciones dentro del request

5. **Corregir el import erroneo** en `presupuestos/models.py`: importar `CotizacionDolar` desde `general.models` en vez de `recursos.models`

### PRIORIDAD MEDIA

6. **Refactorizar CRUD de catalogos** usando class-based views genericas o un mixin:
   ```python
   class CatalogCRUDMixin:
       model = None
       form_class = None
       list_template = None
       ...
   ```

7. **Dividir `recursos/views.py`** en modulos: `views/materiales.py`, `views/mano_de_obra.py`, `views/subcontratos.py`, `views/lotes.py`, `views/tareas.py`, `views/mezclas.py`

8. **Extraer metodos duplicados** a mixins o funciones utilitarias:
   - `precio_por_unidad_analisis` -> mixin `PrecioAnalisisMixin`
   - `actualizar_precios_por_porcentaje` -> funcion en `recursos/utils.py`

9. **Agregar paginacion** a todas las vistas de listado

10. **Usar `django.contrib.messages`** para feedback al usuario

11. **Mover imports** al inicio de archivos (eliminar imports lazy)

12. **Agregar constraint a `TareaRecurso`** para garantizar que exactamente un FK tenga valor:
    ```python
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(material__isnull=False, mano_de_obra__isnull=True, subcontrato__isnull=True, mezcla__isnull=True) |
                    Q(material__isnull=True, mano_de_obra__isnull=False, subcontrato__isnull=True, mezcla__isnull=True) |
                    Q(material__isnull=True, mano_de_obra__isnull=True, subcontrato__isnull=False, mezcla__isnull=True) |
                    Q(material__isnull=True, mano_de_obra__isnull=True, subcontrato__isnull=True, mezcla__isnull=False)
                ),
                name="exactly_one_resource_type",
            )
        ]
    ```

### PRIORIDAD BAJA

13. **Migrar a PostgreSQL** para produccion (concurrencia, mejor rendimiento, JSON fields)

14. **Agregar type hints** a modelos, vistas y formularios

15. **Eliminar o completar la app `empleados`**: si no se va a implementar pronto, quitarla de `INSTALLED_APPS`

16. **Usar `unique_together` -> `UniqueConstraint`**: Django recomienda `constraints` con `UniqueConstraint` en vez del legacy `unique_together`

17. **Agregar `select_for_update`** en el signal `first_member_is_admin` para evitar race conditions

18. **Habilitar settings HTTPS** en produccion (desomentar `SESSION_COOKIE_SECURE`, etc.)

19. **Agregar logging** en vez de `pass` silencioso en excepciones

20. **Crear un `BaseCompanyModel` abstracto** para reducir la repeticion del FK a Company:
    ```python
    class BaseCompanyModel(models.Model):
        company = models.ForeignKey(Company, on_delete=models.CASCADE)
        class Meta:
            abstract = True
    ```

21. **Refactorizar management commands** con una clase base que maneje lectura de JSON y busqueda de company

22. **Eliminar el import de `Min`** no usado en `general/views.py`

23. **Remover `_request`** no utilizado de formularios que no lo necesitan

24. **Usar `__import__` -> import normal** en `compras/views.py`

---

## 4. Metricas del Proyecto

| Metrica | Valor |
|---|---|
| Apps Django | 6 (5 funcionales + 1 placeholder) |
| Modelos | ~25 |
| Vistas | ~60 |
| Formularios | ~15 |
| Templates | ~45 |
| Lineas de codigo Python (aprox.) | ~5,500 |
| Tests | 0 |
| Management commands | 5 |
| Migraciones | ~25 |
| Lineas CSS | ~820 |
| Dependencias | 4 (Django, asgiref, sqlparse, tzdata) |

---

## 5. Conclusion

El proyecto tiene una base funcional solida con buen manejo de multi-tenancy, una UI limpia y una arquitectura Django estandar. Sin embargo, presenta problemas significativos de:

1. **Duplicacion masiva** (~40% del codigo podria eliminarse con refactoring)
2. **Rendimiento** (N+1 queries en calculos criticos de precios)
3. **Tests inexistentes** (riesgo critico para un sistema financiero)
4. **Seguridad** (secciones no verificadas para Compras/Empleados)
5. **Un bug concreto** (`fecha__isoweek` no existe en Django)

Las mejoras de mayor impacto serian: escribir tests, corregir los bugs, resolver N+1 queries, y refactorizar el codigo duplicado.
