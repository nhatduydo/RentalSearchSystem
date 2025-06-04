import React, { useState, useEffect } from 'react';
import { View, Text, Button, StyleSheet, Alert, TouchableOpacity } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import axios, { endpoints } from '../configs/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BookingScreen = ({ route }) => {
  const { roomId } = route.params;

  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(new Date());
  const [showStartPicker, setShowStartPicker] = useState(false);
  const [showEndPicker, setShowEndPicker] = useState(false);
  const [bookingInfo, setBookingInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  const formatDate = (date) => date.toISOString().split('T')[0];

  const handleBooking = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('access_token');
      const res = await axios.post(
        endpoints['room-tenants'],
        {
          room: roomId,
          start_date: formatDate(startDate),
          end_date: formatDate(endDate),
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setBookingInfo(res.data);
      await AsyncStorage.setItem(`booking_room_${roomId}`, res.data.id.toString());
    } catch (err) {
      console.error('Đặt phòng thất bại:', err);
      Alert.alert('Lỗi', 'Không thể đặt phòng, vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    const fetchBookingInfo = async () => {
      try {
        const id = await AsyncStorage.getItem(`booking_room_${roomId}`);
        const token = await AsyncStorage.getItem('access_token');

        if (id) {
          const res = await axios.get(`${endpoints['room-tenants']}${id}/`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          setBookingInfo(res.data);
        }
      } catch (error) {
        console.error('Lỗi khi load lại thông tin đặt phòng:', error);
      }
    };

    fetchBookingInfo();
  }, []);


  return (
    <View style={styles.container}>
      <Text style={styles.title}>Chọn thời gian thuê</Text>

      <Text style={styles.label}>Ngày bắt đầu:</Text>
      <TouchableOpacity onPress={() => setShowStartPicker(true)} style={styles.dateBox}>
        <Text>{formatDate(startDate)}</Text>
      </TouchableOpacity>
      {showStartPicker && (
        <DateTimePicker
          value={startDate}
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowStartPicker(false);
            if (selectedDate) setStartDate(selectedDate);
          }}
        />
      )}

      <Text style={styles.label}>Ngày kết thúc:</Text>
      <TouchableOpacity onPress={() => setShowEndPicker(true)} style={styles.dateBox}>
        <Text>{formatDate(endDate)}</Text>
      </TouchableOpacity>
      {showEndPicker && (
        <DateTimePicker
          value={endDate}
          mode="date"
          display="default"
          onChange={(event, selectedDate) => {
            setShowEndPicker(false);
            if (selectedDate) setEndDate(selectedDate);
          }}
        />
      )}

      <View style={styles.button}>
        <Button title="Xác nhận đặt phòng" onPress={handleBooking} disabled={loading} />
      </View>

      {bookingInfo && (
        <View style={styles.infoBox}>
          <Text style={styles.sectionTitle}>Thông tin đặt phòng</Text>
          <Text><Text style={styles.label}>Người thuê:</Text> {bookingInfo.tenant.full_name} - {bookingInfo.tenant.phone}</Text>
          <Text><Text style={styles.label}>Phòng:</Text> {bookingInfo.room.room_name} - {Number(bookingInfo.room.price).toLocaleString()} VND</Text>
          <Text><Text style={styles.label}>Thời gian:</Text> {bookingInfo.start_date} → {bookingInfo.end_date}</Text>
          <Text><Text style={styles.label}>Trạng thái:</Text> {bookingInfo.status === 'PENDING' ? 'Chờ xác nhận' : bookingInfo.status}</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 16 },
  label: { fontWeight: '600', marginTop: 12 },
  dateBox: {
    padding: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 6,
    backgroundColor: '#f9f9f9',
    marginTop: 6,
  },
  button: { marginTop: 20 },
  infoBox: {
    width: '100%',
    backgroundColor: '#f9f9f9',
    borderColor: "lightblue",
    padding: 15,
    borderRadius: 10,
    marginVertical: 10,
    alignSelf: 'center',
    elevation: 1,
  },
  sectionTitle: {
    alignContent: 'center',
    fontWeight: 'bold',
    fontSize: 16,
    marginBottom: 10,
  },
});

export default BookingScreen;
