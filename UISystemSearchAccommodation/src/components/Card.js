import React from 'react';
import {Animated, View, Text, TouchableOpacity, Image} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import Homestyles from '../styles/homeStyle';

const Card = ({data, index, scrollX, cardWidth, activeCardIndex, navigation}) => {
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
        <Image source={require('../assets/images/meomeo1.jpg')} style={Homestyles.cardImage} />
        <View style={Homestyles.cardDetails}>
          <View style={{flexDirection: 'row', justifyContent: 'space-between'}}>
            <View>
              <Text style={{fontWeight: 'bold', fontSize: 17}}>{data.motel_name}</Text>
              <Text style={{color: 'grey', fontSize: 12}}>{data.address}</Text>
            </View>
            <Icon name="bookmark-border" size={26} color='deepskyblue' />
          </View>
          <View style={{flexDirection: 'row', justifyContent: 'space-between', marginTop: 10}}>
            <View style={{flexDirection: 'row'}}>
              <Icon name="star" size={15} color='orange' />
              <Icon name="star" size={15} color='orange' />
              <Icon name="star" size={15} color='orange' />
              <Icon name="star" size={15} color='orange' />
              <Icon name="star" size={15} color='grey' />
            </View>
            <Text style={{fontSize: 10, color: 'grey'}}>365 reviews</Text>
          </View>
        </View>
      </Animated.View>
    </TouchableOpacity>
  );
};

export default Card;
