import { MaterialIcons, FontAwesome5, Ionicons, Entypo } from '@expo/vector-icons';
export const utilities = [
    {
      name: 'Đăng Bài',
      icon: <MaterialIcons name="post-add" size={30} color="#007bff" />,
      screen: 'Post',
    },
    {
      name: 'Tìm Trọ',
      icon: <FontAwesome5 name="search-location" size={30} color="#28a745" />,
      screen: 'Search',
    },
    {
      name: 'Bản Đồ',
      icon: <Ionicons name="map" size={30} color="#dc3545" />,
      screen: 'Map',
    },
    {
      name: 'Thông Báo',
      icon: <Entypo name="notification" size={30} color="#ff9900" />,
      screen: 'Notification',
    },
  ];
  