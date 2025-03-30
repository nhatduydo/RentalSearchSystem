from django.http import HttpResponse
from django.shortcuts import redirect, render
import cloudinary.uploader
from .models import Motel, MotelImage


def index(request):
    return HttpResponse("HỆ THỐNG HỖ TRỢ TÌM KIẾM NHÀ TRỌ")

# def upload_motel_images(request, motel_id):
#     motel = Motel.objects.get(id=motel_id)

#     if request.method == 'POST':
#         form = MotelImageForm(request.POST, request.FILES)
#         if form.is_valid():
#             images = request.FILES.getlist('images')  # Lấy danh sách ảnh tải lên
#             for image in images:
#                 MotelImage.objects.create(motel=motel, image_url=image, image_type="default")  
#             return redirect('success_url')  # Chuyển hướng sau khi upload thành công
#     else:
#         form = MotelImageForm()

#     return render(request, 'upload_images.html', {'form': form, 'motel': motel})
