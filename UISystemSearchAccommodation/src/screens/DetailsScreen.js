import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, ActivityIndicator, TouchableOpacity, Dimensions, Image, SafeAreaView } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import Modal from 'react-native-modal';
import Icon from 'react-native-vector-icons/MaterialIcons';
import CostGrid from '../components/CostGrid';
import CommentSection from '../components/CommentSection';
import axios, { endpoints } from '../configs/Apis';
import detailStyles from '../styles/detailStyles';
import { useNavigation } from '@react-navigation/native';

const DetailScreen = ({ route }) => {
  const { motel } = route.params;
  const [room, setRoom] = useState(null);
  const [allRooms, setAllRooms] = useState([]);
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isCommentVisible, setCommentVisible] = useState(false);
  const screenHeight = Dimensions.get('window').height;
  const navigation = useNavigation();

  const handleLandlordPress = () => {
    const landlordId = motel?.user.id;
    if (landlordId) {
      navigation.navigate('LandlordInfo', { landlordId });
    }
  };


  useEffect(() => {
    const fetchRooms = async () => {
      try {
        setLoading(true);

        const res = await axios.get(`${endpoints.rooms}?motel_id=${motel.id}`);
        const rooms = res.data.results;
        if (rooms.length === 0) return;

        let allImages = [];
        let url = endpoints['room-images'];
        while (url) {
          const resImg = await axios.get(url);
          allImages = [...allImages, ...resImg.data.results];
          url = resImg.data.next;
        }

        const roomsWithImages = rooms.map((room) => {
          const images = allImages
            .filter((img) => img.room === room.id)
            .map((img) => img.image_url);
          return { ...room, images };
        });

        setAllRooms(roomsWithImages);
        setRoom(roomsWithImages[0]);
        setSelectedRoomId(roomsWithImages[0].id);

      } catch (error) {
        console.error("Lỗi khi tải dữ liệu phòng và ảnh:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchRooms();
  }, [motel.id]);

  const handleRoomChange = (roomId) => {
    const selected = allRooms.find((r) => r.id === roomId);
    setSelectedRoomId(roomId);
    setRoom(selected);
  };

  if (loading) {
    return (
      <View style={detailStyles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  if (!room) {
    return (
      <View style={detailStyles.container}>
        <Text>Không có phòng nào cho nhà trọ này.</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }}>
      <View style={{ flex: 1 }}>
        <ScrollView style={{ backgroundColor: '#fff' }}>
          <ScrollView
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            style={detailStyles.scrollView}
            contentContainerStyle={{ padding: 0, margin: 0 }}
          >
            {room.images?.map((img, index) => (
              <Image key={index} source={{ uri: img }} style={detailStyles.carouselImage} />
            ))}
          </ScrollView>

          <View style={detailStyles.container}>
            <View style={detailStyles.infoBlock1}>
              <Text style={detailStyles.title}>{room.room_name}</Text>
              <Text style={detailStyles.price}>Giá: {parseInt(room.price).toLocaleString()} đ</Text>
            </View>

            <Text style={detailStyles.description}>Mô tả: {room.description}</Text>

            <View style={detailStyles.infoBlock1}>
              <Text>Diện tích: {room.area} m²</Text>
              <Text>Số người tối đa: {room.max_people}</Text>
            </View>

            <CostGrid amenities={room.amenities_display || []} />
          </View>
        </ScrollView>
        <TouchableOpacity onPress={handleLandlordPress} style={{ flexDirection: 'row', alignItems: 'center', padding: 16 }}>
          <Image
            source={{ uri: motel.user.avatar }}
            style={{ width: 40, height: 40, borderRadius: 20, marginRight: 10 }}
          />
          <Text style={{ fontWeight: 'bold', fontSize: 16 }}>
            {motel.user.first_name} {motel.user.last_name}
          </Text>
        </TouchableOpacity>


        <View style={{ marginBottom: 6, padding: 16 }}>
          <Text style={{ fontWeight: 'bold', marginBottom: 4 }}>Chọn phòng:</Text>
          <View
            style={{
              borderWidth: 1,
              borderColor: '#ccc',
              borderRadius: 8,
              overflow: 'hidden',
              height: 50,
              justifyContent: 'center',
            }}
          >
            <Picker
              selectedValue={selectedRoomId}
              onValueChange={handleRoomChange}
              style={{ fontSize: 14 }}
              dropdownIconColor="#888"
              mode="dropdown"
            >
              {allRooms.map((r) => (
                <Picker.Item key={r.id} label={r.room_name} value={r.id} />
              ))}
            </Picker>
          </View>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', padding: 16, borderTopWidth: 1, borderColor: '#ccc', backgroundColor: '#fff', marginBottom: 6 }}>
          <TouchableOpacity style={[detailStyles.button, { flex: 1 }]}>
            <Text style={detailStyles.buttonText}>Đặt lịch xem phòng</Text>
          </TouchableOpacity>

          <TouchableOpacity style={{ alignItems: 'center', marginLeft: 12 }}>
            <Icon name="chat" size={20} color="#007AFF" />
            <Text style={{ fontSize: 12, color: 'gray', marginTop: 4 }}>Chat ngay</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={{ alignItems: 'center', marginLeft: 12 }}
            onPress={() => setCommentVisible(true)}
          >
            <Icon name="chat" size={20} color="#007AFF" />
            <Text style={{ fontSize: 12, color: 'gray', marginTop: 4 }}>Bình luận</Text>
          </TouchableOpacity>
        </View>
      </View>

      <Modal
        isVisible={isCommentVisible}
        onBackdropPress={() => setCommentVisible(false)}
        style={{ justifyContent: 'flex-end', margin: 0 }}
      >
        <View
          style={{
            height: screenHeight * 0.75,
            backgroundColor: '#fff',
            borderTopLeftRadius: 16,
            borderTopRightRadius: 16,
            padding: 16,
          }}
        >
          <CommentSection roomId={room.id} />
        </View>
      </Modal>
    </SafeAreaView>
  );
};

export default DetailScreen;
