from django.db import models

class Rubro(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Rubro"
        verbose_name_plural = "Rubros"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Unidad(models.Model):
    nombre = models.CharField(max_length=50, unique=True)  # Ej: 'm2', 'kg', 'hora'

    class Meta:
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    

class Subrubro(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    rubro = models.ForeignKey(Rubro, on_delete=models.CASCADE, related_name='subrubros')

    class Meta:
        verbose_name = "Subrubro"
        verbose_name_plural = "Subrubros"
        ordering = ['rubro__nombre', 'nombre'] # Ordenar por Rubro y luego por nombre de Subrubro
        unique_together = ('nombre', 'rubro') # Asegura que no haya dos subrubros con el mismo nombre dentro del mismo rubro

    def __str__(self):
        return f"{self.nombre} ({self.rubro.nombre})"
    
    
class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
class TipoMaterial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Tipo de Material"
        verbose_name_plural = "Tipos de Material"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class CategoriaMaterial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    tipo = models.ForeignKey(TipoMaterial, on_delete=models.CASCADE, related_name='categorias')

    class Meta:
        verbose_name = "Categoría de Material"
        verbose_name_plural = "Categorías de Material"
        ordering = ['tipo__nombre', 'nombre']
        unique_together = ('nombre', 'tipo')

    def __str__(self):
        return f"{self.nombre} ({self.tipo.nombre})"