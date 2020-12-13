"""
Defines the models for the `bonds` application
"""
from django.db import models

class Bond(models.Model): 
    """
    A model representing a single bond. 
    """
    # ISINs consist of 12 characters (https://www.investopedia.com/terms/i/isin.asp)
    isin = models.CharField(max_length=12)
    size = models.PositiveIntegerField()
    currency = models.CharField(max_length=10)
    maturity = models.DateField()
    # LEIs are 20-character long (https://en.wikipedia.org/wiki/Legal_Entity_Identifier)
    lei = models.CharField(max_length=20)
    legal_name = models.CharField(max_length=100)
    # When the corresponding user is deleted, remove all their corresponding bonds as well 
    owner = models.ForeignKey('auth.User', related_name='bonds', on_delete=models.CASCADE)