import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const serviceList = [
    'Wifi',
    'Quạt',
    'Bếp gas',
    'Ban công',
    'Quạt trần',
    'Máy giặt',
    'Tủ lạnh',
    'Cách âm',
    'Bàn học',
    'Cửa sổ',
    'Máy lạnh',
];

const CostGrid = ({ amenities }) => {
    const hasAmenity = (name) =>
        amenities.some((item) => item.name.toLowerCase() === name.toLowerCase());

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Chi phí dịch vụ</Text>
            <View style={styles.grid}>
                {serviceList.map((service, index) => (
                    <View key={service} style={styles.gridItem}>
                        <Text style={styles.serviceName}>{service}</Text>
                        <Text style={hasAmenity(service) ? styles.yes : styles.no}>
                            {hasAmenity(service) ? '✔ Có' : '✘ Không'}
                        </Text>
                    </View>
                ))}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        marginTop: 10,
        marginBottom: 10,
        
    },
    title: {
        fontSize: 18,
        fontWeight: '600',
        marginBottom: 12,
    },
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        borderTopWidth: 1,
        borderLeftWidth: 1,
        borderColor: '#ccc',
    },
    gridItem: {
        width: '25%',
        paddingVertical: 12,
        alignItems: 'center',
        justifyContent: 'center',
        borderRightWidth: 1,
        borderBottomWidth: 1,
        borderColor: '#ccc',
    },
    serviceName: {
        fontSize: 15,
        color: '#444',
    },
    yes: {
        fontSize: 15,
        fontWeight: '500',
        color: 'green',
    },
    no: {
        fontSize: 15,
        fontWeight: '500',
        color: 'red',
    },
});

export default CostGrid;
