import React, {useState, useEffect} from 'react';
import {Animated, View, Text, TouchableOpacity, Image} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import Homestyles from '../styles/homeStyle';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { endpoints } from '../configs/Apis';

const Card = ({data, index, scrollX, cardWidth, activeCardIndex, navigation}) => {
  const [imageUrl, setImageUrl] = useState(null);

  const fetchImage = async () => {
    try {
      const token = await AsyncStorage.getItem("access_token");
      if (!token)
        return;
      console.log("data.id",data.id);
      const res = await axios.get(`${endpoints['motel-images']}?motel_id=${data.id}`, {
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
    }, [data.id])
  const inputRange = [
    (index - 1) * cardWidth,
    index * cardWidth,
    (index + 1) * cardWidth,
  ];
  const opacity = scrollX.interpolate({
    inputRange,
    outputRange: [0.7, 0, 0.7],
  });
  const scale = scrollX.interpolate({
    inputRange,
    outputRange: [0.8, 1, 0.8],
  });
  

  return (
    <TouchableOpacity
      disabled={activeCardIndex !== index}
      activeOpacity={1}
      onPress={() => navigation.navigate('Detail', { motel: data })}>
      <Animated.View style={{...Homestyles.card, transform: [{scale}]}}>
        <Animated.View style={{...Homestyles.cardOverLay, opacity}} />
        <View style={Homestyles.priceTag}>
          <Text style={{color: 'white', fontSize: 20, fontWeight: 'bold'}}>
            Còn {data.available_rooms}P
          </Text>
        </View>
        <Image source={{ uri: imageUrl }} style={Homestyles.cardImage} />
        <View style={Homestyles.cardDetails}>
          <View style={{flexDirection: 'row', justifyContent: 'space-between'}}>
            <View>
              <Text style={{fontWeight: 'bold', fontSize: 17}}>{data.motel_name}</Text>
              <Text style={{color: 'grey', fontSize: 12}}>{data.address}</Text>
            </View>
            <Icon name="bookmark-border" size={26} color='deepskyblue' />
          </View>
        </View>
      </Animated.View>
    </TouchableOpacity>
  );
};

export default Card;
