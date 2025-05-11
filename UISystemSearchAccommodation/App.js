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
        <Stack.Screen name="EditProfile" component={EditProfileScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
