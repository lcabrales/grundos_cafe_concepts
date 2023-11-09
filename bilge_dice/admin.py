from django.contrib import admin
from bilge_dice.models import User, Player

class UserAdmin(admin.ModelAdmin):
    pass

class PlayerAdmin(admin.ModelAdmin):
    pass

admin.site.register(User, UserAdmin)
admin.site.register(Player, PlayerAdmin)
