import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, Alert, ActivityIndicator, StyleSheet
} from 'react-native';
import { WebView } from 'react-native-webview';
import axios, { endpoints } from '../configs/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';


const PaymentScreen = ({ route }) => {
  const { roomId } = route.params || {};
  const [selectedMethod, setSelectedMethod] = useState('CARD');
  const [paymentUrl, setPaymentUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cardNumber, setCardNumber] = useState('');
  const [cardHolder, setCardHolder] = useState('');
  const [roomPrice, setRoomPrice] = useState('');

  useEffect(() => {
    const loadUserAndRoom = async () => {
      try {
        const token = await AsyncStorage.getItem("access_token");
        const username = await AsyncStorage.getItem("username");
        const res = await axios.get(`${endpoints.tenants}${username}/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        console.log(username);
        setCardHolder(res.data.full_name || '');
        setCardNumber(res.data.bank_account || '');
      } catch (err) {
        console.error('Lỗi khi tải thông tin:', err);
        Alert.alert('Lỗi', 'Không thể tải thông tin người dùng hoặc phòng.');
      }
    };

    loadUserAndRoom();
  }, []);

  const handleVNPayPayment = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        Alert.alert("Lỗi", "Bạn chưa đăng nhập!");
        return;
      }
      const priceNumber = parseFloat(roomPrice);
      if (isNaN(priceNumber) || priceNumber <= 0) {
        Alert.alert("Lỗi", "Số tiền không hợp lệ.");
        return;
      }
      const paymentRes = await axios.post(endpoints.payments, {
        room: roomId,
        amount: priceNumber,
        payment_method: "VNPAY",
        status: "PENDING",
        description: "Thanh toan tien phong"
      }, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      const paymentId = paymentRes.data.id;
      const vnpayRes = await axios.post(`${endpoints.vnpay}create/`, {
        order_id: paymentId,
        amount: priceNumber
      }, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (vnpayRes.data.payment_url) {
        setPaymentUrl(vnpayRes.data.payment_url);
      } else {
        Alert.alert("Lỗi", "Không nhận được link thanh toán.");
      }
    } catch (err) {
      console.log('Chi tiết lỗi:', err.response?.data);
      Alert.alert('Lỗi thanh toán', JSON.stringify(err.response?.data, null, 2));
    } finally {
      setLoading(false);
    }
  };

  const onNavigationStateChange = (navState) => {
    if (navState.url.includes('/vnpay-return') && paymentUrl) {
      Alert.alert('Thông báo', 'Đã xử lý thanh toán, vui lòng kiểm tra');
      setPaymentUrl(null);
    }
  };


  const renderCardForm = () => (
    <View style={styles.form}>
      <TextInput
        placeholder="Số tài khoản"
        value={cardNumber}
        onChangeText={setCardNumber}
        style={styles.input}
        keyboardType="number-pad"
      />
      <TextInput
        placeholder="Tên tài khoản"
        value={cardHolder}
        onChangeText={setCardHolder}
        style={styles.input}
      />
      <TextInput
        placeholder="Nhập số tiền"
        value={roomPrice}
        onChangeText={setRoomPrice}
        style={styles.input}
      />
      <TouchableOpacity style={styles.button} onPress={() => Alert.alert('Success', 'Đã thanh toán thành công')}>
        <Text style={styles.buttonText}>Thanh Toán ngay</Text>
      </TouchableOpacity>
    </View>
  );

  const renderStripeWarning = () => (
    <Text style={{ fontSize: 16, color: 'gray', marginTop: 20 }}>
      Hiện chưa sử dụng được phương thức này, vui lòng thử các phương thức khác!
    </Text>
  );

  const renderVNPay = () => {
    if (loading) {
      return <ActivityIndicator size="large" color="deepskyblue" />;
    }
    return (
      <View>
        <View style={styles.form}>
          <View>
            <Text style={styles.input}>Thanh toán cho phòng: {roomId}</Text>
          </View>
          <TextInput
            placeholder="Nhập số tiền"
            value={roomPrice}
            onChangeText={setRoomPrice}
            style={styles.input}
          />
        </View>
        <TouchableOpacity style={styles.button} onPress={handleVNPayPayment}>
          <Text style={styles.buttonText}>Thanh toán với VNPay</Text>
        </TouchableOpacity>
      </View>

    );
  };

  return (
    <View style={{ flex: 1, padding: 20 }}>
      {paymentUrl ? (
        <WebView
          source={{ uri: paymentUrl }}
          style={{ flex: 1 }}
          startInLoadingState
          javaScriptEnabled
          onNavigationStateChange={onNavigationStateChange}
        />
      ) : (
        <>
          <View style={styles.tabs}>
            {['CARD', 'STRIPE', 'VNPAY'].map((method) => (
              <TouchableOpacity
                key={method}
                style={[
                  styles.tab,
                  selectedMethod === method && styles.tabSelected,
                ]}
                onPress={() => setSelectedMethod(method)}
              >
                <Text style={selectedMethod === method ? styles.tabTextSelected : styles.tabText}>
                  {method === 'CARD' ? 'Cards' : method}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          {selectedMethod === 'CARD' && renderCardForm()}
          {selectedMethod === 'STRIPE' && renderStripeWarning()}
          {selectedMethod === 'VNPAY' && renderVNPay()}
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  tabs: {
    flexDirection: 'row',
    marginBottom: 20,
    backgroundColor: '#eee',
    borderRadius: 10,
    overflow: 'hidden',
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
  },
  tabSelected: {
    backgroundColor: '#0d0d25',
  },
  tabText: {
    color: 'black',
  },
  tabTextSelected: {
    color: 'white',
    fontWeight: 'bold',
  },
  form: {},
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
  },
  button: {
    backgroundColor: '#3b5bff',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 5,
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});

export default PaymentScreen;
