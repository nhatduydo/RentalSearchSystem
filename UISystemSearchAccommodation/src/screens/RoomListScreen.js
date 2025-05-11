import React, { useEffect, useState } from 'react';
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  Platform,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import ListCard from '../components/ListCard';
import { useNavigation } from '@react-navigation/native';
import axios, { endpoints } from '../configs/Apis'; // Đảm bảo có export endpoints.motels

const RoomListScreen = () => {
  const navigation = useNavigation();
  const [motels, setMotels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMotels = async () => {
      try {
        const res = await axios.get(endpoints.motels);
        setMotels(res.data.results); // Tùy theo API bạn có thể sửa lại .data
      } catch (error) {
        console.error('Lỗi khi tải danh sách nhà trọ:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchMotels();
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={styles.searchWrapper}>
          <Icon name="search" size={20} color="gray" />
          <TextInput style={styles.searchInput} placeholder="Nhập nội dung tìm kiếm" />
        </View>

        <View style={styles.locationWrapper}>
          <Text style={styles.locationText}>Khu vực: Thành phố Hồ Chí Minh</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Filter')}>
            <Icon name="filter-list" size={22} color="blue" />
          </TouchableOpacity>
        </View>

        {loading ? (
          <ActivityIndicator size="large" color="deepskyblue" style={{ marginTop: 20 }} />
        ) : (
          <FlatList
            data={motels}
            numColumns={2}
            keyExtractor={item => item.id.toString()}
            columnWrapperStyle={{ justifyContent: 'space-between', marginBottom: 10 }}
            contentContainerStyle={{ paddingHorizontal: 10, paddingBottom: 100, marginTop: 10 }}
            renderItem={({ item }) => <ListCard room={item} />}
          />
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 10 },
  searchWrapper: {
    marginHorizontal: 10,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 10,
    borderRadius: 30,
    borderWidth: 1,
    borderColor: '#ccc',
  },
  searchInput: { marginLeft: 10, flex: 1, fontSize: 14 },
  locationWrapper: {
    marginTop: 10,
    marginHorizontal: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  locationText: { color: 'gray', fontSize: 13 },
  safeArea: {
    flex: 1,
    backgroundColor: '#fff',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
});

export default RoomListScreen;
