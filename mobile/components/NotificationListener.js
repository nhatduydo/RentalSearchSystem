import * as Notifications from 'expo-notifications';
import { initializeApp } from 'firebase/app';
import { getDatabase, off, onValue, ref } from 'firebase/database';
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

// Cấu hình Firebase
const firebaseConfig = {
    databaseURL: "https://systemaccommodation-eca81-default-rtdb.asia-southeast1.firebasedatabase.app/",
    // Thêm các cấu hình khác nếu cần
};

// Khởi tạo Firebase
const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

const NotificationListener = ({ userId }) => {
    const [notifications, setNotifications] = useState([]);

    useEffect(() => {
        // Cấu hình thông báo local
        Notifications.setNotificationHandler({
            handleNotification: async () => ({
                shouldShowAlert: true,
                shouldPlaySound: true,
                shouldSetBadge: true,
            }),
        });

        // Lắng nghe thông báo từ Firebase
        const notificationsRef = ref(database, `notifications/${userId}`);
        onValue(notificationsRef, (snapshot) => {
            const data = snapshot.val();
            if (data) {
                const notificationList = Object.values(data);
                setNotifications(notificationList);

                // Hiển thị thông báo local cho thông báo mới nhất
                const latestNotification = notificationList[notificationList.length - 1];
                if (latestNotification) {
                    Notifications.scheduleNotificationAsync({
                        content: {
                            title: latestNotification.title,
                            body: latestNotification.content,
                        },
                        trigger: null,
                    });
                }
            }
        });

        // Cleanup listener khi component unmount
        return () => {
            off(notificationsRef);
        };
    }, [userId]);

    return (
        <View style={styles.container}>
            {notifications.map((notification, index) => (
                <View key={index} style={styles.notificationItem}>
                    <Text style={styles.title}>{notification.title}</Text>
                    <Text style={styles.content}>{notification.content}</Text>
                    <Text style={styles.date}>
                        {new Date(notification.created_date).toLocaleString()}
                    </Text>
                </View>
            ))}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: 10,
    },
    notificationItem: {
        backgroundColor: '#fff',
        padding: 15,
        borderRadius: 8,
        marginBottom: 10,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
    },
    title: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 5,
    },
    content: {
        fontSize: 14,
        color: '#666',
        marginBottom: 5,
    },
    date: {
        fontSize: 12,
        color: '#999',
    },
});

export default NotificationListener; 