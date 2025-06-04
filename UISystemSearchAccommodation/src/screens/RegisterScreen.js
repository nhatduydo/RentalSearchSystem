import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import registerStyles from '../styles/registerStyles';

const RegisterScreen = () => {
    const navigation = useNavigation();

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [fullName, setFullName] = useState('');

    const handleNext = () => {
        if (!username || !password || !email || !fullName) {
            Alert.alert('Lỗi', 'Vui lòng nhập đầy đủ thông tin');
            return;
        }

        navigation.navigate('SignUp2', {
            username,
            password,
            email,
            full_name: fullName,
        });
    };

    return (
        <View style={registerStyles.container}>
            <Text style={registerStyles.title}>Đăng Ký - Bước 1</Text>

            <View style={registerStyles.form}>
                <TextInput
                    placeholder="Họ và tên"
                    value={fullName}
                    onChangeText={setFullName}
                    style={registerStyles.input}
                />
                <TextInput
                    placeholder="Tên đăng nhập"
                    value={username}
                    onChangeText={setUsername}
                    style={registerStyles.input}
                />
                <TextInput
                    placeholder="Mật khẩu"
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry
                    style={registerStyles.input}
                />
                <TextInput
                    placeholder="Email"
                    value={email}
                    onChangeText={setEmail}
                    keyboardType="email-address"
                    style={registerStyles.input}
                />
            </View>
            <TouchableOpacity style={registerStyles.signUpBtn} onPress={handleNext}>
                <Text style={registerStyles.signUpText}>Tiếp tục</Text>
            </TouchableOpacity>
        </View>
    );
};

export default RegisterScreen;
