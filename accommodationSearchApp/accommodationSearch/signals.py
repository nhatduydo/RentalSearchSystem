from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accommodationSearch.models import Motel, Room, MotelImage, RoomImage

@receiver([post_save, post_delete], sender = MotelImage)
def update_motel_verification(sender, instance, **kwargs):
    motel = instance.motel
    print(f"Instance motel: {instance.motel}")
    motel.check_verification()
    
@receiver([post_save, post_delete], sender = RoomImage)
def update_motel_verification(sender, instance, **kwargs):
    room = instance.room
    print(f"Instance motel: {instance.room}")
    room.check_verification()