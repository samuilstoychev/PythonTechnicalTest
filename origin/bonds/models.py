"""
Defines the models for the `bonds` application
"""
from django.db import models

class Bond(models.Model): 
    """
    A model representing a single bond. 
    """
    isin = models.CharField(max_length=12)
    size = models.PositiveIntegerField()
    currency = models.CharField(max_length=10)
    maturity = models.DateField()
    lei = models.CharField(max_length=100)
    legal_name = models.CharField(max_length=100)
    owner = models.ForeignKey('auth.User', related_name='bonds', on_delete=models.CASCADE)