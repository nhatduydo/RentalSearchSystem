import React from 'react';
import { View, StyleSheet } from 'react-native';
import MapView, { Marker } from 'react-native-maps';

const MapScreen = () => {
  const location = {
    latitude: 10.762622,
    longitude: 106.660172,
  };

  return (
    <View style={styles.container}>
      <MapView
        style={styles.map}
        initialRegion={location}
      >
        <Marker
          coordinate={{
            latitude: location.latitude,
            longitude: location.longitude,
          }}
          title="Nhà trọ A"
          description="Giá 2tr5/tháng, gần đại học"
        />
      </MapView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
});

export default MapScreen;
