import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import registerStyles from '../styles/registerStyles';

const RegisterScreen = () => {
    const navigation = useNavigation();

    const [fullName, setFullName] = useState('');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');

    const handleRegister = () => {
        const user = {
          fullName,
          username,
          email,
        };
    
        navigation.navigate('Profile', { user });
      };

    return (
        <View style={registerStyles.container}>
            <Text style={registerStyles.title}>Đăng Ký</Text>

            <View style={registerStyles.form}>
                <TextInput placeholder="Họ và tên" value={fullName} onChangeText={setFullName} style={registerStyles.input} />

                <TextInput placeholder="Tên đăng nhập" placeholderTextColor="#888" style={registerStyles.input} value={username} onChangeText={setUsername} />

                <TextInput placeholder="Email" placeholderTextColor="#888" style={registerStyles.input} value={email} onChangeText={setEmail} />

                <TextInput placeholder="Số điện thoại" placeholderTextColor="#888" style={registerStyles.input} value={phone} onChangeText={setPhone} />

                <TextInput placeholder="Mật khẩu" placeholderTextColor="#888" secureTextEntry style={registerStyles.input} value={password} onChangeText={setPassword} />

                <TouchableOpacity style={registerStyles.signUpBtn}>
                    <Text style={registerStyles.signUpText} onPress={handleRegister}>Đăng Ký</Text>
                </TouchableOpacity>

                <Text style={registerStyles.haveAccount}>
                    Đã có tài khoản? <Text style={registerStyles.loginLink} onPress={() => navigation.navigate('SignIn')}>Đăng nhập</Text>
                </Text>
            </View>
        </View>
    );
};

export default RegisterScreen;
