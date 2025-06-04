import { createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';
import BookingScreen from '../screens/BookingScreen';
import PaymentScreen from '../screens/PaymentScreen';

const Tab = createMaterialTopTabNavigator();

const PaymentBookingTabs = ({ route }) => {
    const { roomId } = route.params || {};
    return (
        <Tab.Navigator>
            <Tab.Screen name="Đặt phòng" initialParams={{ roomId }} component={BookingScreen} />
            <Tab.Screen name="Thanh toán" initialParams={{ roomId }} component={PaymentScreen} />
        </Tab.Navigator>
    );
};

export default PaymentBookingTabs;
