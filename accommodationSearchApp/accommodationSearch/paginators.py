# Import class PageNumberPagination từ Django REST framework
# Đây là class cơ sở để thực hiện phân trang theo số trang
from rest_framework.pagination import PageNumberPagination


class ItemPanigator(PageNumberPagination):
    """
    Custom paginator class cho việc phân trang các items
    Kế thừa từ PageNumberPagination của Django REST framework

    Attributes:
        page_size: Số lượng items mặc định trên mỗi trang
        page_size_query_param: Tên tham số trong URL để client có thể chỉ định số lượng items trên trang
        max_page_size: Số lượng items tối đa cho phép trên mỗi trang
    """
    page_size = 6  # Mặc định hiển thị 6 items trên mỗi trang
    page_size_query_param = 'page_size'  # Cho phép client chỉ định số lượng items qua tham số 'page_size' trong URL
    max_page_size = 50  # Giới hạn tối đa 50 items trên mỗi trang để tránh quá tải
