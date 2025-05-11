import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import detailStyles from '../styles/detailStyles';
import axios, { endpoints } from '../configs/Apis';

const DetailScreen = ({ route }) => {
  const { motel } = route.params;
  const [room, setRoom] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFirstRoom = async () => {
      try {
        const res = await axios.get(endpoints.rooms);
        const rooms = res.data.results.filter(rm => rm.motel === motel.id);
        if (rooms.length > 0) {
          setRoom(rooms[0]);
        }
      } catch (error) {
        console.error("Lỗi lấy phòng trọ:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchFirstRoom();
  }, [motel.id]);

  return (
    <ScrollView style={detailStyles.container}>
      {/* <ScrollView horizontal pagingEnabled showsHorizontalScrollIndicator style={detailStyles.scrollView}>
        {room.images?.map((img, index) => (
          <Image key={index} source={{ uri: img }} style={detailStyles.carouselImage} />
        ))}
      </ScrollView> */}

      <Text style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 10 }}>
        {motel.motel_name}
      </Text>

      {loading ? (
        <ActivityIndicator size="large" color="deepskyblue" />
      ) : room ? (
        <View style={detailStyles.info}>
          <Text style={detailStyles.title}>{room.room_name}</Text>
          <Text style={detailStyles.price}>Giá: {room.price.toLocaleString()} VNĐ</Text>
          <Text style={detailStyles.location}>Diện tích: {room.area} m²</Text>
          <Text style={detailStyles.details}>{room.description}</Text>
          {/* <Text style={detailStyles.total}>{room.total}</Text> //tong so phong */}

          {/* <View style={detailStyles.costGrid}>
            {costItems.map((item, index) => (
              <View key={index} style={detailStyles.costCell}>
                <Text style={detailStyles.costLabel}>{item.label}</Text>
                <Text style={detailStyles.costValue}>
                  {item.value.toLocaleString()}
                </Text>
                <Text style={detailStyles.costUnit}>/{item.unit}</Text>
              </View>
            ))}
          </View> */}
        </View>
      ) : (
        <Text>Không có phòng nào trong nhà trọ này.</Text>
      )}

      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', margin: 16 }}>
        <TouchableOpacity style={detailStyles.button}>
          <Text style={detailStyles.buttonText}>Đặt lịch xem phòng</Text>
        </TouchableOpacity>
        <TouchableOpacity style={{ alignItems: 'center', marginLeft: 12 }}>
          <Icon name="chat" size={20} color="#007AFF" />
          <Text style={{ fontSize: 12, color: 'gray', marginTop: 4 }}>Chat ngay</Text>
        </TouchableOpacity>
        <TouchableOpacity style={{ alignItems: 'center', marginLeft: 12 }}>
          <Icon name="chat" size={20} color="#007AFF" />
          <Text style={{ fontSize: 12, color: 'gray', marginTop: 4 }}>Bình luận</Text>
        </TouchableOpacity>
        
      </View>
    </ScrollView>
  );
};

export default DetailScreen;
