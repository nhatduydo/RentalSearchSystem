import React, { useState } from 'react';
import {
    View, Text, TextInput, TouchableOpacity, Alert, Image, Button,
    Switch,
    ScrollView,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import registerStyles from '../styles/registerStyles';
import axios, { endpoints } from '../configs/Apis';
import { RadioButton } from 'react-native-paper';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Platform } from 'react-native';
import moment from 'moment';

const Register2Screen = ({ route, navigation }) => {
    const { username, password, email, full_name } = route.params;

    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [phone, setPhone] = useState('');
    const [address, setAddress] = useState('');
    const [dob, setDob] = useState('');
    const [showDatePicker, setShowDatePicker] = useState(false);
    const [dobDate, setDobDate] = useState(new Date());
    const [gender, setGender] = useState('');
    const [bankAccount, setBankAccount] = useState('');
    const [citizenId, setCitizenId] = useState('');
    const [role, setRole] = useState('TENANT');
    const [avatar, setAvatar] = useState(null);

    const pickImage = async () => {
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

    const showPicker = () => setShowDatePicker(true);

    const onDateChange = (event, selectedDate) => {
        setShowDatePicker(Platform.OS === 'ios');
        if (selectedDate) {
            setDobDate(selectedDate);
            setDob(moment(selectedDate).format('YYYY-MM-DD'));
        }
    };

    const handleSubmit = async () => {
        if (!firstName || !lastName || !phone || !address || !dob || !gender || !bankAccount || !citizenId) {
            Alert.alert('Lỗi', 'Vui lòng nhập đầy đủ thông tin');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            formData.append('email', email);
            formData.append('full_name', full_name);
            formData.append('first_name', firstName);
            formData.append('last_name', lastName);
            formData.append('phone', phone);
            formData.append('address', address);
            formData.append('date_of_birth', dob);
            formData.append('gender', gender);
            formData.append('bank_account', bankAccount);
            formData.append('citizen_id', citizenId);
            formData.append('role', role);
            if (avatar) {
                formData.append('avatar', {
                    uri: avatar,
                    name: 'avatar.jpg',
                    type: 'image/jpeg',
                });
            }


            const res = await axios.post(endpoints.users, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            Alert.alert('Thành công', 'Tài khoản đã được tạo');
            navigation.navigate('SignIn');
        } catch (err) {
            const details = err.response?.data?.details;
            let errorMessage = 'Không thể tạo tài khoản';

            if (details) {
                if (details.email) {
                    errorMessage = 'Nhập đúng cấu trúc email.';
                } else if (details.username) {
                    errorMessage = 'Tên đăng nhập đã tồn tại.';
                }
            }

            Alert.alert('Lỗi đăng ký', errorMessage);
            console.error('Chi tiết:', err.response?.data);
        }
    };

    return (
        <ScrollView contentContainerStyle={registerStyles.container}>
            <Text style={registerStyles.title}>Đăng Ký - Bước 2</Text>

            <View style={registerStyles.form}>
                <View style={registerStyles.row}>
                    <TextInput
                        placeholder="Họ"
                        value={firstName}
                        onChangeText={setFirstName}
                        style={[registerStyles.input, registerStyles.halfInput]}
                    />
                    <TextInput
                        placeholder="Tên"
                        value={lastName}
                        onChangeText={setLastName}
                        style={[registerStyles.input, registerStyles.halfInput, { marginLeft: 10 }]}
                    />
                </View>

                <TextInput
                    placeholder="Số điện thoại"
                    value={phone}
                    onChangeText={setPhone}
                    style={registerStyles.input}
                />

                <TextInput
                    placeholder="Địa chỉ"
                    value={address}
                    onChangeText={setAddress}
                    style={registerStyles.input}
                />

                <View style={registerStyles.row}>
                    <TouchableOpacity
                        onPress={showPicker}
                        style={[registerStyles.input, registerStyles.halfInput, { justifyContent: 'center' }]}
                    >
                        <Text style={{ color: dob ? '#000' : '#888' }}>
                            {dob || 'Chọn ngày sinh'}
                        </Text>
                    </TouchableOpacity>

                    {showDatePicker && (
                        <DateTimePicker
                            value={dobDate}
                            mode="date"
                            display="default"
                            onChange={onDateChange}
                            maximumDate={new Date()}
                        />
                    )}

                    <View style={{ marginBottom: 20 }}>
                        <Text style={{ fontSize: 16, marginBottom: 5 }}>Giới tính:</Text>
                        <RadioButton.Group onValueChange={setGender} value={gender}>
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', marginRight: 20 }}>
                                    <RadioButton.Android value="MALE" />
                                    <Text onPress={() => setGender("MALE")} style={{ fontSize: 14 }}>Nam</Text>
                                </View>
                                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                    <RadioButton.Android value="FEMALE" />
                                    <Text onPress={() => setGender("FEMALE")} style={{ fontSize: 14 }}>Nữ</Text>
                                </View>
                            </View>
                        </RadioButton.Group>
                    </View>

                </View>

                <TextInput
                    placeholder="Tài khoản ngân hàng"
                    value={bankAccount}
                    onChangeText={setBankAccount}
                    style={registerStyles.input}
                />

                <TextInput
                    placeholder="CMND/CCCD"
                    value={citizenId}
                    onChangeText={setCitizenId}
                    style={registerStyles.input}
                />
            </View>


            <View style={registerStyles.roleContainer}>
                <Text style={registerStyles.roleLabel}>
                    Vai trò: {role === 'LANDLORD' ? 'Chủ trọ' : 'Người thuê'}
                </Text>
                <Switch
                    value={role === 'LANDLORD'}
                    onValueChange={(value) => setRole(value ? 'LANDLORD' : 'TENANT')}
                    trackColor={{ false: '#767577', true: '#00aaff' }}
                    thumbColor={role === 'LANDLORD' ? '#ffffff' : '#f4f3f4'}
                />
            </View>

            <Button title="Chọn ảnh đại diện" onPress={pickImage} />
            {avatar && <Image source={{ uri: avatar }} style={{ width: 80, height: 80, marginTop: 10, borderRadius: 50 }} />}

            <TouchableOpacity style={registerStyles.signUpBtn} onPress={handleSubmit}>
                <Text style={registerStyles.signUpText}>Tạo Tài Khoản</Text>
            </TouchableOpacity>
        </ScrollView>
    );
};

export default Register2Screen;
