import React, { useEffect, useState } from "react";
import { View, Text, Image, ScrollView, StyleSheet, ActivityIndicator } from "react-native";
import axios, { endpoints } from "../configs/Apis";
import ListCard from "../components/ListCard";

const LandlordInfoScreen = ({ route }) => {
    const { landlordId } = route.params;
    const [landlord, setLandlord] = useState(null);
    const [motels, setMotels] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadInfo = async () => {
            try {
                setLoading(true);

                const res = await axios.get(`${endpoints.landlords}${landlordId}/`);
                setLandlord(res.data);

                const motelRes = await axios.get(`${endpoints.motels}`);
                const filteredMotels = motelRes.data.results.filter(
                    (motel) => motel.user.id === res.data.user
                );
                setMotels(filteredMotels);
            } catch (err) {
                console.error("Lỗi khi tải thông tin chủ trọ:", err);
            } finally {
                setLoading(false);
            }
        };

        loadInfo();
    }, [landlordId]);

    if (loading) {
        return (
            <View style={{
                flex: 1,
                justifyContent: 'center',
                alignItems: 'center',
            }}>
                <ActivityIndicator size="large" color="#2196F3" />
            </View>
        );
    }

    return (
        <ScrollView style={styles.container}>
            <View style={styles.avatarContainer}>
                <Image
                    source={require('../assets/images/meomeo1.jpg')}
                    style={styles.avatar}
                />
                <Text style={styles.name}>{landlord.full_name}</Text>
                <Text>CCCD: {landlord.citizen_id}</Text>
                <Text>SDT: {landlord.phone}</Text>
                <Text>Địa chỉ: {landlord.address}</Text>
                <Text>Ngày sinh: {landlord.date_of_birth}</Text>
                <Text>Giới tính: {landlord.gender === "MALE" ? "Nam" : "Nữ"}</Text>
                <Text>Ngân hàng: {landlord.bank_account}</Text>
                <Text>Xác minh: {landlord.is_verified ? "✔️ Đã xác minh" : "❌ Chưa xác minh"}</Text>
            </View>

            <Text style={styles.sectionTitle}>Danh sách nhà trọ</Text>
            <View style={styles.listContainer}>
                {motels.map((motel) => (
                    <ListCard key={motel.id} room={motel} />
                ))}
            </View>
        </ScrollView>
    );
};

export default LandlordInfoScreen;

const styles = StyleSheet.create({
    container: {
        padding: 16,
        backgroundColor: "#fff",
    },
    avatarContainer: {
        alignItems: "center",
        marginBottom: 20,
    },
    avatar: {
        width: 100,
        height: 100,
        borderRadius: 50,
        marginBottom: 8,
    },
    name: {
        fontSize: 20,
        fontWeight: "bold",
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: "bold",
        marginVertical: 16,
    },
    listContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
    },
});
