from django.db import models

class Bond(models.Model): 
    isin = models.CharField(max_length=12)
    size = models.PositiveIntegerField()
    currency = models.CharField(max_length=10)
    maturity = models.DateField()
    lei = models.CharField(max_length=100)
    legal_name = models.CharField(max_length=100)