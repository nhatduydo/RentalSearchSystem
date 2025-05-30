import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import BottomNavigation from './src/components/BottomNavigation';
import DetailScreen from './src/screens/DetailsScreen';
import FilterScreen from './src/screens/FilterRoom';
import ProfileScreen from './src/screens/ProfileScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import EditProfileScreen from './src/screens/EditProfileScreen';
import LandlordInfoScreen from './src/screens/LandlordScreen';
import RoomListScreen from './src/screens/RoomListScreen';
import ChatScreen from './src/screens/ChatScreen';
import CreatePostScreen from './src/screens/CreatePostScreen';
import MapScreen from './src/screens/MapScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Main" component={BottomNavigation} options={{ headerShown: false }}/>
        <Stack.Screen name="Detail" component={DetailScreen} options={{ title: 'Chi tiết phòng trọ' }}/>
        <Stack.Screen name="Filter" component={FilterScreen} options={{ title: 'Lọc thông tin' }} />
        <Stack.Screen name="Profile" component={ProfileScreen} options={{ title: 'Thông tin tài khoản' }}/>
        <Stack.Screen name="SignIn" component={LoginScreen} options={{ title: 'Đăng nhập' }}/>
        <Stack.Screen name="SignUp" component={RegisterScreen} options={{ title: 'Đăng ký' }}/>
        <Stack.Screen name="RoomList" component={RoomListScreen} options={{ title: 'Danh sách nhà trọ' }}/>
        <Stack.Screen name="EditProfile" component={EditProfileScreen} options={{ title: 'Chỉnh sửa thông tin' }}/>
        <Stack.Screen name="CreatePost" component={CreatePostScreen} options={{ title: 'Tạo Bài Đăng' }}/>
        <Stack.Screen name="Chat" component={ChatScreen} options={{ title: 'Trò chuyện' }}/>
        <Stack.Screen name="Map" component={MapScreen} options={{ title: 'Bản Đồ' }}/>
        <Stack.Screen name="LandlordInfo" component={LandlordInfoScreen} options={{ title: 'Thông tin chủ trọ' }}/>
      </Stack.Navigator>
    </NavigationContainer>
  );
}