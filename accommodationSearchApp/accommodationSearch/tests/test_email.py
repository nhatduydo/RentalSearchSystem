import asyncio

from accommodationSearch.email_service import EmailService
from django.test import TestCase


class EmailServiceTest(TestCase):
    async def test_send_notification(self):
        # Dữ liệu test
        test_data = {
            'name': 'Nguyễn Văn A',
            'title': 'Nhà trọ test',
            'address': '123 Đường Test, Quận 1, TP.HCM',
            'price': '2.500.000đ/tháng',
            'description': 'Nhà trọ mới, đầy đủ tiện nghi',
            'link': 'https://07ce-2402-800-6315-33d1-856d-dd01-361-2cbc.ngrok-free.app/motel/16'
        }

        # Email nhận test
        test_email = 'nhatduy242@gmail.com'  # Thay bằng email của bạn

        # Gửi email test
        result = await EmailService.send_notification(
            to_email=test_email,
            data=test_data,
            notification_type='NEW_MOTEL'
        )

        self.assertTrue(result, "Email should be sent successfully")


# Để chạy test thủ công
if __name__ == '__main__':
    test = EmailServiceTest()
    asyncio.run(test.test_send_notification())
