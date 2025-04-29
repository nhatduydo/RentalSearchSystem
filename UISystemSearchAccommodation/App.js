import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import BottomNavigation from './src/components/BottomNavigation';
import DetailScreen from './src/screens/DetailsScreen';
import FilterScreen from './src/screens/FilterRoom';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen
          name="Main"
          component={BottomNavigation}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Detail"
          component={DetailScreen}
          options={{ title: 'Chi tiết phòng trọ' }}
        />
        <Stack.Screen
          name="Filter"
          component={FilterScreen}
          options={{ title: 'Lọc thông tin' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
