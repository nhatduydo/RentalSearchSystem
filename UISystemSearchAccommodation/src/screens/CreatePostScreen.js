import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, Image, StyleSheet, Alert, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import axios, { endpoints } from '../configs/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { RichEditor, RichToolbar, actions } from 'react-native-pell-rich-editor';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system';

const CreatePostScreen = ({ navigation }) => {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [user, setUser] = useState(null);
    const [minPrice, setMinPrice] = useState('');
    const [maxPrice, setMaxPrice] = useState('');
    const [images, setImages] = useState([]);

    const richText = useRef();

    const loadUser = async () => {
        try {
            const token = await AsyncStorage.getItem("access_token");
            const username = await AsyncStorage.getItem("username");
            if (!token || !username) return;

            const res = await axios.get(`/users/${username}/`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            setUser(res.data);
        } catch (error) {
            console.error("Lỗi khi lấy thông tin user:", error);
        }
    };

    useEffect(() => {
        loadUser();
    }, []);

    const handlePost = async () => {
        if (!title || !content || !minPrice || !maxPrice) {
            return Alert.alert("Thông báo", "Vui lòng nhập đầy đủ tiêu đề, nội dung và giá");
        }
        if (minPrice >= maxPrice) {
            return Alert.alert("Không được nhập giá tối thiểu lớn hơn hoặc bằng giá tối đa");
        }

        try {
            const token = await AsyncStorage.getItem('access_token');
            const postType = user?.role === 'Tenant' ? 'FIND_ROOM' : 'RENT_OUT';
            

            const formData = new FormData();
            formData.append("title", title);
            formData.append("content", content);
            formData.append("post_type", postType);
            formData.append("min_price", minPrice);
            formData.append("max_price", maxPrice);

            images.forEach(async (img, index) => {
                let uri = img.uri;

                if (Platform.OS === 'android' && uri.startsWith('content://')) {
                    const fileUri = `${FileSystem.documentDirectory}image_${index}.jpg`;
                    await FileSystem.copyAsync({
                        from: uri,
                        to: fileUri,
                    });
                    uri = fileUri;
                }

                formData.append("images", {
                    uri: uri,
                    name: img.fileName || `image_${index}.jpg`,
                    type: img.type || "image/jpeg",
                });
            });

            const res = await axios.post(endpoints.posts, formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                    Authorization: `Bearer ${token}`,
                },
            });
            console.log("Post response-->", res.data);
            Alert.alert("Thành công", "Đăng bài thành công!");
            navigation.goBack();
        } catch (error) {
            console.error("Lỗi đăng bài:", error);
            Alert.alert("Lỗi", "Không thể đăng bài");
        }
    };


    const picker = async () => {
        let { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
            alert("Permission denied!!");
        } else {
            const result = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.Images,
                quality: 1,
            });
            if (!result.canceled) {
                const newImages = result.assets;
                setImages(prev => [...prev, ...newImages]);
            }
        }
    };


    return (
        <ScrollView style={styles.container}>
            {user && (
                <View style={styles.userRow}>
                    <Image source={{ uri: user.avatar }} style={styles.avatar} />
                    <View>
                        <Text style={styles.name}>{user.last_name} {user.first_name}</Text>
                        <Text style={styles.role}>
                            {user.role === 'LANDLORD' ? 'Chủ trọ' : user.role === 'TENANT' ? 'Người dùng' : user.role}
                        </Text>
                    </View>
                </View>
            )}

            <TextInput
                placeholder="Nhập tiêu đề"
                value={title}
                onChangeText={setTitle}
                style={styles.titleInput}
            />
            <RichToolbar
                editor={richText}
                actions={[
                    actions.setBold,
                    actions.setItalic,
                    actions.insertBulletsList,
                    actions.insertOrderedList,
                    actions.insertLink,
                    actions.alignLeft,
                    actions.alignCenter,
                    actions.alignRight,
                ]}
                iconTint="black"
                style={styles.richBar}
                selectedIconTint="green"
                selectedButtonStyle={{ backgroundColor: "#cde" }}
            />

            <RichEditor
                ref={richText}
                placeholder="Nội dung bài viết..."
                onChange={setContent}
                style={styles.richEditor}
                initialHeight={150}
            />

            <TextInput
                placeholder="Giá tối thiểu"
                value={minPrice}
                onChangeText={setMinPrice}
                keyboardType="numeric"
                style={styles.titleInput}
            />

            <TextInput
                placeholder="Giá tối đa"
                value={maxPrice}
                onChangeText={setMaxPrice}
                keyboardType="numeric"
                style={styles.titleInput}
            />

            <View style={styles.imageList}>
                {images.map((img, index) => (
                    <Image key={index} source={{ uri: img.uri }} style={styles.imageBox} />
                ))}

                <TouchableOpacity onPress={picker} style={styles.addBox}>
                    <Ionicons name="add-outline" size={28} color='deepskyblue' />
                </TouchableOpacity>
            </View>


            <TouchableOpacity style={styles.postButton} onPress={handlePost}>
                <Text style={styles.postText}>Đăng bài</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};

export default CreatePostScreen;

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
        padding: 16,
    },
    userRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 16,
    },
    avatar: {
        width: 40,
        height: 40,
        borderRadius: 20,
        marginRight: 10,
    },
    name: {
        fontSize: 16,
        fontWeight: 'bold',
    },
    role: {
        fontSize: 12,
        color: 'gray',
    },
    titleInput: {
        borderColor: '#ccc',
        borderWidth: 1,
        borderRadius: 8,
        padding: 10,
        fontSize: 16,
        marginBottom: 10,
    },
    richBar: {
        borderTopLeftRadius: 8,
        borderTopRightRadius: 8,
        backgroundColor: 'lightgray',
    },
    richEditor: {
        borderColor: '#ddd',
        borderWidth: 1,
        borderBottomLeftRadius: 8,
        borderBottomRightRadius: 8,
        padding: 10,
        marginBottom: 10,
    },
    imageList: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 10,
        marginTop: 10,
    },
    imageBox: {
        width: 80,
        height: 80,
        borderRadius: 8,
        backgroundColor: '#eee',
    },
    addBox: {
        width: 80,
        height: 80,
        borderRadius: 8,
        backgroundColor: '#f0f0f0',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: '#ccc',
    },
    postButton: {
        marginTop: 20,
        backgroundColor: 'green',
        paddingVertical: 12,
        borderRadius: 10,
        alignItems: 'center',
    },
    postText: {
        color: 'white',
        fontSize: 16,
        fontWeight: 'bold',
    },
});
