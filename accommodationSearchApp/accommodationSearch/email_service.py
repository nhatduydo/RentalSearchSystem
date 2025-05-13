import asyncio
from functools import partial

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, Email, Mail


class EmailService:
    @staticmethod
    async def send_notification(to_email, data, notification_type='NEW_MOTEL'):
        try:
            # Khởi tạo SendGrid client với API key
            sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

            # Tạo nội dung email dựa trên loại thông báo
            subject, html_content = EmailService._get_email_content(notification_type, data)

            # Tạo đối tượng email
            message = Mail(
                from_email=Email(settings.SENDER_EMAIL, settings.SENDER_NAME),
                to_emails=to_email,
                subject=subject,
                html_content=Content('text/html', html_content)
            )

            # Gửi email bất đồng bộ
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: sg.send(message))

            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.body}")
            print(f"Response Headers: {response.headers}")

            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    @staticmethod
    def _get_email_content(notification_type, data):
        if notification_type == 'NEW_MOTEL':
            return (
                'Thông báo nhà trọ mới',
                f'''
                <h2>Thông báo nhà trọ mới</h2>
                <p>Xin chào {data.get('name', '')},</p>
                <p>Có nhà trọ mới phù hợp với bạn:</p>
                <p><strong>Tên:</strong> {data.get('title', '')}</p>
                <p><strong>Địa chỉ:</strong> {data.get('address', '')}</p>
                <p><strong>Quận/Huyện:</strong> {data.get('district', '')}</p>
                <p><strong>Thành phố:</strong> {data.get('city', '')}</p>
                <p><strong>Tỉnh/Thành:</strong> {data.get('province', '')}</p>
                <p><strong>Tổng số phòng:</strong> {data.get('total_rooms', '')}</p>
                <p><strong>Số phòng còn trống:</strong> {data.get('available_rooms', '')}</p>
                <p><strong>Mô tả:</strong> {data.get('description', '')}</p>
                <p><strong>Vị trí:</strong> {data.get('latitude', '')}, {data.get('longitude', '')}</p>
                '''
            )
        elif notification_type == 'MOTEL_UPDATE':
            return (
                'Cập nhật thông tin nhà trọ',
                f'''
                <h2>Cập nhật thông tin nhà trọ</h2>
                <p>Xin chào {data.get('name', '')},</p>
                <p>Nhà trọ bạn đang theo dõi đã được cập nhật:</p>
                <p><strong>Tên:</strong> {data.get('title', '')}</p>
                <p><strong>Địa chỉ:</strong> {data.get('address', '')}</p>
                <p><strong>Quận/Huyện:</strong> {data.get('district', '')}</p>
                <p><strong>Thành phố:</strong> {data.get('city', '')}</p>
                <p><strong>Tỉnh/Thành:</strong> {data.get('province', '')}</p>
                <p><strong>Tổng số phòng:</strong> {data.get('total_rooms', '')}</p>
                <p><strong>Số phòng còn trống:</strong> {data.get('available_rooms', '')}</p>
                <p><strong>Mô tả:</strong> {data.get('description', '')}</p>
                <p><strong>Vị trí:</strong> {data.get('latitude', '')}, {data.get('longitude', '')}</p>
                '''
            )
        else:
            return (
                'Thông báo từ hệ thống',
                f'''
                <h2>Thông báo</h2>
                <p>Xin chào {data.get('name', '')},</p>
                <p>{data.get('message', '')}</p>
                '''
            )
