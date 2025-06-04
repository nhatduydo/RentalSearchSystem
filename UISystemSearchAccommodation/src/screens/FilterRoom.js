import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import filterStyles from '../styles/filterStyles';
// import axios, { endpoints } from '../configs/Apis';
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

const districtsByCity = {
  "Hồ Chí Minh": [
    "Bình Chánh",
    "Bình Thạnh",
    "Tân Bình",
    "Bình Tân",
    "Quận 3",
    "Quận 10",
    "Thủ Đức",
  ],
};

export default function FilterScreen() {
  const [city, setCity] = useState('');
  const [district, setDistrict] = useState('');
  const [roomType, setRoomType] = useState('');
  const [priceRange, setPriceRange] = useState('');
  const [maxPeople, setMaxPeople] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [selectedAmenities, setSelectedAmenities] = useState([]);

  const navigation = useNavigation();
  const route = useRoute();
  const onApplyFilter = route.params?.onApplyFilter;

  const toggleAmenity = (id) => {
    if (selectedAmenities.includes(id)) {
      setSelectedAmenities(selectedAmenities.filter(x => x !== id));
    } else {
      setSelectedAmenities([...selectedAmenities, id]);
    }
  };

  const onChangeCity = (value) => {
    setCity(value);
    setDistrict('');
  };


  const handleApply = () => {
    const amenities = selectedAmenities.join(',');
    const params = {
      min_price: minPrice,
      max_price: maxPrice,
      amenities,
      max_people: maxPeople,
      room_type: roomType,
      city,
      district,
    };
    onApplyFilter?.(params);
    navigation.goBack();
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'android' ? 20 : 0}
    >
      <View style={{ flex: 1 }}>
        <ScrollView style={filterStyles.container} contentContainerStyle={{ paddingBottom: 100 }} keyboardShouldPersistTaps="handled">
          <Text style={filterStyles.header}>Bộ lọc phòng</Text>

          <View style={filterStyles.pickerWrapper}>
            <Text style={filterStyles.label}>Tỉnh/Thành phố</Text>
            <Picker
              selectedValue={city}
              onValueChange={onChangeCity}
              style={filterStyles.picker}
            >
              <Picker.Item label="Chọn..." value="" />
              <Picker.Item label="TP. Hồ Chí Minh" value="Hồ Chí Minh" />
            </Picker>
          </View>

          <View style={filterStyles.pickerWrapper}>
            <Text style={filterStyles.label}>Quận/Huyện</Text>
            <Picker
              selectedValue={district}
              onValueChange={setDistrict}
              enabled={city === "Hồ Chí Minh"}
              style={filterStyles.picker}
            >
              <Picker.Item label="Chọn..." value="" />
              {(districtsByCity[city] || []).map((d) => (
                <Picker.Item key={d} label={d} value={d} />
              ))}
            </Picker>
          </View>

          <Text style={filterStyles.sectionTitle}>Giá phòng</Text>
          {[
            { label: '<= 2 triệu', min: 0, max: 2000000 },
            { label: '2 - 3 triệu', min: 2000000, max: 3000000 },
            { label: '3 - 4 triệu', min: 3000000, max: 4000000 },
            { label: '>= 8 triệu', min: 8000000, max: 999999999 },
          ].map(option => (
            <TouchableOpacity
              key={option.label}
              style={[filterStyles.optionButton, priceRange === option.label && filterStyles.optionButtonSelected]}
              onPress={() => {
                setPriceRange(option.label);
                setMinPrice(option.min);
                setMaxPrice(option.max);
              }}
            >
              <Text>{option.label}</Text>
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
        </ScrollView>

        <View style={filterStyles.footer}>
          <TouchableOpacity style={filterStyles.applyButton} onPress={handleApply}>
            <Text style={filterStyles.applyButtonText}>Áp dụng</Text>
          </TouchableOpacity>
        </View>
      </View>

    </KeyboardAvoidingView>
  );
};