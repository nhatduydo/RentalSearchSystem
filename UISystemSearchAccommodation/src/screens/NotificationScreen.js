import React, { useState } from 'react';
import { View, Text, FlatList, TextInput, Image, SafeAreaView, ActivityIndicator } from 'react-native';
import { dataNotification } from '../const/dataNorification';
import { NotificationStyles } from '../styles/notificationStyle';

const NotificationScreen = () => {
  const [query, setQuery] = useState('');

  const filteredData = dataNotification.filter(item =>
    item.title.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <SafeAreaView style={NotificationStyles.container}>
      <View style={NotificationStyles.header}>
        <Text style={NotificationStyles.headerText}>THÔNG BÁO</Text>
        <TextInput style={NotificationStyles.searchBar} placeholder="Tìm kiếm" value={query} onChangeText={setQuery}/>
      </View>

      <FlatList
        ListFooterComponent= {<ActivityIndicator />}
        data={filteredData}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={NotificationStyles.itemContainer}>
            <Image
              source={require('../assets/images/meomeo1.jpg')}
              style={NotificationStyles.logo}
            />
            <View style={NotificationStyles.textWrapper}>
              <Text style={NotificationStyles.title}>{item.title}</Text>
              <Text style={NotificationStyles.description}>{item.description}</Text>
            </View>
          </View>
        )}
      />
    </SafeAreaView>
  );
};

export default NotificationScreen;
