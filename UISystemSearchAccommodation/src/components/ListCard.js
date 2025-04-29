import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity, Dimensions } from 'react-native';
import { useNavigation } from '@react-navigation/native';

const screenWidth = Dimensions.get('window').width;
const cardWidth = (screenWidth - 30) / 2;

const ListCard = ({ room }) => {
  const navigation = useNavigation();

  return (
    <TouchableOpacity onPress={() => navigation.navigate('Detail', { id: room.id })}>
      <View style={[styles.card, { width: cardWidth }]}>
        <Image source={room.image} style={styles.image} />
        <View style={styles.detailsContainer}>
          <Text style={styles.detailsText}>{room.details}</Text>
        </View>
        <View style={styles.content}>
          <Text numberOfLines={2} style={styles.location}>{room.location}</Text>
          <Text style={styles.price}>Giá: {room.price}</Text>
          <Text style={styles.total}>Tổng: {room.total}</Text>
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
  },
  price: {
    fontSize: 12,
    color: '#007bff',
    fontWeight: 'bold',
  },
  total: {
    fontSize: 12,
  },
});

export default ListCard;
