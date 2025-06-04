import React, { useEffect, useState } from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity, Dimensions } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import axios, { endpoints } from '../configs/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';

const screenWidth = Dimensions.get('window').width;
const cardWidth = (screenWidth - 30) / 2;

const ListCard = ({ room }) => {
  const navigation = useNavigation();
  const [imageUrl, setImageUrl] = useState(null);

  const fetchImage = async () => {
    try {
      const token = await AsyncStorage.getItem("access_token");
      if (!token)
        return;
      const res = await axios.get(`${endpoints['motel-images']}?motel_id=${room.id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.data && res.data.results && res.data.results.length > 0) {
        setImageUrl(res.data.results[0].image_url); 
      }
    } catch (error) {
      console.error("Lỗi khi tải ảnh:", error);
    }
  };

  useEffect(() => {
    fetchImage();
  }, [room.id])

  return (
    <TouchableOpacity onPress={() => navigation.navigate('Detail', { motel: room })}>
      <View style={[styles.card, { width: cardWidth }]}>
        <Image source={{ uri: imageUrl }} style={styles.image} />
        <View style={styles.detailsContainer}>
          <Text style={styles.detailsText}>{room.motel_name}</Text>
        </View>
        <View style={styles.content}>
          <Text numberOfLines={2} style={styles.location}>Địa chỉ: {room.address}</Text>
          <Text style={styles.price}>{room.description}</Text>
          <Text style={styles.total}>Tổng: {room.total_rooms} Phòng</Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 10,
    backgroundColor: '#fff',
    overflow: 'hidden',
    marginBottom: 10,
  },
  image: {
    width: '100%',
    height: 120,
    resizeMode: 'cover',
  },
  detailsContainer: {
    position: 'absolute',
    top: 5,
    left: 5,
    backgroundColor: '#007bff',
    borderRadius: 5,
    paddingHorizontal: 5,
    paddingVertical: 2,
    zIndex: 1,
  },
  detailsText: {
    color: 'white',
    fontSize: 11,
    fontWeight: 'bold',
  },
  content: {
    padding: 5,
  },
  location: {
    fontSize: 12,
    marginBottom: 3,
    color: '#007bff',
    fontWeight: 'bold',
  },
  price: {
    fontSize: 12,
    fontWeight: 'semibold',
  },
  total: {
    fontSize: 12,
  },
});

export default ListCard;
