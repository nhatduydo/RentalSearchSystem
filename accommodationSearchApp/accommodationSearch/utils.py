from math import atan2, cos, radians, sin, sqrt


def calculate_distance(latitude1, longitude1, latitude2, longitude2):
    """
    Tính khoảng cách giữa hai điểm trên bề mặt Trái Đất sử dụng công thức Haversine

    Args:
        latitude1 (float): Vĩ độ của điểm thứ nhất (độ)
        longitude1 (float): Kinh độ của điểm thứ nhất (độ)
        latitude2 (float): Vĩ độ của điểm thứ hai (độ)
        longitude2 (float): Kinh độ của điểm thứ hai (độ)

    Returns:
        float: Khoảng cách giữa hai điểm tính bằng kilomet

    Note:
        Công thức Haversine được sử dụng để tính khoảng cách giữa hai điểm trên bề mặt cầu
        (Trái Đất) dựa trên tọa độ vĩ độ và kinh độ của chúng.
        Công thức này tính toán khoảng cách theo đường chim bay (great-circle distance).
    """
    # Chuyển đổi tọa độ từ độ sang radian vì các hàm lượng giác trong Python sử dụng radian
    latitude1, longitude1, latitude2, longitude2 = map(radians, [latitude1, longitude1, latitude2, longitude2])

    # Áp dụng công thức Haversine để tính khoảng cách
    # 1. Tính chênh lệch vĩ độ và kinh độ
    dlatitude = latitude2 - latitude1
    dlongitude = longitude2 - longitude1

    # 2. Tính a theo công thức Haversine
    # a = sin²(Δφ/2) + cos(φ1)·cos(φ2)·sin²(Δλ/2)
    a = sin(dlatitude/2)**2 + cos(latitude1) * cos(latitude2) * sin(dlongitude/2)**2

    # 3. Tính c theo công thức Haversine
    # c = 2·atan2(√a, √(1−a))
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    # 4. Tính khoảng cách cuối cùng
    # distance = R·c, với R là bán kính Trái Đất (6371 km)
    distance = 6371 * c

    return distance
