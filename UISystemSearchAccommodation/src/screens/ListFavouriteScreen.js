import React, { useEffect, useState } from 'react';
import {
  SafeAreaView, View, Text, FlatList,
  StyleSheet, ActivityIndicator, Platform, StatusBar
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import ListCard from '../components/ListCard';
import axios, { endpoints } from '../configs/Apis';

const ListFavouriteScreen = () => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadFavorites = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem("access_token");

      const res = await axios.get(endpoints.favorites, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const motels = res.data.results.map(item => item.motel);
      setFavorites(motels);
    } catch (error) {
      console.error("Lỗi khi tải danh sách yêu thích:", error.response?.data || error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFavorites();
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Danh sách yêu thích</Text>
        <FlatList
          data={favorites}
          numColumns={2}
          keyExtractor={(item) => item.id.toString()}
          columnWrapperStyle={{ justifyContent: 'space-between', marginBottom: 10 }}
          contentContainerStyle={{ paddingHorizontal: 10, paddingBottom: 100, marginTop: 10 }}
          renderItem={({ item }) => <ListCard room={item} />}
          ListEmptyComponent={!loading && <Text style={styles.emptyText}>Bạn chưa yêu thích nhà trọ nào</Text>}
          ListFooterComponent={loading && <ActivityIndicator />}
        />
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 10 },
  title: { fontSize: 18, fontWeight: 'bold', marginHorizontal: 10 },
  emptyText: { textAlign: 'center', marginTop: 20, color: 'gray' },
  safeArea: {
    flex: 1,
    backgroundColor: '#fff',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
});

export default ListFavouriteScreen;
