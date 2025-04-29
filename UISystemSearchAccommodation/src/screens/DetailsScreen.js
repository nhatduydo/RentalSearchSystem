import React from 'react';
import { View, Text, StyleSheet, Image, ScrollView, TouchableOpacity } from 'react-native';

const DetailScreen = ({ route }) => {
    const { room } = route.params;

    return (
        <ScrollView style={styles.container}>
            <Image source={room.image} style={styles.image} />

            <View style={styles.info}>
                <Text style={styles.title}>{room.name}</Text>
                <Text style={styles.price}>Giá: {room.price} triệu</Text>
                <Text style={styles.location}>{room.location}</Text>
                <Text style={styles.details}>{room.details}</Text>
                <Text style={styles.total}>{room.total}</Text>
            </View>

            <TouchableOpacity style={styles.button}>
                <Text style={styles.buttonText}>Đặt lịch xem phòng</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#fff' },
    image: { width: '100%', height: 200 },
    info: { padding: 16 },
    title: { fontSize: 18, fontWeight: 'bold' },
    price: { fontSize: 16, color: 'red', marginVertical: 5 },
    location: { fontSize: 14, marginBottom: 4 },
    details: { fontSize: 14, marginBottom: 4 },
    total: { fontSize: 14, color: 'gray' },
    button: {
        backgroundColor: '#007AFF',
        margin: 16,
        padding: 12,
        borderRadius: 8,
        alignItems: 'center',
    },
    buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});

export default DetailScreen;
