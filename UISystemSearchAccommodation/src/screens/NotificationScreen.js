import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TextInput, Image, SafeAreaView, ActivityIndicator } from 'react-native';
import { NotificationStyles } from '../styles/notificationStyle';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { endpoints } from '../configs/Apis';

const NotificationScreen = () => {
  const [query, setQuery] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [user, setUser] = useState('');
  const [loading, setLoading] = useState(true);

  const loadUser = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) return;

      const resUser = await axios.get(`${endpoints.users}current-user/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setUser(resUser.data);
    } catch (err) {
      console.error('Error loading avatar:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const loadNotifications = async () => {
      try {
        const token = await AsyncStorage.getItem('access_token');
        if (!token) return;

        const res = await axios.get(endpoints.notifications, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setNotifications(res.data.results);
        // console.log('Notifications from API:', res.data);
        // console.log('Set notifications:', res.data.results);
        // console.log('Notifications state:', notifications);

      } catch (err) {
        console.error('Error loading notifications:', err);
      } finally {
        setLoading(false);
      }
    };

    loadNotifications();
    loadUser();

  }, []);

  const filteredData = notifications.filter(item =>
    item.title.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <SafeAreaView style={NotificationStyles.container}>
      <View style={NotificationStyles.header}>
        <Text style={NotificationStyles.headerText}>THÔNG BÁO</Text>
        <TextInput
          style={NotificationStyles.searchBar}
          placeholder="Tìm kiếm"
          value={query}
          onChangeText={setQuery}
        />
      </View>

      {loading ? (
        <ActivityIndicator size="large" />
      ) : (
        <FlatList
          data={filteredData}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <View style={NotificationStyles.itemContainer}>
              <Image
                source={{ uri: user.avatar }}
                style={NotificationStyles.logo}
              />
              <View style={NotificationStyles.textWrapper}>
                <Text style={NotificationStyles.description}>
                  {item.content}
                </Text>

                <Text style={NotificationStyles.meta}>
                  Loại: {item.notification_type}
                </Text>

                <Text style={NotificationStyles.meta}>
                  Ngày tạo: {new Date(item.created_date).toLocaleString()}
                </Text>
              </View>
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
};

export default NotificationScreen;

