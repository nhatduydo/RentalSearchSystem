import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import filterStyles from '../styles/filterStyles';
import axios, { endpoints } from '../configs/Apis';
import { useNavigation, useRoute } from '@react-navigation/native';

const amenitiesList = [
  { id: 6, name: "wifi" },
  { id: 7, name: "Quạt" },
  { id: 8, name: "Bếp gas" },
  { id: 9, name: "Ban công" },
  { id: 10, name: "Quạt trần" },
  { id: 11, name: "Máy giặt" },
  { id: 12, name: "Tủ lạnh" },
  { id: 13, name: "Cách âm" },
  { id: 14, name: "Bàn học" },
  { id: 15, name: "Cửa sổ" }
];

const FilterScreen = () => {
  const navigation = useNavigation();
  const route = useRoute();

  // Lấy selectedFilters từ route.params
  const { selectedFilters = {}, allMotels = [], onApplyFilter } = route.params || {};

  // Khởi tạo state với giá trị lấy từ selectedFilters hoặc mặc định
  const [city, setCity] = useState(selectedFilters.city || '');
  const [district, setDistrict] = useState(selectedFilters.district || '');
  const [roomType, setRoomType] = useState(selectedFilters.roomType || '');
  const [priceRange, setPriceRange] = useState(selectedFilters.priceRange || '');
  const [maxPeople, setMaxPeople] = useState(selectedFilters.maxPeople || '');
  const [selectedAmenities, setSelectedAmenities] = useState(selectedFilters.selectedAmenities || []);

  // Hàm toggle tiện ích
  const toggleAmenity = (id) => {
    setSelectedAmenities(prev =>
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
    );
  };

  // Hàm phân tích khoảng giá thành số
  const parsePriceRange = (range) => {
    if (range === '<= 2 triệu') return [0, 2000000];
    if (range === '2 - 3 triệu') return [2000000, 3000000];
    if (range === '3 - 4 triệu') return [3000000, 4000000];
    if (range === '4 - 5 triệu') return [4000000, 5000000];
    if (range === '5 - 6 triệu') return [5000000, 6000000];
    if (range === '6 - 8 triệu') return [6000000, 8000000];
    if (range === '>= 8 triệu') return [8000000, null];
    return [null, null];
  };

  // Hàm fetch phòng (giống như bạn có sẵn)
  const fetchAllRooms = async (params) => {
    let page = 1;
    let allRooms = [];
    let hasNext = true;

    while (hasNext) {
      const res = await axios.get(endpoints.rooms, {
        params: { ...params, page },
      });

      allRooms = [...allRooms, ...res.data.results];
      hasNext = !!res.data.next;
      page++;
    }

    return allRooms;
  };

  // Hàm fetch nhà trọ theo id (giống bạn)
  const fetchAllMotels = async (motelIds) => {
    let page = 1;
    let allMotelsFiltered = [];
    let hasNext = true;

    while (hasNext) {
      const res = await axios.get(endpoints.motels, {
        params: {
          id__in: motelIds.join(','),
          page: page,
        },
      });

      allMotelsFiltered = [...allMotelsFiltered, ...res.data.results];
      hasNext = !!res.data.next;
      page++;
    }

    return allMotelsFiltered;
  };

  // Áp dụng bộ lọc
  const applyFilters = async () => {
    const params = {};

    if (priceRange) {
      const [min, max] = parsePriceRange(priceRange);
      if (min !== null) params.min_price = min;
      if (max !== null) params.max_price = max;
    }

    if (maxPeople) params.max_people = maxPeople;

    if (selectedAmenities.length > 0) {
      params.amenities = selectedAmenities.join(',');
    }

    if (roomType) {
      params.room_type = roomType;
    }

    try {
      // Lấy tất cả phòng phù hợp
      const allRooms = await fetchAllRooms(params);

      // Lấy id motel từ phòng
      const motelIds = [...new Set(allRooms.map(room => room.motel_id))];

      if (motelIds.length === 0) {
        console.log('Không tìm thấy nhà trọ phù hợp');
        onApplyFilter && onApplyFilter([], { city, district, roomType, priceRange, maxPeople, selectedAmenities });
        navigation.goBack();
        return;
      }

      // Lấy danh sách motel
      let filteredMotels = await fetchAllMotels(motelIds);

      // Lọc tiếp theo city và district nếu có
      if (city) filteredMotels = filteredMotels.filter(motel => motel.city === city);
      if (district) filteredMotels = filteredMotels.filter(motel => motel.district === district);

      onApplyFilter && onApplyFilter(filteredMotels, { city, district, roomType, priceRange, maxPeople, selectedAmenities });

      navigation.goBack();
    } catch (error) {
      console.error('Lỗi khi lọc:', error);
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'android' ? 20 : 0}
    >
      <ScrollView style={filterStyles.container} contentContainerStyle={{ paddingBottom: 60 }} keyboardShouldPersistTaps="handled">
        <Text style={filterStyles.header}>Bộ lọc phòng</Text>

        <View style={filterStyles.pickerWrapper}>
          <Text style={filterStyles.label}>Tỉnh/Thành phố</Text>
          <Picker selectedValue={city} onValueChange={setCity} style={filterStyles.picker}>
            <Picker.Item label="Chọn..." value="" />
            <Picker.Item label="TP. Hồ Chí Minh" value="TP. Hồ Chí Minh" />
            <Picker.Item label="TP. Hà Nội" value="TP. Hà Nội" />
          </Picker>
        </View>

        <View style={filterStyles.pickerWrapper}>
          <Text style={filterStyles.label}>Quận/Huyện</Text>
          <Picker selectedValue={district} onValueChange={setDistrict} style={filterStyles.picker}>
            <Picker.Item label="Chọn..." value="" />
            <Picker.Item label="Quận 1" value="Quận 1" />
            <Picker.Item label="Từ Liêm" value="Từ Liêm" />
          </Picker>
        </View>

        <View style={filterStyles.pickerWrapper}>
          <Text style={filterStyles.label}>Loại phòng</Text>
          <Picker selectedValue={roomType} onValueChange={setRoomType} style={filterStyles.picker}>
            <Picker.Item label="Chọn..." value="" />
            <Picker.Item label="Phòng trọ" value="phong_tro" />
            <Picker.Item label="Chung cư mini" value="cc_mini" />
          </Picker>
        </View>

        <Text style={filterStyles.sectionTitle}>Giá phòng</Text>
        {['<= 2 triệu', '2 - 3 triệu', '3 - 4 triệu', '>= 8 triệu'].map(option => (
          <TouchableOpacity
            key={option}
            style={[filterStyles.optionButton, priceRange === option && filterStyles.optionButtonSelected]}
            onPress={() => setPriceRange(option)}
          >
            <Text>{option}</Text>
          </TouchableOpacity>
        ))}

        <Text style={filterStyles.sectionTitle}>Số người tối đa</Text>
        {['1', '2', '3', '4', '>= 5'].map(option => (
          <TouchableOpacity
            key={option}
            style={[filterStyles.optionButton, maxPeople === option && filterStyles.optionButtonSelected]}
            onPress={() => setMaxPeople(option)}
          >
            <Text>{option}</Text>
          </TouchableOpacity>
        ))}

        <Text style={filterStyles.sectionTitle}>Tiện ích</Text>
        {amenitiesList.map(item => (
          <TouchableOpacity
            key={item.id}
            style={[filterStyles.optionButton, selectedAmenities.includes(item.id) && filterStyles.optionButtonSelected]}
            onPress={() => toggleAmenity(item.id)}
          >
            <Text>{item.name}</Text>
          </TouchableOpacity>
        ))}

        <TouchableOpacity style={filterStyles.applyButton} onPress={applyFilters}>
          <Text style={filterStyles.applyButtonText}>Áp dụng</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

export default FilterScreen;
