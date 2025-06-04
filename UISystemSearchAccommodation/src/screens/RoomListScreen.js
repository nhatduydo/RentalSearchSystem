import React, { useEffect, useState } from 'react';
import { SafeAreaView, View, Text, TextInput, FlatList, StyleSheet, TouchableOpacity, Platform, StatusBar, ActivityIndicator, } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import ListCard from '../components/ListCard';
import { useNavigation } from '@react-navigation/native';
import axios, { endpoints } from '../configs/Apis';

const RoomListScreen = () => {
  const navigation = useNavigation();
  const [motels, setMotels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [page, setPage] = useState(1);


  const loadMotels = async () => {
    try {
      setLoading(true);
      const url = `${endpoints.motels}?page=${page}`;
      const res = await axios.get(url);
      //console.log(res);
      setMotels(prev =>
        page === 1 ? res.data.results : [...prev, ...res.data.results]
      );

      if (!res.data.next) {
        setPage(0);
      }
    } catch (error) {
      console.error("Lỗi khi tải danh sách trọ:", error);
    } finally {
      setLoading(false);
    }
  };

  const searchMotel = async (params) => {
    setLoading(true);
    try {
      const filteredParams = Object.fromEntries(
        Object.entries(params).filter(
          ([key, value]) => value !== null && value !== undefined && value !== ''
        )
      );
      const query = new URLSearchParams(filteredParams).toString();
      //console.log("query --> ", query);
      const response = await axios.get(`${endpoints.searchs}?${query}`);
      //console.log("Dữ liệu sau khi lọc --> ", response.data);
      setMotels(response.data);
    } catch (error) {
      console.error("err", error);
      setMotels([]);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    setMotels([]);
    setPage(1);
  }, [searchText]);

  const handleSearch = () => {
    if (searchText.trim() === '') {
      setPage(1);
      setMotels([]);
      loadMotels();
    } else {
      searchMotel({ q: searchText });
    }
  };

  useEffect(() => {
    if (page > 0) {
      loadMotels();
    }
  }, [page]);

  const handleApplyFilter = (params) => {
    searchMotel(params);
  };

  const loadMore = () => {
    if (!loading && page !== 0) {
      setLoading(true);
      setPage(prev => prev + 1);
    }
  };


  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={styles.searchWrapper}>
          <TouchableOpacity onPress={() => handleSearch()}>
            <Icon name="search" size={20} color="gray" />
          </TouchableOpacity>
          <TextInput
            style={styles.searchInput}
            placeholder="Nhập nội dung tìm kiếm"
            value={searchText}
            onChangeText={setSearchText}
            returnKeyType="search"
            onSubmitEditing={() => handleSearch()}
          />
        </View>

        <View style={styles.locationWrapper}>
          <Text style={styles.locationText}>Khu vực: Thành phố Hồ Chí Minh</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Filter', { onApplyFilter: handleApplyFilter })}>
            <Icon name="filter-list" size={22} color="blue" />
          </TouchableOpacity>
        </View>
        <FlatList
          data={motels}
          numColumns={2}
          keyExtractor={(item) => item.id.toString()}
          columnWrapperStyle={{ justifyContent: 'space-between', marginBottom: 10 }}
          contentContainerStyle={{ paddingHorizontal: 10, paddingBottom: 100, marginTop: 10 }}
          renderItem={({ item }) => <ListCard room={item} />}
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListFooterComponent={loading && <ActivityIndicator />}
        />
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
