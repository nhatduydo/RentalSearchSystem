import React, { useState } from 'react';
import { View, Text, Button, Alert, ActivityIndicator } from 'react-native';
import axios, { endpoints } from '../configs/Apis';
import { WebView } from 'react-native-webview';

const PaymentScreen = () => {
    const [paymentUrl, setPaymentUrl] = useState(null);
    const [loading, setLoading] = useState(false);

    const handlePayment = async () => {
        try {
            setLoading(true);
            const res = await axios.post(endpoints['payments-checkout'], {
                user_id: 1,
                room_id: 5,
                amount: 100000,
                payment_method: 'vnpay'
            });

            if (res.data.payment_url) {
                setPaymentUrl(res.data.payment_url);
            }

        } catch (err) {
            Alert.alert('Lỗi thanh toán', 'Không thể tạo yêu cầu thanh toán.');
        } finally {
            setLoading(false);
        }
    };

    const onNavigationStateChange = (navState) => {
        if (navState.url.includes('/vnpay-return')) {
            Alert.alert('Thông báo', 'Đã xử lý thanh toán, vui lòng kiểm tra');
            setPaymentUrl(null);
        }
    };

    if (paymentUrl) {
        return (
            <WebView
                source={{ uri: paymentUrl }}
                onNavigationStateChange={onNavigationStateChange}
            />
        );
    }

    return (
        <View style={{ padding: 20 }}>
            <Text style={{ fontSize: 18, marginBottom: 20 }}>
                Tổng tiền: 100.000 VNĐ
            </Text>
            {loading ? (
                <ActivityIndicator color="deepskyblue" size="large" />
            ) : (
                <Button title="Thanh toán với VNPay" onPress={handlePayment} />
            )}
        </View>
    );
};

export default PaymentScreen;
