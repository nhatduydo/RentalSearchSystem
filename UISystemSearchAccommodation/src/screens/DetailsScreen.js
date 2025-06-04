import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, ActivityIndicator, TouchableOpacity, Dimensions, Image, SafeAreaView, Button } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import Modal from 'react-native-modal';
import { Ionicons } from '@expo/vector-icons';
import CostGrid from '../components/CostGrid';
import CommentSection from '../components/CommentSection';
import axios, { endpoints } from '../configs/Apis';
import detailStyles from '../styles/detailStyles';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const DetailScreen = ({ route }) => {
  const { motel } = route.params;
  const [room, setRoom] = useState(null);
  const [allRooms, setAllRooms] = useState([]);
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isCommentVisible, setCommentVisible] = useState(false);
  const [motelRatings, setMotelRatings] = useState([]);
  const [averageRating, setAverageRating] = useState(null);
  const [showComments, setShowComments] = useState(false);
  const [isFollowed, setIsFollowed] = useState(false);
  const [userId, setUserId] = useState(null);
  const [followId, setFollowId] = useState(null);
  const [isFavorited, setIsFavorited] = useState(false);

  const screenHeight = Dimensions.get('window').height;
  const navigation = useNavigation();

  const handleLandlordPress = () => {
    const landlordId = motel?.user.id;
    if (landlordId) {
      navigation.navigate('LandlordInfo', { landlordId });
    }
  };
  const fetchMotelRatings = async () => {
    try {
      const res = await axios.get(`${endpoints["motelRatings"]}?motel_id=${motel.id}`);
      setMotelRatings(res.data.results);

      if (res.data.results.length > 0) {
        const total = res.data.results.reduce((sum, r) => sum + r.rating, 0);
        const avg = total / res.data.results.length;
        setAverageRating(avg.toFixed(1));
      } else {
        setAverageRating("Chưa có đánh giá");
      }
    } catch (error) {
      console.error("Lỗi khi tải đánh giá nhà trọ:", error);
    }
  };

  const fetchRooms = async () => {
    try {
      setLoading(true);

      const res = await axios.get(`${endpoints.rooms}?motel_id=${motel.id}`);
      const rooms = res.data.results;
      //console.log('room -->', rooms);
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
      //console.log("roomWithImages:", roomsWithImages);

      setAllRooms(roomsWithImages);
      setRoom(roomsWithImages[0]);
      setSelectedRoomId(roomsWithImages[0].id);

    } catch (error) {
      console.error("Lỗi khi tải dữ liệu phòng và ảnh:", error);
    } finally {
      setLoading(false);
    }
  };




  const handleRoomChange = (roomId) => {
    const selected = allRooms.find((r) => r.id === roomId);
    setSelectedRoomId(roomId);
    setRoom(selected);
  };

  const getUserId = async () => {
    try {
      const token = await AsyncStorage.getItem("access_token");
      const username = await AsyncStorage.getItem("username");
      if (!token || !username) return null;

      const res = await axios.get(`/users/${username}/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      return res.data.id;
    } catch (error) {
      console.error("Lỗi khi lấy userId:", error);
      return null;
    }
  };
  const checkFollowStatus = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const uid = await getUserId();
      setUserId(uid);

      const res = await axios.get(endpoints.follows, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const follows = res.data.results || [];

      const foundFollow = follows.find(
        (follow) => follow.followed_user?.id === motel.user.id
      );

      setIsFollowed(!!foundFollow);
      setFollowId(foundFollow?.id || null);
    } catch (error) {
      console.error("Lỗi khi kiểm tra follow:", error);
    }
  };


  const handleFollowToggle = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');

      if (isFollowed) {
        // UNFOLLOW
        if (!followId) return;

        await axios.delete(`${endpoints.follows}${followId}/`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        setIsFollowed(false);
        setFollowId(null);
      } else {
        // FOLLOW
        const res = await axios.post(
          endpoints.follows,
          { followed_user_id: motel.user.id },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        setIsFollowed(true);
        setFollowId(res.data.id);
      }
    } catch (error) {
      console.error("Lỗi khi xử lý follow:", error);
    }
  };


  const goToChat = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) return alert("Không tìm thấy token");

      const userId = await getUserId();
      if (!userId) return alert("Không lấy được userId");

      const landlordId = motel.user.id;
      const savedRoomId = await AsyncStorage.getItem(`chat_room_${landlordId}`);

      if (savedRoomId) {
        try {
          const res = await axios.get(
            `${endpoints['chat-rooms']}${savedRoomId}/`,
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );

          const participants = res.data.participants.map(p => p.id);
          const isValidRoom =
            participants.includes(userId) && participants.includes(landlordId);

          console.log("userID-->", userId);

          if (isValidRoom) {
            return navigation.navigate('Chat', {
              roomId: savedRoomId,
              userId: userId,
              token: token,
              partner: {
                id: motel.user.id,
                firstName: motel.user.first_name,
                lastName: motel.user.last_name,
                avatar: motel.user.avatar,
              }
            });
          }
        } catch (err) {
          console.log("Room không hợp lệ hoặc đã bị xóa:", err);
        }
      }

      const res = await axios.post(
        endpoints['chat-rooms'],
        { participants: [userId, landlordId] },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const newRoomId = res.data.id;
      await AsyncStorage.setItem(`chat_room_${landlordId}`, newRoomId.toString());

      navigation.navigate('Chat', {
        roomId: newRoomId,
        token: token,
      });

    } catch (err) {
      console.error("Lỗi khi tạo hoặc truy cập phòng chat:", err);
    }
  };

  const toggleFavorite = async () => {
    try {
      const token = await AsyncStorage.getItem("access_token");
      //console.log("motelID-->", motel.id);
      //console.log("token-->", token);
      const res = await axios.post(`${endpoints.motels}${motel.id}/favorite/`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      //console.log("res-->", res);
      setIsFavorited(res.data.favorite);
    } catch (error) {
      console.error('Lỗi yêu thích:', error);
    }
  };

  useEffect(() => {
    fetchMotelRatings();
    fetchRooms();
    checkFollowStatus();
  }, [motel.id]);


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
            <TouchableOpacity onPress={() => setShowComments(!showComments)}>
              <Text style={{ fontWeight: 'bold', fontSize: 16, marginBottom: 8 }}>
                Đánh giá nhà trọ {showComments ? '▲' : '▼'}
              </Text>
            </TouchableOpacity>

            {showComments && (
              <>
                {averageRating ? (
                  <Text style={{ marginBottom: 4 }}>⭐ {averageRating} / 5 từ {motelRatings.length} đánh giá</Text>
                ) : (
                  <Text>Chưa có đánh giá nào</Text>
                )}

                {motelRatings.slice(0, 2).map((r) => (
                  <View key={r.id} style={{ marginTop: 8, padding: 8, borderWidth: 1, borderColor: '#ccc', borderRadius: 8 }}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
                      <Image source={{ uri: r.user.avatar }} style={{ width: 24, height: 24, borderRadius: 12, marginRight: 6 }} />
                      <Text style={{ fontWeight: 'bold' }}>{r.user.first_name} {r.user.last_name}</Text>
                    </View>
                    <Text>⭐ {r.rating} / 5</Text>
                    <Text style={{ color: '#555' }}>{r.comment}</Text>
                  </View>
                ))}
              </>
            )}

            <CostGrid amenities={room.amenities_display || []} />
          </View>

          <View style={detailStyles.container}>
            <Text style={detailStyles.description}><Text style={{ fontWeight: 'bold' }}>Mô tả:</Text> {room.description}</Text>
            <View style={detailStyles.infoBlock2}>
              <Text>Diện tích: {room.area} m²</Text>
              <Text>Số người tối đa: {room.max_people}</Text>
            </View>
          </View>
        </ScrollView>
        <TouchableOpacity onPress={handleLandlordPress} style={{ flexDirection: 'row', alignItems: 'center', padding: 16, backgroundColor: 'lightblue' }}>
          <Image
            source={{ uri: motel.user.avatar }}
            style={{ width: 40, height: 40, borderRadius: 20, marginRight: 10 }}
          />
          <Text style={{ fontWeight: 'bold', fontSize: 16 }}>
            {motel.user.first_name} {motel.user.last_name}
          </Text>
          <TouchableOpacity
            onPress={handleFollowToggle}
            style={{
              paddingHorizontal: 12,
              paddingVertical: 12,
              backgroundColor: 'lightblue',
              borderRadius: 20,
              marginHorizontal: 5,
            }}
          >
            <Ionicons
              name={isFollowed ? "bookmarks" : "bookmarks-outline"}
              size={20}
              color={isFollowed ? "#FF9500" : "#007AFF"}
            />
          </TouchableOpacity>

        </TouchableOpacity>


        <View style={{ marginBottom: 6, padding: 16 }}>
          <Text style={{ fontWeight: 'bold', marginBottom: 4 }}>Chọn phòng:</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 10 }}>
            <View style={{
              borderWidth: 1,
              borderColor: '#ccc',
              borderRadius: 8,
              overflow: 'hidden',
              height: 50,
              flex: 1,
              justifyContent: 'center',
              marginRight: 8
            }}>
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

            <TouchableOpacity
              onPress={toggleFavorite}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 12,
                backgroundColor: 'lightblue',
                borderRadius: 20,
                marginHorizontal: 5,
              }}
            >
              <Ionicons
                name={isFavorited ? "heart" : "heart-outline"}
                size={20}
                color={isFavorited ? "#DD0000" : "#222222"}
              />
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => navigation.navigate('Map', {
                latitude: motel.latitude,
                longitude: motel.longitude,
                motelName: motel.motel_name
              })}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 12,
                backgroundColor: 'lightblue',
                borderRadius: 20
              }}
            >
              <Ionicons name="map-outline" size={20} color="#007AFF" />
            </TouchableOpacity>
          </View>
        </View>

        <View style={{ flexDirection: 'row', alignItems: 'center', padding: 16, borderTopWidth: 1, borderColor: '#ccc', backgroundColor: '#fff', marginBottom: 6 }}>
          <TouchableOpacity style={[detailStyles.button, { flex: 1 }]} onPress={() => navigation.navigate('PaymentBooking', { roomId: room.id })}>
            <Text style={detailStyles.buttonText}>Thanh toán / Đặt phòng</Text>
          </TouchableOpacity>

          <TouchableOpacity style={{ alignItems: 'center', marginLeft: 12 }} onPress={goToChat}>
            <Ionicons name="chatbox-ellipses-outline" size={20} color="#007AFF" />
            <Text style={{ fontSize: 12, color: 'gray', marginTop: 4 }}>Chat ngay</Text>
          </TouchableOpacity>

          {/* <TouchableOpacity
            style={{ alignItems: 'center', marginLeft: 12 }}
            onPress={() => setCommentVisible(true)}
          >
            <Ionicons name="chatbubble-ellipses-outline" size={20} color="#007AFF" />
            <Text style={{ fontSize: 12, color: 'gray', marginTop: 4 }}>Bình luận</Text>
          </TouchableOpacity> */}
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
