import React from 'react';
import { SafeAreaView, View, Text, TextInput, FlatList, StyleSheet, TouchableOpacity, Platform, StatusBar } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import dataListCate from '../const/dataListCate';
import ListCard from '../components/ListCard';

const RoomListScreen = () => {
    return (
        <SafeAreaView style={styles.safeArea}>
            <View style={styles.container}>
                <View style={styles.searchWrapper}>
                    <Icon name="search" size={20} color="gray" />
                    <TextInput style={styles.searchInput} placeholder="Nhập nội dung tìm kiếm" />
                </View>

                <View style={styles.locationWrapper}>
                    <Text style={styles.locationText}>Khu vực: Thành phố Hồ Chí Minh</Text>
                    <TouchableOpacity>
                        <Icon name="filter-list" size={22} color="blue" />
                    </TouchableOpacity>
                </View>

                <FlatList
                    data={dataListCate}
                    numColumns={2}
                    keyExtractor={item => item.id.toString()}
                    columnWrapperStyle={{ justifyContent: 'space-between', marginBottom: 10 }}
                    contentContainerStyle={{ paddingHorizontal: 10, paddingBottom: 100, marginTop: 10 }}
                    renderItem={({ item }) => <ListCard room={item} />}
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
