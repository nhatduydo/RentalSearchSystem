import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Pressable } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import filterStyles from '../styles/filterStyles';

const FilterScreen = () => {
  const [city, setCity] = useState('HCM');
  const [district, setDistrict] = useState('');
  const [roomType, setRoomType] = useState('');
  const [priceRange, setPriceRange] = useState('');
  const [pet, setPet] = useState('');
  const [airCon, setAirCon] = useState('');
  const [parking, setParking] = useState('');
  const [internet, setInternet] = useState('');
  const [quantity, setQuantity] = useState('');

  const priceOptions = [
    'Tất cả', '<= 2 triệu', '2 - 3 triệu', '3 - 4 triệu',
    '4 - 5 triệu', '5 - 6 triệu', '6 - 8 triệu', '>= 8 triệu'
  ];
  const quantityPeople = [
    '1 người', '2 người', '3 người', '4 người', '>= 5 người'
  ]

  const Options = ['Có', 'Không', 'Tất cả'];

  const renderOptionButtons = (options, selected, setSelected) => (
    <View style={filterStyles.optionContainer}>
      {options.map(option => (
        <TouchableOpacity
          key={option}
          style={[filterStyles.optionButton, selected === option && filterStyles.optionButtonSelected]}
          onPress={() => setSelected(option)}
        >
          <Text style={[filterStyles.optionText, selected === option && filterStyles.optionTextSelected]}>
            {option}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  return (
    <ScrollView style={filterStyles.container}>
      <Text style={filterStyles.header}>Tìm phòng theo khu vực</Text>

      <View style={filterStyles.pickerWrapper}>
        <Text style={filterStyles.label}>Tỉnh/Thành phố</Text>
        <Picker selectedValue={city} onValueChange={setCity} style={filterStyles.picker}>
          <Picker.Item label="Thành phố Hồ Chí Minh" value="HCM" />
          <Picker.Item label="Hà Nội" value="HN" />
        </Picker>
      </View>

      <View style={filterStyles.pickerWrapper}>
        <Text style={filterStyles.label}>Quận/huyện</Text>
        <Picker selectedValue={district} onValueChange={setDistrict} style={filterStyles.picker}>
          <Picker.Item label="Chọn quận huyện..." value="" />
          <Picker.Item label="Quận 1" value="q1" />
          <Picker.Item label="Quận Bình Thạnh" value="qBT" />
        </Picker>
      </View>

      <View style={filterStyles.pickerWrapper}>
        <Text style={filterStyles.label}>Loại phòng</Text>
        <Picker selectedValue={roomType} onValueChange={setRoomType} style={filterStyles.picker}>
          <Picker.Item label="Chọn loại phòng..." value="" />
          <Picker.Item label="Phòng trọ" value="phong_tro" />
          <Picker.Item label="Chung cư mini" value="cc_mini" />
        </Picker>
      </View>

      <Text style={filterStyles.sectionTitle}>Giá</Text>
      {renderOptionButtons(priceOptions, priceRange, setPriceRange)}

      <Text style={filterStyles.sectionTitle}>Nuôi thú cưng</Text>
      {renderOptionButtons(Options, pet, setPet)}

      <Text style={filterStyles.sectionTitle}>Máy lạnh</Text>
      {renderOptionButtons(Options, airCon, setAirCon)}

      <Text style={filterStyles.sectionTitle}>Chỗ đậu xe</Text>
      {renderOptionButtons(Options, parking, setParking)}

      <Text style={filterStyles.sectionTitle}>Wifi</Text>
      {renderOptionButtons(Options, internet, setInternet)}

      <Text style={filterStyles.sectionTitle}>Số lượng người ở</Text>
      {renderOptionButtons(quantityPeople, quantity, setQuantity)}

      <TouchableOpacity style={filterStyles.applyButton}>
        <Text style={filterStyles.applyButtonText}>Áp dụng</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

export default FilterScreen;
