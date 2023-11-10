from django.db import models

class User(models.Model):
    username = models.CharField(max_length=30)
    nps = models.IntegerField()

class Game(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    rolls = models.CharField(max_length=6, blank=True)

class Player(models.Model):
    name = models.CharField(max_length=20)
    image = models.FileField(upload_to="bilgedice_images/", blank=True)
    is_user = models.BooleanField()

class PlayerState(models.Model):
    game = models.ForeignKey(Game, null=True, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, null=True, on_delete=models.CASCADE)
    hand = models.CharField(max_length=4, blank=True)
    qualifiers = models.CharField(max_length=2, blank=True)