import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, Image, TouchableOpacity, Alert } from 'react-native';
import { useNavigation, useIsFocused } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { endpoints } from '../configs/Apis';
import Icon from 'react-native-vector-icons/AntDesign';
import { Menu, Provider } from 'react-native-paper';
import profileStyle from '../styles/profileStyle';
import landlordProfileStyle from '../styles/landlordProfileStyle';

import ListCard from '../components/ListCard';
import PostCard from '../components/PostCard';
import { Ionicons } from '@expo/vector-icons';

const ProfileScreen = () => {
  const [user, setUser] = useState(null);
  const [hostels, setHostels] = useState([]);
  const [posts, setPosts] = useState([]);
  const [menuVisible, setMenuVisible] = useState(false);
  const [loading, setLoading] = useState(true);

  const navigation = useNavigation();
  const isFocused = useIsFocused();

  const openMenu = () => setMenuVisible(true);
  const closeMenu = () => setMenuVisible(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const token = await AsyncStorage.getItem('access_token');
        const username = await AsyncStorage.getItem('username');
        if (!token || !username) return;

        let allUsers = [];
        let url = endpoints.users;
        while (url) {
          const res = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } });
          allUsers = [...allUsers, ...res.data.results];
          url = res.data.next;
        }

        const findUser = allUsers.find(u => u.username === username);
        if (!findUser) return;

        const userId = findUser.id;
        // console.log(userId)

        let tenants = [];
        let tenantUrl = endpoints.tenants;
        while (tenantUrl) {
          const res = await axios.get(tenantUrl, { headers: { Authorization: `Bearer ${token}` } });
          tenants = [...tenants, ...res.data.results];
          tenantUrl = res.data.next;
        }
        const matchedTenant = tenants.find(t => t.user === userId);


        let landlords = [];
        let landlordUrl = endpoints.landlords;
        while (landlordUrl) {
          const res = await axios.get(landlordUrl, { headers: { Authorization: `Bearer ${token}` } });
          landlords = [...landlords, ...res.data.results];
          landlordUrl = res.data.next;
        }
        const matchedLandlord = landlords.find(l => l.user === userId);
        setUser({ ...findUser, landlordInfo: matchedLandlord, tenantInfo: matchedTenant });

        let allHostels = [];
        let motelUrl = `${endpoints.motels}?user=${userId}`;
        while (motelUrl) {
          const res = await axios.get(motelUrl, {
            headers: { Authorization: `Bearer ${token}` }
          });
          allHostels = [...allHostels, ...res.data.results];
          motelUrl = res.data.next;
        }
        const myHostels = allHostels.filter(m => Number(m.user.id) === Number(userId));
        setHostels(myHostels);

        let allPosts = [];
        let postUrl = `${endpoints.posts}?user=${userId}`;
        while (postUrl) {
          const res = await axios.get(postUrl, {
            headers: { Authorization: `Bearer ${token}` }
          });
          allPosts = [...allPosts, ...res.data.results];
          postUrl = res.data.next;
        }
        const myPosts = allPosts.filter(p => Number(p.user.id) === Number(userId));
        setPosts(myPosts);

      } catch (error) {
        console.error("Lỗi khi tải dữ liệu:", error);
      } finally {
        setLoading(false);
      }
    };

    if (isFocused) {
      loadData();
    }
  }, [isFocused]);

  const handleLogout = async () => {
    Alert.alert('Xác nhận', 'Bạn có chắc chắn muốn đăng xuất?', [
      { text: 'Hủy', style: 'cancel' },
      {
        text: 'Đăng xuất',
        style: 'destructive',
        onPress: async () => {
          await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'username']);
          setUser(null);
        }
      }
    ]);
  };
  const goToChatWithTenant = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const username = await AsyncStorage.getItem("username");
      if (!token || !username) return alert("Không có thông tin đăng nhập");

      const resUser = await axios.get(`/users/${username}/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const landlordId = resUser.data.id;

      const resRooms = await axios.get(`/chat-rooms/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      let room = null;

      for (const r of resRooms.data.results) {
        for (const participant of r.participants) {
          if (participant.id === landlordId) {
            room = r;
            break;
          }
        }
        if (room) break;
      }
      console.log(room);


      let roomId;
      if (room) {
        roomId = room.id;
      } else {
        Alert.alert("Thông báo", "Không tìm thấy phòng chat với người thuê.");
        return;
      }

      navigation.navigate('Chat', {
        roomId: roomId,
        userId: landlordId,
        token: token
      });

    } catch (err) {
      console.error("Lỗi khi vào phòng chat:", err);
      Alert.alert("Lỗi", "Không thể vào phòng chat.");
    }
  };


  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <Text>Đang tải dữ liệu...</Text>
      </View>
    );
  }

  return loading ? (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <Text style={{ textAlign: 'center' }}>Đang tải thông tin...</Text>
    </View>
  ) : (<Provider>
    <ScrollView>
      {!user ? (
        <View style={profileStyle.container}>
          <Image
            source={require('../assets/images/room.jpg')}
            style={profileStyle.image}
            resizeMode="contain"
          />
          <Text style={profileStyle.title}>Chào mừng đến với</Text>
          <Text style={profileStyle.subtitle}>Tìm Kiếm Nhà Trọ</Text>
          <Text style={profileStyle.description}>
            Hệ thống tìm kiếm nhà trọ tốt nhất!
          </Text>
          <TouchableOpacity style={profileStyle.loginButton} onPress={() => navigation.navigate('SignIn')}>
            <Text style={profileStyle.loginText}>Đăng nhập</Text>
          </TouchableOpacity>
          <TouchableOpacity style={profileStyle.registerButton} onPress={() => navigation.navigate('SignUp')}>
            <Text style={profileStyle.registerText}>Đăng ký</Text>
          </TouchableOpacity>
        </View>
      ) : user.landlordInfo ? (
        <ScrollView contentContainerStyle={{ alignItems: 'center', justifyContent: 'center' }}>
          <View style={landlordProfileStyle.landlordProfileHeader}>
            <View style={landlordProfileStyle.landlordProfileTopBar}>
              <TouchableOpacity onPress={goToChatWithTenant}>
                <Icon name="message1" size={24} color="#000" style={{ marginRight: 16 }} />
              </TouchableOpacity>
              <View style={{ flexDirection: 'row', justifyContent: 'flex-end' }}>
                <Menu
                  visible={menuVisible}
                  onDismiss={closeMenu}
                  anchor={
                    <TouchableOpacity onPress={openMenu}>
                      <Icon name="setting" size={24} color="#000" />
                    </TouchableOpacity>
                  }
                >
                  <Menu.Item
                    onPress={() => {
                      navigation.navigate('EditProfile', { user });
                      closeMenu();
                    }}
                    title="Thông tin cá nhân"
                  />

                  <Menu.Item
                    onPress={handleLogout}
                    title="Đăng xuất"
                  />
                </Menu>
              </View>
            </View>

            <View style={landlordProfileStyle.landlordProfileInfo}>
              {user?.avatar && (
                <Image source={{ uri: user.avatar }} style={landlordProfileStyle.landlordAvatar} />
              )}
              <Text style={landlordProfileStyle.landlordName}>{user.landlordInfo.full_name}</Text>
              <Text style={landlordProfileStyle.landlordEmail}>{user.email}</Text>
            </View>
          </View>

          <View style={landlordProfileStyle.landlordInfoBox}>
            <Text style={landlordProfileStyle.landlordSectionTitle}>Danh sách nhà trọ</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={landlordProfileStyle.horizontalScrollContainer}>
              {hostels.map(motel => (
                <ListCard key={motel.id} room={motel} />
              ))}
            </ScrollView>
          </View>

          <View style={landlordProfileStyle.landlordInfoBox}>
            <Text style={landlordProfileStyle.landlordSectionTitle}>Bài đăng của bạn</Text>
            <ScrollView contentContainerStyle={landlordProfileStyle.horizontalScrollContainer}>
              {posts.map(post => (
                <PostCard key={post.id} post={post} />
              ))}
            </ScrollView>
          </View>

        </ScrollView>) : user.tenantInfo ? (
          <ScrollView contentContainerStyle={{ alignItems: 'center', justifyContent: 'center' }}>
            <View style={landlordProfileStyle.landlordProfileHeader}>
              <View style={landlordProfileStyle.landlordProfileTopBar}>
                <TouchableOpacity onPress={() => navigation.navigate('ListFavourite')}>
                  <Ionicons name="heart-circle-outline" size={24} color="#000" style={{ marginRight: 16 }} />
                </TouchableOpacity>
                <View style={{ flexDirection: 'row', justifyContent: 'flex-end' }}>
                  <Menu
                    visible={menuVisible}
                    onDismiss={closeMenu}
                    anchor={
                      <TouchableOpacity onPress={openMenu}>
                        <Icon name="setting" size={24} color="#000" />
                      </TouchableOpacity>
                    }
                  >
                    <Menu.Item
                      onPress={() => {
                        navigation.navigate('EditProfile', { user });
                        closeMenu();
                      }}
                      title="Thông tin cá nhân"
                    />
                    <Menu.Item
                      onPress={handleLogout}
                      title="Đăng xuất"
                    />
                  </Menu>
                </View>
              </View>

              <View style={landlordProfileStyle.landlordProfileInfo}>
                {user?.avatar && (
                  <Image source={{ uri: user.avatar }} style={landlordProfileStyle.landlordAvatar} />
                )}
                <Text style={landlordProfileStyle.landlordName}>{user.tenantInfo.full_name}</Text>
                <Text style={landlordProfileStyle.landlordEmail}>{user.email}</Text>
              </View>
            </View>

            <View style={landlordProfileStyle.landlordInfoBox}>
              <Text style={landlordProfileStyle.landlordSectionTitle}>Thông tin người thuê</Text>
              <Text style={{ textAlign: 'center', marginTop: 10 }}>Bạn hiện đang là người thuê. Các chức năng quản lý sẽ hiển thị ở đây.</Text>
            </View>
          </ScrollView>
        ) : null}

    </ScrollView>
  </Provider>
  );
};

export default ProfileScreen;
