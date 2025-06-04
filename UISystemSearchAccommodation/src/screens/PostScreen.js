import React, { useEffect, useState } from "react";
import { View, FlatList, ActivityIndicator, RefreshControl, Text, Image, TouchableOpacity } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from '@react-navigation/native';
import PostCard from "../components/PostCard";
import { useIsFocused } from '@react-navigation/native';
import axios, { endpoints } from "../configs/Apis";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { Ionicons } from '@expo/vector-icons';

const PostScreen = () => {
    const navigation = useNavigation();
    const [posts, setPosts] = useState([]);
    const [nextPage, setNextPage] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);
    const [avatarUri, setAvatarUri] = useState(null);
    const isFocused = useIsFocused();

    const getPosts = async () => {
        try {
            const token = await AsyncStorage.getItem('access_token');
            if (!token) return;

            const append = false;

            const res = await axios.get(endpoints.posts, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (append) {
                setPosts(prev => [...prev, ...res.data.results]);
            } else {
                setPosts(res.data.results);
            }

            setNextPage(res.data.next);
        } catch (error) {
            console.error("Lỗi khi lấy bài đăng:", error);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    const getAvatarUser = async () => {
        try {
            const token = await AsyncStorage.getItem("access_token");
            const username = await AsyncStorage.getItem("username");
            if (!token || !username) return;

            const res = await axios.get(`/users/${username}/`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            setAvatarUri(res.data.avatar);
        } catch (error) {
            console.error("Lỗi khi lấy avatar user:", error);
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await getPosts();
        setRefreshing(false);
    };

    const onEndReached = async () => {
        if (!nextPage || loadingMore) return;

        setLoadingMore(true);
        await getPosts(nextPage, true);
    };

    useEffect(() => {
        if (isFocused) {
            getPosts();
            getAvatarUser();
        }
    }, [isFocused]);

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: "#fff" }}>
            {loading ? (
                <ActivityIndicator size="large" color="#000" style={{ marginTop: 20 }} />
            ) : (
                <View style={{ flex: 1 }}>
                    <View style={{ flexDirection: 'row', marginTop: 10, justifyContent: 'space-between', paddingHorizontal: 20 }}>
                        <View style={{ paddingBottom: 15 }}>
                            <Text style={{ fontSize: 28, fontWeight: 'bold', color: 'deepskyblue' }}>Bài Đăng</Text>
                        </View>
                        <View style={{ paddingTop: 8, flexDirection: 'row' }}>
                            <Ionicons name="bookmark-outline" size={28} color='deepskyblue' style={{ marginLeft: 8 }} />
                            <Ionicons name="add-circle-outline" size={28} color='deepskyblue' style={{ marginLeft: 8 }} onPress={() => navigation.navigate('CreatePost')} />
                            <TouchableOpacity onPress={() => navigation.navigate('Profile')} style={{ marginLeft: 8 }}>
                                <Image
                                    source={{ uri: avatarUri }}
                                    style={{
                                        width: 40,
                                        height: 40,
                                        borderRadius: 15,
                                        borderWidth: 1,
                                        borderColor: '#ccc',
                                    }}
                                />
                            </TouchableOpacity>
                        </View>

                    </View>

                    <FlatList
                        data={posts}
                        keyExtractor={(item) => item.id}
                        renderItem={({ item }) => <PostCard post={item} />}
                        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
                        onEndReached={onEndReached}
                        onEndReachedThreshold={0.5}
                        ListFooterComponent={
                            loadingMore ? <ActivityIndicator size="small" color="#aaa" style={{ marginVertical: 10 }} /> : null
                        }
                    />
                </View>
            )}
        </SafeAreaView>
    );
};

export default PostScreen;
