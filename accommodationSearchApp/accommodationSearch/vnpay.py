"""
Module tích hợp thanh toán VNPay
Cung cấp các phương thức để:
1. Tạo URL thanh toán với chữ ký bảo mật
2. Xác thực dữ liệu trả về từ VNPay
"""

import hashlib
import hmac
import urllib.parse


class vnpay:
    """
    Class xử lý tích hợp thanh toán VNPay
    - requestData: Dictionary chứa dữ liệu gửi đến VNPay
    - responseData: Dictionary chứa dữ liệu trả về từ VNPay
    """
    requestData = {}
    responseData = {}

    def get_payment_url(self, vnpay_payment_url, secret_key):
        """
        Tạo URL thanh toán VNPay với chữ ký bảo mật

        Quy trình:
        1. Sắp xếp các tham số theo thứ tự alphabet
        2. Tạo chuỗi query string từ các tham số
        3. Tạo chữ ký HMAC-SHA512
        4. Kết hợp URL gốc với query string và chữ ký

        Args:
            vnpay_payment_url: URL gốc của cổng thanh toán VNPay
            secret_key: Khóa bí mật để tạo chữ ký

        Returns:
            URL thanh toán đầy đủ với chữ ký bảo mật
        """
        # Sắp xếp các tham số theo thứ tự alphabet để đảm bảo tính nhất quán
        inputData = sorted(self.requestData.items())
        queryString = ''
        seq = 0
        # Tạo chuỗi query string từ các tham số
        for key, val in inputData:
            if seq == 1:
                queryString = queryString + "&" + key + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                queryString = key + '=' + urllib.parse.quote_plus(str(val))

        # Tạo chữ ký HMAC-SHA512
        hashValue = self.__hmacsha512(secret_key, queryString)
        # Kết hợp URL gốc với query string và chữ ký
        return vnpay_payment_url + "?" + queryString + '&vnp_SecureHash=' + hashValue

    def validate_response(self, secret_key):
        """
        Xác thực dữ liệu trả về từ VNPay

        Quy trình:
        1. Lấy chữ ký từ dữ liệu trả về
        2. Loại bỏ các tham số liên quan đến chữ ký
        3. Tạo lại chuỗi dữ liệu và chữ ký
        4. So sánh chữ ký nhận được với chữ ký tính toán

        Args:
            secret_key: Khóa bí mật để xác thực chữ ký

        Returns:
            True nếu chữ ký hợp lệ, False nếu không hợp lệ
        """
        # Lấy chữ ký từ dữ liệu trả về
        vnp_SecureHash = self.responseData['vnp_SecureHash']

        # Loại bỏ các tham số liên quan đến chữ ký
        if 'vnp_SecureHash' in self.responseData.keys():
            self.responseData.pop('vnp_SecureHash')

        if 'vnp_SecureHashType' in self.responseData.keys():
            self.responseData.pop('vnp_SecureHashType')

        # Sắp xếp và tạo chuỗi dữ liệu từ các tham số còn lại
        inputData = sorted(self.responseData.items())
        hasData = ''
        seq = 0 # seq: Dùng để biết khi nào thêm dấu &. Dòng đầu tiên thì không cần &, các dòng sau thì thêm.
        for key, val in inputData:
            # Chỉ xử lý các tham số bắt đầu bằng 'vnp_'
            #  Ghép các cặp key=value thành chuỗi hasData, phân cách bằng dấu &.
            if str(key).startswith('vnp_'):
                if seq == 1:
                    # urllib.parse.quote_plus(str(val)): Mã hóa URL giá trị (vd: dấu cách thành +, ký tự đặc biệt thành %XX).
                    hasData = hasData + "&" + str(key) + '=' + urllib.parse.quote_plus(str(val))
                else:
                    seq = 1
                    hasData = str(key) + '=' + urllib.parse.quote_plus(str(val))

        # Tạo lại chữ ký từ dữ liệu
        hashValue = self.__hmacsha512(secret_key, hasData)

        # In thông tin debug (có thể bỏ trong môi trường production)
        print(
            'Validate debug, HashData:' + hasData + "\n HashValue:" + hashValue + "\nInputHash:" + vnp_SecureHash)

        # So sánh chữ ký nhận được với chữ ký tính toán
        return vnp_SecureHash == hashValue

    @staticmethod
    def __hmacsha512(key, data):
        """
        Tạo chữ ký HMAC-SHA512

        Args:
            key: Khóa bí mật
            data: Dữ liệu cần tạo chữ ký

        Returns:
            Chuỗi chữ ký dạng hex
        """
        # Chuyển đổi key và data sang dạng bytes
        byteKey = key.encode('utf-8')
        byteData = data.encode('utf-8')
        # Tạo chữ ký HMAC-SHA512 và trả về dạng hex
        return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()
