from math import atan2, cos, radians, sin, sqrt


def calculate_distance(latitude1, longitude1, latitude2, longitude2):
    """
    Tính khoảng cách giữa hai điểm trên bề mặt Trái Đất sử dụng công thức Haversine
    """
    latitude1, longitude1, latitude2, longitude2 = map(radians, [latitude1, longitude1, latitude2, longitude2])

    dlatitude = latitude2 - latitude1
    dlongitude = longitude2 - longitude1
    a = sin(dlatitude/2)**2 + cos(latitude1) * cos(latitude2) * sin(dlongitude/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = 6371 * c

    return distance
