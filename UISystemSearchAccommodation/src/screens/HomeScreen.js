import React, { useEffect, useState, useRef } from 'react';
import { Dimensions, Image, SafeAreaView, Text, View, Animated, ActivityIndicator, TouchableOpacity, } from 'react-native';
import { Searchbar } from 'react-native-paper';
// import Icon from 'react-native-vector-icons/MaterialIcons';
import Homestyles from '../styles/homeStyle';
//import dataAccommodation from '../const/dataAccommodation';
import { Ionicons } from '@expo/vector-icons';
import Card from '../components/Card';
import { utilities } from '../const/utilities';
import axios, { endpoints } from '../configs/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';

const HomeScreen = ({ navigation }) => {
  const [avatarUri, setAvatarUri] = useState(null);
  const scrollX = useRef(new Animated.Value(0)).current;
  const [activeCardIndex, setActiveCardIndex] = useState(0);
  const cardWidth = Dimensions.get('window').width - 80;

  const [motels, setMotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const getAvatarUser = async () => {
    try {
      const token = await AsyncStorage.getItem("access_token");
      const username = await AsyncStorage.getItem("username");
      if (!token || !username) return;

      const res = await axios.get(`/users/${username}/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setAvatarUri(res.data.avatar);
    } catch (error) {
      console.error("Lỗi khi lấy avatar user:", error);
    }
  };

  useEffect(() => {
    const fetchMotels = async () => {
      try {
        const res = await axios.get(endpoints.motels);
        setMotels(res.data.results.slice(0, 5));
      } catch (err) {
        console.error('Lỗi lấy danh sách nhà trọ:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchMotels();
    getAvatarUser();
  }, []);


  return (
    <SafeAreaView style={Homestyles.safeArea}>
      <View style={Homestyles.header}>
        <View style={{ paddingBottom: 15 }}>
          <Text style={{ fontSize: 25, fontWeight: 'bold' }}>
            Hệ Thống Tìm Kiếm
          </Text>
          <View style={{ flexDirection: 'row' }}>
            <Text style={{ fontSize: 28, fontWeight: 'bold', color: 'deepskyblue' }}>
              Nhà Trọ
            </Text>
          </View>
        </View>
        {avatarUri ? (
          <TouchableOpacity onPress={() => navigation.navigate('Profile')} style={{ marginLeft: 8, marginTop: 8 }}>
            <Image
              source={{ uri: avatarUri }}
              style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                borderWidth: 1,
                borderColor: '#ccc',
              }}
            />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity onPress={() => navigation.navigate('SignIn')} style={{ marginLeft: 8 }}>
            <Ionicons name="person-outline" size={36} color="deepskyblue" />
          </TouchableOpacity>
        )}
      </View>
      <TouchableOpacity onPress={() => navigation.navigate('Search')} activeOpacity={1}>
        <Searchbar
          placeholder="Tìm phòng giá tốt tại đây"
          style={Homestyles.searchBar}
          editable={false}
          pointerEvents="none"
        />
      </TouchableOpacity>

      <View
        style={{
          flexDirection: 'row',
          justifyContent: 'space-between',
          marginHorizontal: 20,
          marginTop: 20,
        }}>
        <Text style={{ fontWeight: 'bold', color: 'grey' }}>Nhà trọ phổ biến</Text>
        <TouchableOpacity onPress={() => navigation.navigate('Search')}>
          <Text style={{ color: 'grey' }}>Xem tất cả</Text>
        </TouchableOpacity>

      </View>

      <View>
        {loading ? (
          <ActivityIndicator size="large" color="deepskyblue" style={{ marginTop: 30 }} />
        ) : (
          <Animated.FlatList
            data={motels}
            keyExtractor={(item) => item.id.toString()}
            horizontal
            showsHorizontalScrollIndicator={false}
            snapToInterval={cardWidth}
            decelerationRate="fast"
            bounces={false}
            contentContainerStyle={{
              paddingVertical: 30,
              paddingLeft: 20,
              paddingRight: cardWidth / 2 - 40,
            }}
            renderItem={({ item, index }) => (
              <Card
                data={item}
                index={index}
                scrollX={scrollX}
                cardWidth={cardWidth}
                activeCardIndex={activeCardIndex}
                navigation={navigation}
              />
            )}
            onMomentumScrollEnd={(e) => {
              const index = Math.round(e.nativeEvent.contentOffset.x / cardWidth);
              setActiveCardIndex(index);
            }}
            onScroll={Animated.event(
              [{ nativeEvent: { contentOffset: { x: scrollX } } }],
              { useNativeDriver: true }
            )}
          />
        )}
      </View>

      <View
        style={{
          flexDirection: 'row',
          justifyContent: 'space-between',
          marginHorizontal: 20,
          marginTop: 10,
        }}>
        <Text style={{ fontWeight: 'bold', color: 'grey' }}>Tiện Ích</Text>
      </View>

      <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-around', marginTop: 20 }}>
        {utilities.map((item, index) => (
          <TouchableOpacity
            key={index}
            style={{
              width: 80,
              height: 80,
              backgroundColor: '#f0f0f0',
              borderRadius: 10,
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 15,
            }}
            onPress={() => navigation.navigate(item.screen)}
          >
            {item.icon}
            <Text style={{ fontSize: 12, marginTop: 5, textAlign: 'center' }}>{item.name}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </SafeAreaView>
  );
};

export default HomeScreen;