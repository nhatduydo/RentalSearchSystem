import React from 'react';
import { FlatList, Image, SafeAreaView, StatusBar, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { chatStyles } from '../styles/chatStyles';
import { dataChats } from '../const/dataChats';
import Icon from 'react-native-vector-icons/MaterialIcons';

const ChatScreen = () => {
  const [message, setMessage] = React.useState('');

  const handleSend = () => {
    alert("hehe");
  }

  return (
    <SafeAreaView style={chatStyles.container}>
      <StatusBar backgroundColor="#2196F3" barStyle="light-content" />
      <View style={chatStyles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Image source={require('../assets/images/meomeo1.jpg')} style={chatStyles.avatar} />
        <Text style={chatStyles.name}>Trí</Text>
      </View>

      <FlatList
        data={dataChats}
        renderItem={({ item }) => (
          <View
            style={[
              chatStyles.messageContainer,
              item.sender === 'me' ? chatStyles.myMessage : chatStyles.otherMessage,
            ]}>
            <Text style={chatStyles.messageText}>{item.text}</Text>
          </View>
        )}
        keyExtractor={(item, index) => index.toString()}
        contentContainerStyle={{ padding: 10 }}
        inverted
      />

      <View style={chatStyles.inputContainer}>
        <TextInput
          style={chatStyles.input}
          placeholder="Nhập tin nhắn..."
          value={message}
          onChangeText={setMessage}
        />
        <TouchableOpacity onPress={handleSend}>
          <Icon name="send" size={24} color="#2196F3" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>

  );
};

export default ChatScreen;