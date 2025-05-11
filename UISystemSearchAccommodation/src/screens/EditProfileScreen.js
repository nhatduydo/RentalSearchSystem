import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, Button, Image, TouchableOpacity } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

const EditProfileScreen = ({ route, navigation }) => {
  const [user, setUser] = useState(route.params.user || {});

  const handleChange = (value, field) => {
    setUser({ ...user, [field]: value });
  };

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      alert('Permission denied!');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync();
    if (!result.canceled) {
      setUser({ ...user, avatar: result.assets[0] });
    }
  };

  const handleSave = () => {
    navigation.navigate('Profile', { user });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Chỉnh sửa thông tin</Text>

      <TouchableOpacity onPress={pickImage}>
        {user.avatar?.uri ? (
          <Image source={{ uri: user.avatar.uri }} style={styles.avatar} />
        ) : (
          <View style={styles.avatarPlaceholder}>
            <Text>Chọn ảnh đại diện</Text>
          </View>
        )}
      </TouchableOpacity>

      <TextInput
        style={styles.input}
        placeholder="Họ tên"
        value={user.fullName}
        onChangeText={text => handleChange(text, 'fullName')}
      />
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={user.email}
        onChangeText={text => handleChange(text, 'email')}
      />
      <TextInput
        style={styles.input}
        placeholder="Số điện thoại"
        value={user.phone}
        onChangeText={text => handleChange(text, 'phone')}
      />

      <Button title="Lưu" onPress={handleSave} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, alignItems: 'center' },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 20 },
  input: {
    width: '100%',
    borderBottomWidth: 1,
    marginBottom: 15,
    fontSize: 16,
    paddingVertical: 5,
  },
  avatar: { width: 100, height: 100, borderRadius: 50, marginBottom: 10 },
  avatarPlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#ccc',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
});

export default EditProfileScreen;
