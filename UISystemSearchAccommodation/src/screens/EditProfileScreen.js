import {
  View, Text, TextInput, Button, Image, TouchableOpacity,
  Alert, ActivityIndicator, ScrollView, StyleSheet
} from 'react-native';
import React, { useState, useEffect } from 'react';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { endpoints } from '../configs/Apis';
import { Ionicons } from '@expo/vector-icons';

const EditProfileScreen = ({ route, navigation }) => {
  const { user } = route.params;
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState(null);
  const [avatar, setAvatar] = useState(user.avatar);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUserInfo = async () => {
      try {
        const token = await AsyncStorage.getItem('access_token');
        let res;

        if (user.role === 'LANDLORD') {
          res = await axios.get(`${endpoints.landlords}?user=${user.id}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
        } else if (user.role === 'TENANT') {
          res = await axios.get(`${endpoints.tenants}?user=${user.id}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
        }

        const matchedUser = res.data.results.find((item) => item.user === user.id);
        if (matchedUser) {
          setFormData(matchedUser);
        } else {
          Alert.alert("Không tìm thấy dữ liệu người dùng!");
        }
      } catch (err) {
        console.error("Lỗi load thông tin:", err);
        Alert.alert("Lỗi", "Không thể tải thông tin người dùng.");
      } finally {
        setLoading(false);
      }
    };

    loadUserInfo();
  }, []);

  const pickImage = async () => {
    if (!editMode) return;
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permissionResult.granted) {
      Alert.alert("Permission Denied", "Camera roll permission is required!");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync();
    if (!result.canceled) {
      setAvatar(result.assets[0].uri);
    }
  };

  const saveChanges = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');

      const body = {
        full_name: formData.full_name,
        address: formData.address,
        date_of_birth: formData.date_of_birth,
        bank_account: formData.bank_account,
      };

      if (user.role === 'LANDLORD') {
        await axios.put(`${endpoints.landlords}${formData.user}/`, body, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else if (user.role === 'TENANT') {
        await axios.put(`${endpoints.tenants}${formData.user}/`, body, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }

      if (avatar !== user.avatar) {
        const form = new FormData();
        form.append('avatar', {
          uri: avatar,
          name: 'avatar.jpg',
          type: 'image/jpeg',
        });

        await axios.patch(`${endpoints.users}${user.id}/`, form, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data',
          },
        });
      }

      Alert.alert("Thành công", "Cập nhật thông tin thành công");
      setEditMode(false);
    } catch (err) {
      Alert.alert("Lỗi", "Không thể cập nhật thông tin.");
      console.log("Lỗi trả về:", err.response?.data || err.message);
    }
  };

  if (loading || !formData) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text>Đang tải thông tin...</Text>
      </View>
    );
  }

  return (
    <ScrollView >
      <View style={styles.headers}>
        <TouchableOpacity onPress={pickImage} disabled={!editMode} style={styles.avatarContainer}>
          <Image source={{ uri: avatar }} style={styles.avatar} />
          {editMode && (
            <View style={styles.editIcon}>
              <Ionicons name="camera" size={20} color="white" />
            </View>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.field}>
          <Text style={styles.label}>Họ tên</Text>
          {editMode ? (
            <TextInput
              style={styles.input}
              value={formData.full_name}
              onChangeText={(text) => setFormData({ ...formData, full_name: text })}
            />
          ) : (
            <Text style={styles.text}>{formData.full_name}</Text>
          )}
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Địa chỉ</Text>
          {editMode ? (
            <TextInput
              style={styles.input}
              value={formData.address}
              onChangeText={(text) => setFormData({ ...formData, address: text })}
            />
          ) : (
            <Text style={styles.text}>{formData.address}</Text>
          )}
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Ngày sinh</Text>
          {editMode ? (
            <TextInput
              style={styles.input}
              value={formData.date_of_birth}
              onChangeText={(text) => setFormData({ ...formData, date_of_birth: text })}
            />
          ) : (
            <Text style={styles.text}>{formData.date_of_birth}</Text>
          )}
        </View>

        <View style={styles.field}>
          <Text style={styles.label}>Ngân hàng</Text>
          {editMode ? (
            <TextInput
              style={styles.input}
              value={formData.bank_account}
              onChangeText={(text) => setFormData({ ...formData, bank_account: text })}
            />
          ) : (
            <Text style={styles.text}>{formData.bank_account}</Text>
          )}
        </View>

        <View style={styles.buttonRow}>
          {editMode ? (
            <>
              <Button title="Hủy" color="gray" onPress={() => setEditMode(false)} />
              <Button title="Lưu" color="green" onPress={saveChanges} />
            </>
          ) : (
            <Button title="Chỉnh sửa" onPress={() => setEditMode(true)} />
          )}
        </View>
      </ScrollView>

    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    backgroundColor: '#fff',
    flexGrow: 1,
  },
  headers: {
    backgroundColor: '#add8e6',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 0,
    paddingTop: 30,
    paddingBottom: 20,
  },

  avatar: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 3,
    borderColor: '#007AFF',
  },

  editIcon: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: '#007AFF',
    borderRadius: 20,
    padding: 6,
    borderWidth: 2,
    borderColor: '#fff',
  },
  field: {
    width: '100%',
    marginBottom: 20,
  },
  input: {
    width: '100%',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f9f9f9',
    textAlign: 'center', // căn giữa text trong TextInput
  },
  text: {
    fontSize: 16,
    color: '#555',
    paddingVertical: 6,
    textAlign: 'center',
  },
  label: {
    fontWeight: 'bold',
    fontSize: 14,
    color: '#333',
    marginBottom: 4,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-evenly',
    marginTop: 30,
  },


});

export default EditProfileScreen;
