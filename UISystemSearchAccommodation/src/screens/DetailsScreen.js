import React from 'react';
import { View, Text, StyleSheet, Image, ScrollView, TouchableOpacity, Dimensions, FlatList } from 'react-native';
import dataDetailRoom from '../const/dataDetailRoom';
import detailStyles from '../styles/detailStyles';
import Icon from 'react-native-vector-icons/MaterialIcons';

const DetailScreen = ({ route }) => {
    const { id } = route.params;

    const room = dataDetailRoom.find((item) => item.id === id);
    console.log('Dữ liệu phòng:', room);

    const costItems = [
        { label: 'Điện', value: room.expense.electric, unit: 'kWh' },
        { label: 'Nước', value: room.expense.water, unit: 'ng' },
        { label: 'Xe', value: room.expense.cycle, unit: 'xe' },
        { label: 'Quản lý', value: room.expense.manage, unit: 'ph' },
        { label: 'Wifi', value: room.expense.internet, unit: 'ph' },
        { label: 'Máy giặt', value: room.expense.wash, unit: 'ng' },
    ];


    return (
        <ScrollView style={detailStyles.container}>
            <ScrollView horizontal
                pagingEnabled showsHorizontalScrollIndicator={true} style={detailStyles.scrollView} >
                {room.images?.map((img, index) => (
                    <Image key={index} source={img} style={detailStyles.carouselImage} />
                ))}
            </ScrollView>

            <View style={detailStyles.info}>
                <Text style={detailStyles.title}>{room.name}</Text>
                <Text style={detailStyles.price}>Giá: {room.price}</Text>
                <Text style={detailStyles.location}>{room.location}</Text>
                <Text style={detailStyles.details}>{room.details}</Text>
                <Text style={detailStyles.total}>{room.total}</Text>

                <View style={detailStyles.costGrid}>
                    {costItems.map((item, index) => (
                        <View key={index} style={detailStyles.costCell}>
                            <Text style={detailStyles.costLabel}>{item.label}</Text>
                            <Text style={detailStyles.costValue}>
                                {item.value.toLocaleString()}
                            </Text>
                            <Text style={detailStyles.costUnit}>/{item.unit}</Text>
                        </View>
                    ))}
                </View>

            </View>

            <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', margin: 16 }}>
                <TouchableOpacity style={detailStyles.button}>
                    <Text style={detailStyles.buttonText}>Đặt lịch xem phòng</Text>
                </TouchableOpacity>
                <TouchableOpacity style={{ alignItems: 'center', marginLeft: 12 }}>
                    <Icon name="chat" size={20} color='#007AFF'></Icon>
                    <Text style={{ fontSize: 12, color: 'gray', marginTop: 4 }}>Chat ngay</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
};

export default DetailScreen;
