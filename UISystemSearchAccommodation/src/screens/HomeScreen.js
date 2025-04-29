import React from 'react';
import {
  Dimensions,
  Image,
  SafeAreaView,
  Text,
  View,
  Animated,
} from 'react-native';
import { Searchbar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialIcons';
import Homestyles from '../styles/homeStyle';
import dataAccommodation from '../const/dataAccommodation';
import Card from '../components/Card';
import { categoryTrends } from '../const/categoryTrends';
const { width } = Dimensions.get('screen');
const cardWidth = width / 1.8;

const HomeScreen = ({ navigation }) => {
  const [q, setQ] = React.useState();
  const scrollX = React.useRef(new Animated.Value(0)).current;
  const [activeCardIndex, setActiveCardIndex] = React.useState(0);
  const cardWidth = Dimensions.get('window').width - 80;


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
        <Icon name="person-outline" size={36} color='deepskyblue'></Icon>
      </View>
      <Searchbar placeholder="Tìm phòng giá tốt tại đây" value={q} onChangeText={setQ} style={Homestyles.searchBar} />

      <View
        style={{
          flexDirection: 'row',
          justifyContent: 'space-between',
          marginHorizontal: 20,
          marginTop: 20,
        }}>
        <Text style={{ fontWeight: 'bold', color: 'grey' }}>Nhà trọ gần đây</Text>
        <Text style={{ color: 'grey' }}>Show all</Text>
      </View>

      <View>
        <Animated.FlatList
          data={dataAccommodation}
          keyExtractor={(item, index) => index.toString()}
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
      </View>


      <View
          style={{
            flexDirection: 'row',
            justifyContent: 'space-between',
            marginHorizontal: 20,
            marginTop: 20,
          }}>
          <Text style={{ fontWeight: 'bold', color: 'grey' }}>Xu hướng tìm phòng trọ</Text>
          <Text style={{ color: 'grey' }}>Xem tất cả</Text>
        </View>

      <View style={{ marginHorizontal: 20 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 20 }}>
          {categoryTrends.map((item, index) => (
            <View key={index} style={{ alignItems: 'center', width: 70 }}>
              <Image source={item.image} style={{ width: 60, height: 60, borderRadius: 15 }} />
              <Text style={{ fontSize: 12, textAlign: 'center', marginTop: 5 }}>{item.name}</Text>
            </View>
          ))}
        </View>
      </View>
    </SafeAreaView>
  );
};

export default HomeScreen;