import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity } from 'react-native';
import loginStyles from '../styles/loginStyles';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/FontAwesome';

const LoginScreen = () => {
    const navigation = useNavigation();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const handleLogin = () => {
        // Giả lập đăng nhập thành công
        const user = {
            fullName: 'Nguyễn Văn A',
            username: username,
            email: 'vana@gmail.com',
            phone: '0987654321'
        };

        navigation.navigate('Main', { screen: 'Profile', params: { user } });
    };

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
                        <Text style={[loginStyles.fbText, {marginLeft: 8}]}>Facebook</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={loginStyles.googleBtn}>
                        <Icon name="google" size={20} color='#fff' />
                        <Text style={[loginStyles.googleText , {marginLeft: 8}]}>Google</Text>
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
