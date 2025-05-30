import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import loginStyles from '../styles/loginStyles';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/FontAwesome';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { endpoints } from '../configs/Apis';

const LoginScreen = () => {
    const navigation = useNavigation();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
        try {
            setLoading(true);
            const response = await axios.post(endpoints['oauth2-token'], {
                username: username,
                password: password,
                client_id: '5ZSVyx7Z9CzRooRyodvOxyMnL5gVHt16UqBiwh7y',
                client_secret: 'vxFust8TqAfft0AOPzK5R9Igc2WVpysm18wKX6AWgJidk5o9Eii2cmdhEvaeglbOBeAStBrI0RCl1YhM3QstIrmYrCsh189IIr79B0595eA3PJYWMWUnNpmdDKmuuHUa',
                grant_type: 'password'
            }, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const { access_token, refresh_token } = response.data;

            await AsyncStorage.setItem('access_token', access_token);
            await AsyncStorage.setItem('refresh_token', refresh_token);
            await AsyncStorage.setItem('username', username);

            navigation.reset({
                index: 0,
                routes: [
                    {
                        name: 'Main',
                        state: {
                            index: 4,
                            routes: [
                                { name: 'Home' },
                                { name: 'Chat' },
                                { name: 'Search' },
                                { name: 'Notification' },
                                { name: 'Profile' },
                            ],
                        },
                    },
                ],
            });

        } catch (error) {
            console.error('Login failed:', error);
            console.log('Response:', error?.response?.data);
            Alert.alert('Đăng nhập thất bại', 'Vui lòng kiểm tra lại tài khoản hoặc mật khẩu.');
        } finally {
            setLoading(false);
        }
    };
    if (loading) {
        return (
            <View style={loginStyles.container}>
                <ActivityIndicator size="large" color="#00b69f" />
            </View>
        );
    }

    return (
        <View style={loginStyles.container}>
            <Text style={loginStyles.title}>Đăng nhập</Text>

            <View style={loginStyles.form}>
                <TextInput placeholder="Tên đăng nhập" placeholderTextColor="#888" value={username} onChangeText={setUsername} style={loginStyles.input} />

                <TextInput placeholder="Mật khẩu" placeholderTextColor="#888" secureTextEntry style={loginStyles.input} value={password} onChangeText={setPassword} />

                <TouchableOpacity>
                    <Text style={loginStyles.forgot}>Quên Mật Khẩu?</Text>
                </TouchableOpacity>

                <TouchableOpacity style={loginStyles.signInBtn}>
                    <Text style={loginStyles.signInText} onPress={handleLogin}>Đăng nhập</Text>
                </TouchableOpacity>

                <Text style={loginStyles.orText}>hoặc đăng nhập bằng</Text>

                <View style={loginStyles.socialRow}>
                    <TouchableOpacity style={loginStyles.fbBtn}>
                        <Icon name="facebook" size={20} color='#fff' />
                        <Text style={[loginStyles.fbText, { marginLeft: 8 }]}>Facebook</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={loginStyles.googleBtn}>
                        <Icon name="google" size={20} color='#fff' />
                        <Text style={[loginStyles.googleText, { marginLeft: 8 }]}>Google</Text>
                    </TouchableOpacity>
                </View>

                <Text style={loginStyles.terms}>
                    Chúng tôi đồng ý với <Text style={loginStyles.termsLink}>Chính sách và Điều khoản</Text>
                </Text>

                <Text style={loginStyles.signupText}>
                    Chưa có tài khoản? <Text style={loginStyles.signupLink} onPress={() => navigation.navigate('SignUp')}>Đăng ký ngay</Text>
                </Text>
            </View>
        </View>
    );
};

export default LoginScreen;
