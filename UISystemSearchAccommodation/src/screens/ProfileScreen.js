import React, { useState, useEffect } from 'react';
import { View, Text, Button, StyleSheet, Image, TouchableOpacity } from 'react-native';
import { useNavigation, useIsFocused } from '@react-navigation/native';

const ProfileScreen = ({ route }) => {
  const [user, setUser] = useState(null);
  const navigation = useNavigation();
  const isFocused = useIsFocused();

  useEffect(() => {
    if (isFocused && route.params?.user) {
      setUser(route.params.user);
    }
  }, [route.params, isFocused]);

  return (
    <View style={styles.container}>
      {!user ? (
        <>
          <Text style={styles.title}>
            Vui lòng <Text style={{ color: 'blue' }}>Đăng Nhập</Text> hoặc <Text style={{ color: 'green' }}>Đăng Ký</Text> để tiếp tục sử dụng
          </Text>
          <View style={styles.button}>
            <Button title="Đăng Nhập" onPress={() => navigation.navigate('SignIn')} />
          </View>
          <View style={styles.button}>
            <Button title="Đăng Ký" onPress={() => navigation.navigate('SignUp')} />
          </View>
        </>
      ) : (
        <>
          {user.avatar?.uri && (
            <Image source={{ uri: user.avatar.uri }} style={styles.avatar} />
          )}
          <Text style={styles.name}>Xin chào, {user.fullName}!</Text>
          <Text style={styles.info}>Tên đăng nhập: {user.username}</Text>
          <Text style={styles.info}>Email: {user.email}</Text>
          <Text style={styles.info}>Số điện thoại: {user.phone || 'Chưa cập nhật'}</Text>

          <TouchableOpacity
            style={styles.editButton}
            onPress={() => navigation.navigate('EditProfile', { user })}
          >
            <Text style={styles.editButtonText}>Chỉnh sửa thông tin</Text>
          </TouchableOpacity>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  button: { marginVertical: 10, width: '60%' },
  avatar: { width: 100, height: 100, borderRadius: 50, marginBottom: 15 },
  name: { fontSize: 20, fontWeight: 'bold', marginBottom: 10 },
  info: { fontSize: 16, marginVertical: 2 },
  editButton: {
    marginTop: 20,
    backgroundColor: '#1e90ff',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  editButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
});

export default ProfileScreen;
