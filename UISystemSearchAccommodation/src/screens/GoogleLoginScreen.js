import React, { useEffect, useState } from 'react';
import { Button, View, Text, Alert, ActivityIndicator } from 'react-native';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import * as AuthSession from 'expo-auth-session';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { endpoints } from '../configs/Apis';

WebBrowser.maybeCompleteAuthSession();

const GoogleLoginScreen = ({ navigation }) => {
  const [role, setRole] = useState('TENANT');
  const [loading, setLoading] = useState(false);

  const redirectUri = AuthSession.makeRedirectUri({
    useProxy: true,
  });

  const [request, response, promptAsync] = Google.useAuthRequest({
    clientId: '284762867837-sv52qe2s58lc15sjjv6b8bpmoqmucbkg.apps.googleusercontent.com',
    redirectUri,
  });

  useEffect(() => {
    if (response?.type === 'success') {
      const { id_token } = response.authentication;
      handleGoogleLogin(id_token);
    }
  }, [response]);

  const handleGoogleLogin = async (idToken) => {
    setLoading(true);
    try {
      const res = await axios.post(endpoints['google-auth'], {
        token_id: idToken,
        role: role,
      })

      const result = res.data;
      await AsyncStorage.setItem('access_token', result.access_token);

      Alert.alert('Đăng nhập thành công!');
      navigation.replace('ProfileScreen');
    } catch (error) {
      Alert.alert('Lỗi mạng', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, justifyContent: 'center', padding: 20 }}>
      <Text style={{ fontSize: 18, marginBottom: 20 }}>Chọn vai trò:</Text>

      <Button
        title={role === 'TENANT' ? 'Người thuê trọ' : 'Chủ trọ'}
        onPress={() => setRole(role === 'TENANT' ? 'LANDLORD' : 'TENANT')}
      />

      <View style={{ height: 20 }} />

      {loading ? (
        <ActivityIndicator size="large" />
      ) : (
        <Button title="Đăng nhập với Google" onPress={() => promptAsync()} disabled={!request} />
      )}
    </View>
  );
};

export default GoogleLoginScreen;
